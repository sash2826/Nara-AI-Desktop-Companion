"""Hybrid search orchestrator combining keyword and semantic search.

Uses Reciprocal Rank Fusion (RRF) to merge the two ranked lists into a single
unified result set. RRF is robust to score-scale differences between providers
and consistently outperforms naive score addition in information retrieval benchmarks.

RRF formula per result:
    rrf_score = Σ  1 / (k + rank_i)
where k=60 is a smoothing constant (standard literature value) and rank_i is the
1-based position of the chunk in provider i's result list.

Chunks appearing in both lists receive contributions from both; chunks in only one
list receive a single contribution. The merged list is deduplicated by chunk_id and
sorted by descending RRF score before top_k truncation.

Architecture:
    HybridSearchOrchestrator
        │
        ├── KeywordSearchProvider   (FTS5 BM25 over SQLite)
        ├── QdrantSearchProvider    (vector cosine over Qdrant)
        └── RRF merge + top_k slice
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import aiosqlite
from qdrant_client import QdrantClient

from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.retrieval.keyword_search import KeywordSearchProvider
from enterprise_ai_companion.capabilities.retrieval.qdrant_search import QdrantSearchProvider
from enterprise_ai_companion.capabilities.retrieval.search_models import SearchResult

logger = logging.getLogger(__name__)

# RRF smoothing constant — standard literature value.
_RRF_K: int = 60

# Fetch multiplier: each provider retrieves more results than requested so RRF
# has enough material to work with after deduplication and filtering.
_FETCH_MULTIPLIER: int = 3


@dataclass(frozen=True)
class HybridSearchResult:
    """A single result from the hybrid search pipeline.

    The rrf_score is the combined Reciprocal Rank Fusion score — higher is better.
    The keyword_rank and semantic_rank fields record the 1-based position in each
    provider's list (None if the chunk was absent from that provider's results).
    """

    chunk_id: str
    document_id: str
    document_path: str
    chunk_index: int
    content: str
    rrf_score: float
    keyword_rank: int | None
    semantic_rank: int | None


class HybridSearchOrchestrator:
    """Runs keyword and semantic search concurrently, merges via RRF.

    Designed as a thin coordinator — each provider owns its own retrieval
    logic; the orchestrator only combines results.
    """

    def __init__(
        self,
        conn: aiosqlite.Connection,
        qdrant_client: QdrantClient,
        embedding_service: EmbeddingService,
    ) -> None:
        self._keyword = KeywordSearchProvider(conn=conn)
        self._semantic = QdrantSearchProvider(
            conn=conn,
            qdrant_client=qdrant_client,
            embedding_service=embedding_service,
        )

    async def search(
        self,
        query: str,
        top_k: int = 10,
        workspace_path: str | None = None,
        semantic_weight: float = 1.0,
        keyword_weight: float = 1.0,
    ) -> list[HybridSearchResult]:
        """Execute hybrid search and return merged results.

        Args:
            query: Preprocessed query string (stop-words removed, expansions added).
            top_k: Maximum number of results to return.
            workspace_path: Optional workspace filter applied by both providers.
            semantic_weight: Multiplier applied to the semantic RRF contribution (default 1.0).
            keyword_weight: Multiplier applied to the keyword RRF contribution (default 1.0).

        Returns:
            Results ordered by descending RRF score, deduplicated by chunk_id.
        """
        if not query.strip():
            return []

        fetch_k = top_k * _FETCH_MULTIPLIER

        # Run both providers concurrently — neither blocks the other.
        keyword_results, semantic_results = await asyncio.gather(
            self._keyword_safe(query, fetch_k, workspace_path),
            self._semantic_safe(query, fetch_k, workspace_path),
        )

        merged = _rrf_merge(
            keyword_results=keyword_results,
            semantic_results=semantic_results,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
        )

        logger.debug(
            "Hybrid search: query=%r keyword=%d semantic=%d merged=%d top_k=%d",
            query,
            len(keyword_results),
            len(semantic_results),
            len(merged),
            top_k,
        )

        return merged[:top_k]

    # ------------------------------------------------------------------
    # Internal helpers — isolate provider failures from each other
    # ------------------------------------------------------------------

    async def _keyword_safe(
        self, query: str, top_k: int, workspace_path: str | None
    ) -> list[SearchResult]:
        try:
            return await self._keyword.search(query, top_k=top_k, workspace_path=workspace_path)
        except Exception as exc:
            logger.warning("Keyword provider failed during hybrid search: %s", exc)
            return []

    async def _semantic_safe(
        self, query: str, top_k: int, workspace_path: str | None
    ) -> list[SearchResult]:
        try:
            return await self._semantic.search(query, top_k=top_k, workspace_path=workspace_path)
        except Exception as exc:
            logger.warning("Semantic provider failed during hybrid search: %s", exc)
            return []


# ---------------------------------------------------------------------------
# RRF implementation
# ---------------------------------------------------------------------------

def _rrf_merge(
    keyword_results: list[SearchResult],
    semantic_results: list[SearchResult],
    semantic_weight: float = 1.0,
    keyword_weight: float = 1.0,
) -> list[HybridSearchResult]:
    """Merge two ranked lists using Reciprocal Rank Fusion.

    Each chunk accumulates an RRF score from every list it appears in.
    Chunks in both lists receive contributions from both, boosting their rank.
    """
    # Build rank maps: chunk_id → 1-based position.
    keyword_rank: dict[str, int] = {r.chunk_id: i + 1 for i, r in enumerate(keyword_results)}
    semantic_rank: dict[str, int] = {r.chunk_id: i + 1 for i, r in enumerate(semantic_results)}

    # Collect all unique chunk_ids from both lists.
    all_chunk_ids: dict[str, SearchResult] = {}
    for r in keyword_results:
        all_chunk_ids[r.chunk_id] = r
    for r in semantic_results:
        if r.chunk_id not in all_chunk_ids:
            all_chunk_ids[r.chunk_id] = r

    results: list[HybridSearchResult] = []
    for chunk_id, result in all_chunk_ids.items():
        kw_rank = keyword_rank.get(chunk_id)
        sem_rank = semantic_rank.get(chunk_id)

        rrf_score = 0.0
        if kw_rank is not None:
            rrf_score += keyword_weight / (_RRF_K + kw_rank)
        if sem_rank is not None:
            rrf_score += semantic_weight / (_RRF_K + sem_rank)

        results.append(
            HybridSearchResult(
                chunk_id=chunk_id,
                document_id=result.document_id,
                document_path=result.document_path,
                chunk_index=result.chunk_index,
                content=result.content,
                rrf_score=rrf_score,
                keyword_rank=kw_rank,
                semantic_rank=sem_rank,
            )
        )

    results.sort(key=lambda r: r.rrf_score, reverse=True)
    return results
