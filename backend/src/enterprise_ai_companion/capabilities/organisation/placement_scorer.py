"""Placement scorer for file organisation recommendations.

Combines two signals to score each candidate folder for a newly-indexed file:

  score = 0.75 × graph_score + 0.25 × rerank_score

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
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiosqlite

from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator import (
    HybridSearchOrchestrator,
)

logger = logging.getLogger(__name__)

_GRAPH_WEIGHT = 0.75
_RERANK_WEIGHT = 0.25

_LABEL_STRONG = "Most Likely"
_LABEL_GOOD = "Likely"
_LABEL_POSSIBLE = "Possible"

_SCORE_STRONG_THRESHOLD = 0.60
_SCORE_GOOD_THRESHOLD = 0.30
# Candidates below this threshold are suppressed entirely — avoids spurious
# "Possible" suggestions when there is no meaningful topical overlap.
# Calibrated for Overlap coefficient scoring (not Jaccard). Files with zero
# intersection always score 0.0, so any positive threshold suffices to filter
# them. 0.05 allows a 1-entity overlap on a 5-entity file (score = 0.14)
# while excluding noise from rerank alone.
_SCORE_MIN_THRESHOLD = 0.10

# The graph score must reach this value before the rerank signal is added.
# Raising from >0.0 to >=0.10 eliminates false positives caused by a single
# coincidental shared entity (e.g. "photography" linking an equipment guide
# to a travel folder, or "data" linking a personal document to any project).
_GRAPH_GATE_THRESHOLD = 0.10

# When fewer than this many canonical entities are extracted (small or sparse
# files, or FOREIGN KEY races during concurrent indexing), fall back to
# tokenising the filename so the scorer has at least a filename-level signal.
_SPARSE_ENTITY_THRESHOLD = 5

# Minimum number of entities that must overlap before a graph score is awarded.
# A single shared word (e.g. "data", "report") is too fragile and causes false
# positives for unrelated files. Two distinct overlapping entities are required.
_MIN_INTERSECTION_COUNT = 2

_FILENAME_STOPWORDS: frozenset[str] = frozenset({
    "pdf", "doc", "docx", "txt", "md",
    "the", "a", "an", "of", "in", "on", "at", "for", "and", "or",
    "to", "by", "from", "with",
})

# Generic business/document terms that appear in almost any file and cannot
# discriminate between project folders. Filtering them from the overlap
# computation prevents spurious matches caused by boilerplate vocabulary.
_GENERIC_TERMS: frozenset[str] = frozenset({
    "data", "report", "analysis", "management", "system",
    "process", "review", "plan", "strategy", "performance", "service",
    "solution", "information", "project", "team", "work", "business",
    "company", "organization", "requirement", "document", "guide",
    "overview", "update", "summary", "assessment", "evaluation",
    "implementation", "development", "application",
    "infrastructure", "technology", "digital", "enterprise", "global",
    "new", "key", "main", "core", "high", "low", "current", "future",
    "total", "list", "type", "use", "based", "level", "area",
    "structure", "approach", "objective", "result", "output", "input",
    "value", "quality", "standard", "policy", "procedure", "control",
})


def _filename_keywords(file_path: str) -> set[str]:
    """Tokenise a file/folder stem into lowercase keyword terms.

    Works on both file paths (uses stem) and directory paths (uses final
    directory name). Used to supplement sparse entity sets and as folder-name
    anchors so semantically-named empty folders still participate in scoring.
    Four-digit year tokens are excluded as non-discriminative.
    """
    p = Path(file_path)
    # For directories use the folder name; for files use the stem.
    name = p.name if p.is_dir() or not p.suffix else p.stem
    words = re.sub(r"[_\-\.\s]+", " ", name).lower().split()
    return {
        w for w in words
        if len(w) > 2
        and w not in _FILENAME_STOPWORDS
        and not re.fullmatch(r"\d{4}", w)
    }


def _expand_for_matching(canonicals: set[str]) -> set[str]:
    """Expand multi-word canonical entity strings into individual word tokens.

    LLM extraction often produces multi-word entities like
    'japan 2026 photography itinerary' or 'golden-hour'. Exact-string matching
    misses the connection to single-word canonical terms like 'japan' or
    'photography' that the same concept is stored under in other documents.

    This function adds individual word tokens from multi-word entities so the
    overlap computation is vocabulary-bridged. The original strings are kept
    alongside the expansions so the entity set remains a superset.
    """
    expanded = set(canonicals)
    for entity in canonicals:
        if " " in entity or "-" in entity:
            tokens = re.sub(r"[-\s]+", " ", entity).lower().split()
            expanded |= {
                t for t in tokens
                if len(t) > 2
                and t not in _FILENAME_STOPWORDS
                and not re.fullmatch(r"\d{4}", t)
            }
    return expanded


@dataclass(frozen=True)
class FolderScore:
    """Score for a single candidate folder."""

    folder: str
    score: float
    label: str
    graph_score: float = 0.0
    rerank_score: float = 0.0


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

        raw_canonicals = await self._get_canonical_set_for_document(document_id)
        # Expand multi-word entities into individual word tokens so that
        # 'japan 2026 photography itinerary' contributes 'japan' and
        # 'photography' to the matching vocabulary.
        new_file_canonicals = _expand_for_matching(raw_canonicals)
        first_chunk_text = await self._get_first_chunk_text(document_id)

        logger.info(
            "[PLACEMENT] doc=%s canonical entities (%d → %d after expansion): %s",
            document_id, len(raw_canonicals), len(new_file_canonicals),
            sorted(new_file_canonicals)[:20],
        )

        tasks = [
            self._score_folder(
                folder_path=folder,
                new_file_canonicals=new_file_canonicals,
                query_text=first_chunk_text,
            )
            for folder in candidate_folder_paths
        ]
        folder_scores: list[FolderScore] = await asyncio.gather(*tasks)

        for fs in folder_scores:
            logger.info(
                "[PLACEMENT] folder=%s graph=%.4f rerank=%.4f score=%.4f label=%s",
                fs.folder, fs.graph_score, fs.rerank_score, fs.score, fs.label,
            )

        scored = sorted(
            (fs for fs in folder_scores if fs.score >= _SCORE_MIN_THRESHOLD),
            key=lambda fs: fs.score,
            reverse=True,
        )

        if not scored:
            logger.info(
                "[PLACEMENT] All %d candidate(s) below threshold %.2f — no recommendation",
                len(folder_scores), _SCORE_MIN_THRESHOLD,
            )

        return [
            {"folder": fs.folder, "score": round(fs.score, 4), "label": fs.label}
            for fs in scored[:3]
        ]

    async def _score_folder(
        self,
        folder_path: str,
        new_file_canonicals: set[str],
        query_text: str,
    ) -> FolderScore:
        graph_s, rerank_s = await asyncio.gather(
            self._graph_score(folder_path, new_file_canonicals),
            self._rerank_score(folder_path, query_text),
        )
        # Graph score is the gate. RRF rerank returns small positive scores for
        # ANY query, so rerank alone creates false positives for unrelated files.
        # We require graph_s >= _GRAPH_GATE_THRESHOLD (not merely >0) so that a
        # single coincidental entity overlap (score ≈ 0.05–0.08) is suppressed.
        if graph_s < _GRAPH_GATE_THRESHOLD:
            return FolderScore(
                folder=folder_path, score=0.0, label=_LABEL_POSSIBLE,
                graph_score=graph_s, rerank_score=rerank_s,
            )
        combined = _GRAPH_WEIGHT * graph_s + _RERANK_WEIGHT * rerank_s
        return FolderScore(
            folder=folder_path,
            score=combined,
            label=_label(combined),
            graph_score=graph_s,
            rerank_score=rerank_s,
        )

    # ------------------------------------------------------------------
    # Graph score — canonical-name Jaccard
    # ------------------------------------------------------------------

    async def _graph_score(
        self,
        folder_path: str,
        new_file_canonicals: set[str],
    ) -> float:
        """Overlap coefficient on canonical entity names between the new file and folder.

        Uses min(|A|, |B|) as the denominator (Szymkiewicz-Simpson / overlap
        coefficient) rather than Jaccard's union. Jaccard penalises a genuine
        match when the folder has many more entities than the new file — e.g. a
        5-entity file with 1 matching term against a 30-entity folder gives
        Jaccard = 1/34 ≈ 0.03 but Overlap = 1/5 = 0.20, which correctly
        reflects that 20 % of the new file's topics are represented.
        """
        if not new_file_canonicals:
            return 0.0

        folder_canonicals = await self._get_canonical_set_for_folder(folder_path)
        if not folder_canonicals:
            return 0.0

        # Strip generic boilerplate terms before computing overlap so that
        # words like "data", "report", "framework" cannot single-handedly
        # create a false match between an unrelated file and a project folder.
        effective_new = new_file_canonicals - _GENERIC_TERMS
        effective_folder = folder_canonicals - _GENERIC_TERMS

        intersection = effective_new & effective_folder

        # Require at least _MIN_INTERSECTION_COUNT distinct domain-specific
        # entities to overlap. A single shared word is too fragile a signal.
        if len(intersection) < _MIN_INTERSECTION_COUNT:
            logger.debug(
                "[PLACEMENT] graph_score folder=%s intersection=%d < min=%d — suppressed",
                folder_path, len(intersection), _MIN_INTERSECTION_COUNT,
            )
            return 0.0

        denominator = min(len(effective_new), len(effective_folder))
        logger.debug(
            "[PLACEMENT] graph_score folder=%s intersection=%d denominator=%d",
            folder_path, len(intersection), denominator,
        )
        return len(intersection) / denominator if denominator else 0.0

    async def _get_canonical_set_for_document(self, document_id: str) -> set[str]:
        """Return canonical names for entities in *document_id*, expanded 1 hop.

        When fewer than _SPARSE_ENTITY_THRESHOLD entities are found (LLM
        non-determinism, concurrent-indexing FOREIGN KEY races, or very small
        files), the canonical set is supplemented with keyword terms tokenised
        from the file name so the scorer has at least a filename-level signal.
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

        # Expand 1 hop — include canonical names of directly related entities.
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

        # Sparse fallback: supplement with filename keyword terms so the scorer
        # is not completely blind when LLM extraction misses obvious terms like
        # 'tokyo' from Tokyo_Sunrise_Sunset_Times.pdf.
        if len(canonicals) < _SPARSE_ENTITY_THRESHOLD:
            async with self._conn.execute(
                "SELECT file_path FROM documents WHERE id = ?", (document_id,)
            ) as cur:
                doc_row = await cur.fetchone()
            if doc_row:
                filename_terms = _filename_keywords(doc_row[0])
                logger.debug(
                    "[PLACEMENT] sparse entity set (%d) for doc=%s — adding filename terms: %s",
                    len(canonicals), document_id, sorted(filename_terms),
                )
                canonicals |= filename_terms

        return canonicals

    async def _get_canonical_set_for_folder(self, folder_path: str) -> set[str]:
        """Return canonical entity names for *folder_path*, expanded 1 hop.

        Always supplements with folder-name keyword terms so that a semantically
        named folder (e.g. "Photography Trip - Japan 2026" → 'photography',
        'trip', 'japan') can still participate in scoring even when the folder
        is empty or its indexed content uses different vocabulary.

        Multi-word entities in the folder's corpus are further decomposed into
        individual tokens to bridge vocabulary mismatches with incoming files.
        """
        async with self._conn.execute(
            "SELECT id FROM documents WHERE workspace_path = ?",
            (folder_path,),
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

                # Expand 1 hop via relationships.
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

        # Folder-name semantic anchors — always present regardless of indexed
        # content. An empty "Photography Trip - Japan 2026" folder gains
        # {'photography', 'trip', 'japan'} as matching vocabulary.
        canonicals |= _filename_keywords(folder_path)

        # Token-expand multi-word entity strings so the folder's vocabulary
        # bridges to single-word entities in incoming files.
        return _expand_for_matching(canonicals)

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
