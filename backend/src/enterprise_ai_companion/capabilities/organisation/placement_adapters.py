"""Production adapters for PlacementScorer ports.

Each adapter satisfies one port interface and owns the infrastructure details
(raw SQL, HybridSearchOrchestrator) that PlacementScorer must not know about.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import aiosqlite

from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.organisation.placement_ports import (
    GraphScorePort,
    RerankPort,
    expand_for_matching,
    filename_bigrams,
    filename_keywords,
)
from enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator import (
    HybridSearchOrchestrator,
)

logger = logging.getLogger(__name__)

_SPARSE_ENTITY_THRESHOLD = 5


class SqliteGraphScoreAdapter(GraphScorePort):
    """Satisfies GraphScorePort using direct SQLite queries.

    Owns all SQL against graph_entities, graph_relationships, documents, and
    chunks so schema changes are contained here rather than inside the scorer.
    """

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get_canonicals_for_document(
        self,
        document_id: str,
        file_path: str,
    ) -> set[str]:
        """Return canonical names for entities in *document_id*, expanded 1 hop.

        Falls back to filename keyword terms when fewer than
        _SPARSE_ENTITY_THRESHOLD entities are found (LLM non-determinism,
        concurrent-indexing FOREIGN KEY races, or very small files).
        """
        async with self._conn.execute(
            "SELECT id, canonical FROM graph_entities WHERE source_document_id = ?",
            (document_id,),
        ) as cur:
            rows = await cur.fetchall()

        if not rows:
            entity_ids: list[str] = []
            canonicals: set[str] = set()
        else:
            entity_ids = [row[0] for row in rows]
            canonicals = {row[1] for row in rows if row[1]}

        if entity_ids:
            placeholders = ",".join("?" * len(entity_ids))
            async with self._conn.execute(
                f"""
                SELECT e.canonical FROM graph_entities e
                WHERE e.id IN (
                    SELECT target_id FROM graph_relationships WHERE source_id IN ({placeholders})
                    UNION
                    SELECT source_id FROM graph_relationships WHERE target_id IN ({placeholders})
                ) AND e.canonical IS NOT NULL
                """,
                entity_ids + entity_ids,
            ) as cur:
                neighbour_rows = await cur.fetchall()
            canonicals |= {row[0] for row in neighbour_rows}

        # Always supplement with filename keywords — the filename is a strong
        # placement signal (e.g. "Access_Control_Plan_v2" → "access") and
        # is cheap to compute. The sparse-entity fallback below kept this
        # conditional, but graph extraction is occasionally incomplete due to
        # LLM non-determinism or FK races, so we always add it.
        filename_terms = filename_keywords(file_path)
        if len(canonicals) < _SPARSE_ENTITY_THRESHOLD:
            logger.debug(
                "[PLACEMENT] sparse entity set (%d) for doc=%s — filename terms: %s",
                len(canonicals), document_id, sorted(filename_terms),
            )
        canonicals |= filename_terms
        # Bigrams (e.g. "depot charging", "warehouse picking") are compound
        # domain signals that directly match multi-word corpus entities, giving
        # sparse files enough intersection points to clear the MIN_INTERSECTION gate.
        canonicals |= filename_bigrams(file_path)

        return canonicals

    async def get_canonicals_for_folder(self, folder_path: str) -> set[str]:
        """Return canonical entity names for *folder_path*, expanded 1 hop.

        Always supplements with folder-name keyword terms so that a
        semantically-named empty folder still participates in scoring.
        """
        prefix = folder_path.rstrip(os.sep) + os.sep
        async with self._conn.execute(
            "SELECT id FROM documents WHERE file_path LIKE ?",
            (prefix + "%",),
        ) as cur:
            doc_rows = await cur.fetchall()

        canonicals: set[str] = set()

        if doc_rows:
            doc_ids = [row[0] for row in doc_rows]
            placeholders = ",".join("?" * len(doc_ids))

            async with self._conn.execute(
                f"SELECT id, canonical FROM graph_entities WHERE source_document_id IN ({placeholders})",
                doc_ids,
            ) as cur:
                entity_rows = await cur.fetchall()

            if entity_rows:
                entity_ids = [row[0] for row in entity_rows]
                canonicals = {row[1] for row in entity_rows if row[1]}

                ent_placeholders = ",".join("?" * len(entity_ids))
                async with self._conn.execute(
                    f"""
                    SELECT e.canonical FROM graph_entities e
                    WHERE e.id IN (
                        SELECT target_id FROM graph_relationships WHERE source_id IN ({ent_placeholders})
                        UNION
                        SELECT source_id FROM graph_relationships WHERE target_id IN ({ent_placeholders})
                    ) AND e.canonical IS NOT NULL
                    """,
                    entity_ids + entity_ids,
                ) as cur:
                    neighbour_rows = await cur.fetchall()
                canonicals |= {row[0] for row in neighbour_rows}

        canonicals |= filename_keywords(folder_path)
        return expand_for_matching(canonicals)

    async def get_known_folder_paths(
        self,
        exclude_paths: set[str] | None = None,
        max_candidates: int = 150,
    ) -> list[str]:
        """Return unique parent directories inferred from indexed file paths.

        Ranked by document count descending; ancestor directories pruned so
        only leaf directories are returned.
        """
        async with self._conn.execute("SELECT file_path FROM documents") as cur:
            rows = await cur.fetchall()

        exclude = exclude_paths or set()
        folder_counts: dict[str, int] = {}
        for row in rows:
            parent = str(Path(row[0]).parent)
            if parent not in exclude:
                folder_counts[parent] = folder_counts.get(parent, 0) + 1

        ranked = sorted(folder_counts, key=lambda p: folder_counts[p], reverse=True)
        capped = ranked[:max_candidates]

        capped_set = set(capped)
        return [
            f for f in capped
            if not any(
                other != f and other.startswith(f.rstrip(os.sep) + os.sep)
                for other in capped_set
            )
        ]


class HybridRerankAdapter(RerankPort):
    """Satisfies RerankPort using HybridSearchOrchestrator.

    Owns both the chunk-text fetch and the search call so PlacementScorer
    needs no database connection or Qdrant client for reranking.
    """

    def __init__(
        self,
        conn: aiosqlite.Connection,
        embedding_service: EmbeddingService,
        qdrant_client: Any,
    ) -> None:
        self._conn = conn
        self._embedding_service = embedding_service
        self._qdrant_client = qdrant_client

    async def rerank(
        self,
        document_id: str,
        folder_path: str,
        top_k: int = 30,
    ) -> float:
        """Return mean RRF score of top-5 results from hybrid search scoped to *folder_path*.

        Fetches the first chunk of *document_id* as the query text. Searches
        without a workspace_path filter (all documents use the watched root as
        workspace_path, so subfolder filtering is done post-hoc by file_path prefix).
        """
        query_text = await self._get_first_chunk_text(document_id)
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
                top_k=top_k,
                workspace_path=None,
                semantic_weight=0.7,
                keyword_weight=0.3,
            )
            if not results:
                return 0.0

            prefix = folder_path.rstrip(os.sep) + os.sep
            folder_results = [r for r in results if r.document_path.startswith(prefix)]
            if not folder_results:
                return 0.0

            top5 = folder_results[:5]
            return sum(r.rrf_score for r in top5) / len(top5)
        except Exception:
            logger.debug("Rerank score fetch failed for folder %s", folder_path)
            return 0.0

    async def _get_first_chunk_text(self, document_id: str) -> str:
        async with self._conn.execute(
            "SELECT content FROM chunks WHERE document_id = ? ORDER BY chunk_index LIMIT 1",
            (document_id,),
        ) as cur:
            row = await cur.fetchone()
        return str(row[0]) if row else ""
