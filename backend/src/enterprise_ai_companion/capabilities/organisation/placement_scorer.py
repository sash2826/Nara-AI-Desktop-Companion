"""Placement scorer for file organisation recommendations.

Combines two signals to score each candidate folder for a newly-indexed file:

  score = 0.70 × graph_score + 0.30 × rerank_score

graph_score — Jaccard similarity between the new file's entity IDs and the
  entity IDs of documents already in the candidate folder (expanded 1 hop via
  graph relationships to surface closely related entities).

rerank_score — Mean RRF score returned by HybridSearchOrchestrator when the
  new file's first chunk text is used as a query against each candidate folder's
  indexed content.

Only folders with a non-zero combined score are returned. The caller takes the
top-3 and attaches confidence labels.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import aiosqlite

from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator import (
    HybridSearchOrchestrator,
)

logger = logging.getLogger(__name__)

_GRAPH_WEIGHT = 0.70
_RERANK_WEIGHT = 0.30

_LABEL_STRONG = "Strong"
_LABEL_GOOD = "Good"
_LABEL_POSSIBLE = "Possible"

_SCORE_STRONG_THRESHOLD = 0.65
_SCORE_GOOD_THRESHOLD = 0.35


@dataclass(frozen=True)
class FolderScore:
    """Score for a single candidate folder."""

    folder: str
    score: float
    label: str


class PlacementScorer:
    """Scores candidate folders for a newly-indexed file."""

    def __init__(
        self,
        conn: aiosqlite.Connection,
        graph_provider: GraphProvider,
        embedding_service: EmbeddingService,
        qdrant_client: Any,
    ) -> None:
        self._conn = conn
        self._graph_provider = graph_provider
        self._embedding_service = embedding_service
        self._qdrant_client = qdrant_client

    async def score_all(
        self,
        document_id: str,
        candidate_folder_paths: list[str],
    ) -> list[dict[str, Any]]:
        """Score every candidate folder and return up to 3 results sorted by score desc.

        Returns a list of dicts suitable for JSON serialisation:
        ``[{"folder": str, "score": float, "label": str}, ...]``
        """
        if not candidate_folder_paths:
            return []

        new_file_entity_ids = await self._get_entity_ids_for_document(document_id)
        first_chunk_text = await self._get_first_chunk_text(document_id)

        tasks = [
            self._score_folder(
                folder_path=folder,
                new_file_entity_ids=new_file_entity_ids,
                query_text=first_chunk_text,
            )
            for folder in candidate_folder_paths
        ]
        folder_scores: list[FolderScore] = await asyncio.gather(*tasks)

        scored = sorted(
            (fs for fs in folder_scores if fs.score > 0.0),
            key=lambda fs: fs.score,
            reverse=True,
        )

        return [
            {"folder": fs.folder, "score": round(fs.score, 4), "label": fs.label}
            for fs in scored[:3]
        ]

    async def _score_folder(
        self,
        folder_path: str,
        new_file_entity_ids: set[str],
        query_text: str,
    ) -> FolderScore:
        graph_s, rerank_s = await asyncio.gather(
            self._graph_score(folder_path, new_file_entity_ids),
            self._rerank_score(folder_path, query_text),
        )
        combined = _GRAPH_WEIGHT * graph_s + _RERANK_WEIGHT * rerank_s
        return FolderScore(
            folder=folder_path,
            score=combined,
            label=_label(combined),
        )

    # ------------------------------------------------------------------
    # Graph score
    # ------------------------------------------------------------------

    async def _graph_score(
        self,
        folder_path: str,
        new_file_entity_ids: set[str],
    ) -> float:
        if not new_file_entity_ids:
            return 0.0

        folder_entity_ids = await self._get_entity_ids_for_folder(folder_path)
        if not folder_entity_ids:
            return 0.0

        intersection = new_file_entity_ids & folder_entity_ids
        union = new_file_entity_ids | folder_entity_ids
        return len(intersection) / len(union) if union else 0.0

    async def _get_entity_ids_for_document(self, document_id: str) -> set[str]:
        """Return the entity IDs extracted directly from *document_id*."""
        async with self._conn.execute(
            "SELECT id FROM graph_entities WHERE source_document_id = ?",
            (document_id,),
        ) as cur:
            rows = await cur.fetchall()
        return {row[0] for row in rows}

    async def _get_entity_ids_for_folder(self, folder_path: str) -> set[str]:
        """Return entity IDs for all documents in *folder_path*, expanded 1 hop."""
        # Step 1: collect document IDs in this folder (workspace_path == folder_path).
        async with self._conn.execute(
            "SELECT id FROM documents WHERE workspace_path = ?",
            (folder_path,),
        ) as cur:
            doc_rows = await cur.fetchall()

        if not doc_rows:
            return set()

        doc_ids = [row[0] for row in doc_rows]
        placeholders = ",".join("?" * len(doc_ids))

        # Step 2: seed entity IDs directly associated with those documents.
        async with self._conn.execute(
            f"SELECT id FROM graph_entities WHERE source_document_id IN ({placeholders})",
            doc_ids,
        ) as cur:
            entity_rows = await cur.fetchall()

        seed_ids = {row[0] for row in entity_rows}
        if not seed_ids:
            return set()

        # Step 3: expand 1 hop via graph_relationships (both directions).
        ent_placeholders = ",".join("?" * len(seed_ids))
        seed_list = list(seed_ids)
        async with self._conn.execute(
            f"""
            SELECT target_id FROM graph_relationships WHERE source_id IN ({ent_placeholders})
            UNION
            SELECT source_id FROM graph_relationships WHERE target_id IN ({ent_placeholders})
            """,
            seed_list + seed_list,
        ) as cur:
            neighbour_rows = await cur.fetchall()

        return seed_ids | {row[0] for row in neighbour_rows}

    # ------------------------------------------------------------------
    # Rerank score
    # ------------------------------------------------------------------

    async def _rerank_score(self, folder_path: str, query_text: str) -> float:
        """Mean RRF score of top-5 results from hybrid search scoped to *folder_path*."""
        if not query_text:
            return 0.0

        try:
            orchestrator = HybridSearchOrchestrator(
                conn=self._conn,
                qdrant_client=self._qdrant_client,
                embedding_service=self._embedding_service,
            )
            results = await orchestrator.search(
                query=query_text,
                top_k=5,
                workspace_path=folder_path,
                semantic_weight=0.7,
                keyword_weight=0.3,
            )
            if not results:
                return 0.0
            return sum(r.rrf_score for r in results) / len(results)
        except Exception:
            logger.debug("Rerank score fetch failed for folder %s", folder_path)
            return 0.0

    # ------------------------------------------------------------------
    # Chunk text helper
    # ------------------------------------------------------------------

    async def _get_first_chunk_text(self, document_id: str) -> str:
        """Return the text of the first chunk for *document_id*, or empty string."""
        async with self._conn.execute(
            "SELECT content FROM chunks WHERE document_id = ? ORDER BY chunk_index LIMIT 1",
            (document_id,),
        ) as cur:
            row = await cur.fetchone()
        return str(row[0]) if row else ""


def _label(score: float) -> str:
    if score >= _SCORE_STRONG_THRESHOLD:
        return _LABEL_STRONG
    if score >= _SCORE_GOOD_THRESHOLD:
        return _LABEL_GOOD
    return _LABEL_POSSIBLE
