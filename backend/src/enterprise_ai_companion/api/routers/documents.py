"""API endpoints for browsing and managing indexed documents."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.graph.knowledge_graph_service import KnowledgeGraphService
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider
from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.infrastructure.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    workspace_path: str
    file_path: str
    char_count: int
    chunk_count: int
    indexed_at: str


def _system_path_prefixes() -> list[str]:
    """Return normalised system-path prefixes from config (lower-cased for case-insensitive match)."""
    raw = get_config().system_index_paths
    return [p.strip().lower().rstrip("/\\") for p in raw.split(",") if p.strip()]


def _is_system_document(file_path: str, prefixes: list[str]) -> bool:
    normalised = file_path.lower().replace("\\", "/")
    return any(normalised.startswith(p.replace("\\", "/")) for p in prefixes)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    request: Request,
    workspace_path: str | None = Query(default=None),
    include_system: bool = Query(default=False),
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[DocumentResponse]:
    """Return indexed documents, optionally filtered by workspace path.

    System documents (paths listed in EAC_SYSTEM_INDEX_PATHS) are excluded by
    default. Pass include_system=true to include them.
    """
    repo = DocumentRepository(request.app.state.db)

    if workspace_path:
        docs = await repo.list_by_workspace(workspace_path)
        docs = docs[offset : offset + limit]
    else:
        docs = await repo.list_all(limit=limit, offset=offset)

    if not include_system:
        prefixes = _system_path_prefixes()
        if prefixes:
            docs = [d for d in docs if not _is_system_document(d.file_path, prefixes)]

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


class BulkDeleteRequest(BaseModel):
    document_ids: list[str]


@router.delete("/bulk", status_code=204)
async def bulk_delete_documents(body: BulkDeleteRequest, request: Request) -> None:
    """Remove multiple documents and all their chunks in a single request.

    Each document is deleted independently. Failures are logged but do not
    abort the remaining deletions — the endpoint always returns 204.
    """
    db = request.app.state.db
    doc_repo = DocumentRepository(db)
    qdrant_client = request.app.state.qdrant.get_client()
    chunk_repo = ChunkRepository(db, qdrant_client)
    graph_provider = getattr(request.app.state, "graph", None) or NullGraphProvider()
    graph_service = KnowledgeGraphService(graph_provider)

    for document_id in body.document_ids:
        try:
            async with db.execute(
                "SELECT id, file_path FROM documents WHERE id = ?", (document_id,)
            ) as cur:
                row = await cur.fetchone()
            if row is None:
                logger.warning("Bulk delete: document %s not found, skipping.", document_id)
                continue
            file_path = row[1]
            await chunk_repo.delete_by_document(document_id)
            try:
                await graph_service.delete_document(document_id)
            except Exception as exc:
                logger.warning("Graph cleanup failed for document %s: %s", document_id, exc)
            await doc_repo.delete_by_path(file_path)
            logger.info("Bulk delete: removed document %s (%s)", document_id, file_path)
        except Exception as exc:
            logger.error("Bulk delete: failed to delete document %s: %s", document_id, exc)


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, request: Request) -> None:
    """Remove a document and all its chunks from SQLite, Qdrant, and the knowledge graph."""
    db = request.app.state.db
    doc_repo = DocumentRepository(db)
    qdrant_client = request.app.state.qdrant.get_client()
    chunk_repo = ChunkRepository(db, qdrant_client)

    graph_provider = getattr(request.app.state, "graph", None) or NullGraphProvider()
    graph_service = KnowledgeGraphService(graph_provider)

    # Verify the document exists before attempting deletion.
    async with db.execute(
        "SELECT id, file_path FROM documents WHERE id = ?", (document_id,)
    ) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    file_path = row[1]

    # Remove chunks from SQLite + FTS5 + Qdrant vectors.
    await chunk_repo.delete_by_document(document_id)

    # Remove graph entities (best-effort — graph failures must not abort the operation).
    try:
        await graph_service.delete_document(document_id)
    except Exception as exc:
        logger.warning("Graph cleanup failed for document %s: %s", document_id, exc)

    # Remove the document row last so FK constraints are satisfied throughout.
    await doc_repo.delete_by_path(file_path)
    logger.info("Document deleted: %s (%s)", document_id, file_path)
