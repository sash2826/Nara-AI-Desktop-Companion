"""Embeddings router — POST /embeddings."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

# Module-level singleton — loaded once when the first request arrives.
_service = EmbeddingService()


class EmbedRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be empty")
        return v


class EmbedResponse(BaseModel):
    embedding: list[float]
    dim: int


@router.post("", response_model=EmbedResponse)
async def create_embedding(body: EmbedRequest) -> EmbedResponse:
    """Generate a BGE-M3 embedding vector for the supplied text.

    Returns a 1024-dimensional float vector suitable for semantic search and
    similarity comparison.
    """
    try:
        vector = _service.generate(body.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return EmbedResponse(embedding=vector, dim=len(vector))
