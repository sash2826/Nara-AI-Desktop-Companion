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
from enterprise_ai_companion.capabilities.graph.graph_query_service import GraphQueryService
from enterprise_ai_companion.capabilities.graph.graph_provider import GraphProvider
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider
from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
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
    graph_entities: list[str] = field(default_factory=list)

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
        graph_provider: GraphProvider | None = None,
        chunk_repo: ChunkRepository | None = None,
    ) -> None:
        self._orchestrator = HybridSearchOrchestrator(
            conn=conn,
            qdrant_client=qdrant_client,
            embedding_service=embedding_service,
        )
        self._reranker: ChunkReranker = reranker or HeuristicReranker()
        self._graph_svc = GraphQueryService(graph_provider or NullGraphProvider())
        self._chunk_repo = chunk_repo

    async def assemble(
        self,
        query: str,
        workspace_path: str | None = None,
        use_graph: bool = True,
    ) -> ContextPayload:
        """Retrieve and assemble context chunks for the given query.

        Pipeline:
          1. Hybrid vector+keyword search (RRF).
          2. Heuristic reranking.
          3. Quality filter + token budget.
          4. Graph expansion (optional, best-effort): expand retrieval via
             entity neighbourhoods when the graph provider is online.

        Args:
            query: Raw user query (will be preprocessed internally).
            workspace_path: Optional folder path to restrict retrieval to.
            use_graph: When True, graph-augmented expansion is attempted.
                       Falls back to vector-only when the graph is offline.

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

        # Graph expansion — add graph-referenced chunks not yet in the set.
        graph_entities: list[str] = []
        if use_graph:
            chunks, graph_entities = await self._expand_via_graph(
                query=pq.search_text,
                chunks=chunks,
                workspace_path=workspace_path,
            )

        logger.debug(
            "ContextAssembler: query=%r candidates=%d reranked=%d retained=%d graph_entities=%d",
            query,
            len(candidates),
            len(reranked),
            len(chunks),
            len(graph_entities),
        )

        return ContextPayload(
            chunks=chunks,
            active_workspace=workspace_path,
            total_chars=sum(len(c.content) for c in chunks),
            graph_entities=graph_entities,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _expand_via_graph(
        self,
        query: str,
        chunks: list[ContextChunk],
        workspace_path: str | None,
    ) -> tuple[list[ContextChunk], list[str]]:
        """Supplement vector-retrieved chunks with graph-neighbour chunks.

        For each token in the query that matches an entity in the graph, the
        connected document IDs are fetched. Chunks from those documents that
        are not already in the retrieved set are fetched from the chunk
        repository and appended (subject to the overall budget cap).

        Returns:
            Tuple of (updated chunks list, entity names that contributed).
        """
        if self._chunk_repo is None:
            return chunks, []

        already_seen: set[tuple[str, int]] = {
            (c.document_id, c.chunk_index) for c in chunks
        }
        graph_entities: list[str] = []
        extra_chunks: list[ContextChunk] = []
        total_chars = sum(len(c.content) for c in chunks)

        # Use individual query tokens as entity lookup keys — coarse but cheap.
        tokens = [t.strip() for t in query.split() if len(t.strip()) > 3]

        for token in tokens:
            if len(chunks) + len(extra_chunks) >= _MAX_CONTEXT_CHUNKS:
                break
            if total_chars >= _MAX_CONTEXT_CHARS:
                break

            try:
                doc_ids = await self._graph_svc.get_connected_documents(token)
            except Exception:
                continue

            if not doc_ids:
                continue

            graph_entities.append(token)

            for doc_id in doc_ids:
                if len(chunks) + len(extra_chunks) >= _MAX_CONTEXT_CHUNKS:
                    break

                try:
                    doc_chunks = await self._chunk_repo.get_by_document(doc_id)
                except Exception:
                    continue

                for dc in doc_chunks:
                    if (dc.document_id, dc.chunk_index) in already_seen:
                        continue
                    if total_chars + len(dc.content) > _MAX_CONTEXT_CHARS:
                        continue
                    already_seen.add((dc.document_id, dc.chunk_index))
                    total_chars += len(dc.content)
                    extra_chunks.append(
                        ContextChunk(
                            chunk_id=dc.id,
                            document_id=dc.document_id,
                            document_path=getattr(dc, "document_path", ""),
                            chunk_index=dc.chunk_index,
                            content=dc.content,
                            rrf_score=0.0,
                            semantic_rank=None,
                            keyword_rank=None,
                        )
                    )

        return chunks + extra_chunks, graph_entities

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
