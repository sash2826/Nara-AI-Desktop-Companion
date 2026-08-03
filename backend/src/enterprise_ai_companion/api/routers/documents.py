"""API endpoints for browsing indexed documents."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    workspace_path: str
    file_path: str
    char_count: int
    chunk_count: int
    indexed_at: str


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    request: Request,
    workspace_path: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[DocumentResponse]:
    """Return indexed documents, optionally filtered by workspace path."""
    repo = DocumentRepository(request.app.state.db)

    if workspace_path:
        docs = await repo.list_by_workspace(workspace_path)
        docs = docs[offset : offset + limit]
    else:
        docs = await repo.list_all(limit=limit, offset=offset)

    return [
        DocumentResponse(
            id=d.id,
            workspace_path=d.workspace_path,
            file_path=d.file_path,
            char_count=d.char_count,
            chunk_count=d.chunk_count,
            indexed_at=d.indexed_at,
        )
        for d in docs
    ]
