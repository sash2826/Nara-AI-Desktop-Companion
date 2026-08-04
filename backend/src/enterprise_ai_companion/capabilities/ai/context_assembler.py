"""Context assembly service for the AI retrieval pipeline.

Wraps the hybrid search orchestrator with quality filtering, deduplication,
and token-budget enforcement so callers receive a ready-to-use ranked chunk
list rather than raw search output.

Epic 4.2 (reranker) and Epic 4.4 (suggested queries) both import from this
module — keep it free of FastAPI / router dependencies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import aiosqlite
from qdrant_client import QdrantClient

from enterprise_ai_companion.capabilities.ai.reranker import ChunkReranker, HeuristicReranker, RankedChunk
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator import (
    HybridSearchOrchestrator,
    HybridSearchResult,
)
from enterprise_ai_companion.capabilities.retrieval.query_preprocessor import QueryPreprocessor

logger = logging.getLogger(__name__)

# Retrieval configuration constants.
_CANDIDATE_FETCH_K: int = 20   # initial candidates from hybrid search
_MAX_CONTEXT_CHUNKS: int = 5   # maximum chunks passed to the LLM
_MAX_CONTEXT_CHARS: int = 12_000  # ~3 k tokens at 4 chars/token

# Minimum RRF score to retain a chunk — 1/(60+200) ≈ 0.0038.
# Rank 200 is below any result from a fetch-20 call in practice, so this
# filters only pathological zero-score artefacts, not real results.
_MIN_RRF_SCORE: float = 0.004

_preprocessor = QueryPreprocessor()


@dataclass(frozen=True)
class ContextChunk:
    """A single retrieved chunk, ready for LLM injection."""

    chunk_id: str
    document_id: str
    document_path: str
    chunk_index: int
    content: str
    rrf_score: float
    semantic_rank: int | None
    keyword_rank: int | None


@dataclass
class ContextPayload:
    """Assembled context ready to be injected into the LLM system message."""

    chunks: list[ContextChunk] = field(default_factory=list)
    active_workspace: str | None = None
    total_chars: int = 0

    def format_for_prompt(self) -> str:
        """Return a formatted string suitable for the system message context block."""
        if not self.chunks:
            return ""
        parts = [
            f"[{i + 1}] Source: {c.document_path} (chunk {c.chunk_index})\n{c.content}"
            for i, c in enumerate(self.chunks)
        ]
        return "\n\n---\n\n".join(parts)


class ContextAssembler:
    """Builds a quality-filtered, budget-capped ContextPayload from a user query.

    Pipeline:
      1. Hybrid search — fetch _CANDIDATE_FETCH_K candidates via RRF.
      2. Reranking — re-order candidates by query-to-chunk relevance signal.
      3. Filter & budget — drop noise, deduplicate, enforce char/count limits.

    The reranker is injected at construction time so a cross-encoder
    implementation can replace the default heuristic without changing callers.
    """

    def __init__(
        self,
        conn: aiosqlite.Connection,
        qdrant_client: QdrantClient,
        embedding_service: EmbeddingService,
        reranker: ChunkReranker | None = None,
    ) -> None:
        self._orchestrator = HybridSearchOrchestrator(
            conn=conn,
            qdrant_client=qdrant_client,
            embedding_service=embedding_service,
        )
        self._reranker: ChunkReranker = reranker or HeuristicReranker()

    async def assemble(
        self,
        query: str,
        workspace_path: str | None = None,
    ) -> ContextPayload:
        """Retrieve and assemble context chunks for the given query.

        Args:
            query: Raw user query (will be preprocessed internally).
            workspace_path: Optional folder path to restrict retrieval to.

        Returns:
            A ContextPayload with deduplicated, budget-capped chunks.
        """
        if not query.strip():
            return ContextPayload(active_workspace=workspace_path)

        pq = _preprocessor.process(query)

        try:
            candidates = await self._orchestrator.search(
                query=pq.search_text,
                top_k=_CANDIDATE_FETCH_K,
                workspace_path=workspace_path,
            )
        except Exception as exc:
            logger.warning("ContextAssembler: hybrid search failed: %s", exc)
            return ContextPayload(active_workspace=workspace_path)

        # Rerank before applying budget so the most query-relevant chunks
        # are preferred over the highest-RRF chunks.
        reranked = self._reranker.rerank(
            query=query,
            candidates=candidates,
            top_n=_CANDIDATE_FETCH_K,
        )

        chunks = self._filter_and_budget(reranked)

        logger.debug(
            "ContextAssembler: query=%r candidates=%d reranked=%d retained=%d",
            query,
            len(candidates),
            len(reranked),
            len(chunks),
        )

        return ContextPayload(
            chunks=chunks,
            active_workspace=workspace_path,
            total_chars=sum(c.chunk_index for c in chunks),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _filter_and_budget(
        self, candidates: list[RankedChunk]
    ) -> list[ContextChunk]:
        """Apply quality filtering, deduplication, and token budget.

        Candidates arrive pre-sorted by rerank_score (descending).
        The RRF score floor still filters pathological zero-score artefacts.
        """

        # 1. Quality filter: drop noise below the minimum RRF score.
        filtered = [c for c in candidates if c.rrf_score >= _MIN_RRF_SCORE]

        # 2. Deduplication: one entry per (document_id, chunk_index) pair.
        seen: set[tuple[str, int]] = set()
        deduped: list[RankedChunk] = []
        for c in filtered:
            key = (c.document_id, c.chunk_index)
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        # 3. Token budget: accumulate from highest rerank_score until budget reached.
        retained: list[ContextChunk] = []
        total_chars = 0
        for c in deduped:
            if len(retained) >= _MAX_CONTEXT_CHUNKS:
                break
            if total_chars + len(c.content) > _MAX_CONTEXT_CHARS:
                break
            total_chars += len(c.content)
            retained.append(
                ContextChunk(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    document_path=c.document_path,
                    chunk_index=c.chunk_index,
                    content=c.content,
                    rrf_score=c.rrf_score,
                    semantic_rank=c.semantic_rank,
                    keyword_rank=c.keyword_rank,
                )
            )

        return retained
