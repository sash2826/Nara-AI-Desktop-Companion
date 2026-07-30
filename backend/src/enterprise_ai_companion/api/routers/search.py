"""API endpoints for semantic and keyword document search."""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator

from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator import HybridSearchOrchestrator
from enterprise_ai_companion.capabilities.retrieval.keyword_search import KeywordSearchProvider
from enterprise_ai_companion.capabilities.retrieval.qdrant_search import QdrantSearchProvider
from enterprise_ai_companion.capabilities.retrieval.query_preprocessor import QueryPreprocessor

router = APIRouter(prefix="/search", tags=["search"])

_preprocessor = QueryPreprocessor()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    workspace_path: str | None = None

    @field_validator("query")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query must not be empty")
        return v.strip()


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_path: str
    chunk_index: int
    content: str
    score: float


class SemanticSearchResponse(BaseModel):
    results: list[SearchResultItem]


class KeywordSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    workspace_path: str | None = None

    @field_validator("query")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query must not be empty")
        return v.strip()


class KeywordSearchResponse(BaseModel):
    results: list[SearchResultItem]


class HybridSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=50)
    workspace_path: str | None = None
    semantic_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    keyword_weight: float = Field(default=1.0, ge=0.0, le=10.0)

    @field_validator("query")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query must not be empty")
        return v.strip()


class HybridSearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_path: str
    chunk_index: int
    content: str
    rrf_score: float
    keyword_rank: int | None
    semantic_rank: int | None


class HybridSearchResponse(BaseModel):
    results: list[HybridSearchResultItem]


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def _get_db(request: Request) -> aiosqlite.Connection:
    return request.app.state.db  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    body: SemanticSearchRequest, request: Request
) -> SemanticSearchResponse:
    """Return the top-k document chunks most semantically similar to the query."""
    pq = _preprocessor.process(body.query)
    provider = QdrantSearchProvider(
        conn=_get_db(request),
        qdrant_client=request.app.state.qdrant.get_client(),
        embedding_service=EmbeddingService(),
    )
    results = await provider.search(
        query=pq.search_text,
        top_k=body.top_k,
        workspace_path=body.workspace_path,
    )
    return SemanticSearchResponse(
        results=[
            SearchResultItem(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                document_path=r.document_path,
                chunk_index=r.chunk_index,
                content=r.content,
                score=r.score,
            )
            for r in results
        ]
    )


@router.post("/keyword", response_model=KeywordSearchResponse)
async def keyword_search(
    body: KeywordSearchRequest, request: Request
) -> KeywordSearchResponse:
    """Return up to top_k document chunks matching the query via FTS5 keyword search."""
    pq = _preprocessor.process(body.query)
    provider = KeywordSearchProvider(conn=_get_db(request))
    results = await provider.search(
        query=pq.search_text,
        top_k=body.top_k,
        workspace_path=body.workspace_path,
    )
    return KeywordSearchResponse(
        results=[
            SearchResultItem(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                document_path=r.document_path,
                chunk_index=r.chunk_index,
                content=r.content,
                score=r.score,
            )
            for r in results
        ]
    )


@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(
    body: HybridSearchRequest, request: Request
) -> HybridSearchResponse:
    """Return top_k document chunks ranked by Reciprocal Rank Fusion over keyword + semantic results.

    Runs keyword (FTS5) and semantic (Qdrant) search concurrently, then merges
    the two ranked lists using RRF. Chunks appearing in both lists are boosted.

    Use ``semantic_weight`` and ``keyword_weight`` to bias the blend (both default 1.0).
    """
    pq = _preprocessor.process(body.query)
    orchestrator = HybridSearchOrchestrator(
        conn=_get_db(request),
        qdrant_client=request.app.state.qdrant.get_client(),
        embedding_service=EmbeddingService(),
    )
    results = await orchestrator.search(
        query=pq.search_text,
        top_k=body.top_k,
        workspace_path=body.workspace_path,
        semantic_weight=body.semantic_weight,
        keyword_weight=body.keyword_weight,
    )
    return HybridSearchResponse(
        results=[
            HybridSearchResultItem(
                chunk_id=r.chunk_id,
                document_id=r.document_id,
                document_path=r.document_path,
                chunk_index=r.chunk_index,
                content=r.content,
                rrf_score=r.rrf_score,
                keyword_rank=r.keyword_rank,
                semantic_rank=r.semantic_rank,
            )
            for r in results
        ]
    )
