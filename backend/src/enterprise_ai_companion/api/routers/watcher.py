"""API endpoints for managing watched folders and querying watcher state."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.graph.knowledge_graph_service import KnowledgeGraphService
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider
from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.capabilities.indexing.file_watcher import WatchedFolder

logger = logging.getLogger(__name__)

router = APIRouter()


class AddFolderRequest(BaseModel):
    path: str


class WatchedFolderResponse(BaseModel):
    id: str
    path: str
    auto_index: bool
    added_at: str

    @classmethod
    def from_domain(cls, folder: WatchedFolder) -> "WatchedFolderResponse":
        return cls(
            id=folder.id,
            path=folder.path,
            auto_index=folder.auto_index,
            added_at=folder.added_at,
        )


class WatcherStatusResponse(BaseModel):
    running: bool
    watched_count: int
    folders: list[str]


@router.post("/folders", response_model=WatchedFolderResponse, status_code=201)
async def add_watched_folder(body: AddFolderRequest, request: Request) -> WatchedFolderResponse:
    """Register a new folder for automatic background indexing."""
    watcher = request.app.state.watcher
    try:
        folder = await watcher.add_folder(body.path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return WatchedFolderResponse.from_domain(folder)


@router.delete("/folders/{folder_id}", status_code=204)
async def remove_watched_folder(folder_id: str, request: Request) -> None:
    """Unregister a watched folder and purge all documents indexed from it."""
    watcher = request.app.state.watcher

    # Resolve folder path before removing so we can purge its documents.
    folders = await watcher.list_folders()
    folder = next((f for f in folders if f.id == folder_id), None)
    if folder is None:
        raise HTTPException(status_code=404, detail=f"Watched folder not found: {folder_id}")

    try:
        await watcher.remove_folder(folder_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await _purge_folder_documents(folder.path, request)


async def _purge_folder_documents(folder_path: str, request: Request) -> None:
    """Delete all indexed documents whose workspace_path matches folder_path.

    Mirrors the cascade used by bulk_delete_documents:
    chunks (SQLite + Qdrant) → graph entities → document row.
    Failures on individual documents are logged and do not abort the purge.
    """
    db = request.app.state.db
    doc_repo = DocumentRepository(db)
    qdrant_client = request.app.state.qdrant.get_client()
    chunk_repo = ChunkRepository(db, qdrant_client)
    graph_provider = getattr(request.app.state, "graph", None) or NullGraphProvider()
    graph_service = KnowledgeGraphService(graph_provider)

    docs = await doc_repo.list_by_workspace(folder_path)
    if not docs:
        logger.info("Folder purge: no indexed documents found for %s", folder_path)
        return

    logger.info("Folder purge: removing %d document(s) from %s", len(docs), folder_path)
    for doc in docs:
        try:
            await chunk_repo.delete_by_document(doc.id)
            try:
                await graph_service.delete_document(doc.id)
            except Exception as exc:
                logger.warning("Folder purge: graph cleanup failed for %s: %s", doc.id, exc)
            await doc_repo.delete_by_path(doc.file_path)
            logger.info("Folder purge: removed %s", doc.file_path)
        except Exception as exc:
            logger.error("Folder purge: failed to remove %s: %s", doc.file_path, exc)


@router.get("/folders", response_model=list[WatchedFolderResponse])
async def list_watched_folders(request: Request) -> list[WatchedFolderResponse]:
    """List all registered watched folders."""
    watcher = request.app.state.watcher
    folders = await watcher.list_folders()
    return [WatchedFolderResponse.from_domain(f) for f in folders]


@router.get("/status", response_model=WatcherStatusResponse)
async def get_watcher_status(request: Request) -> WatcherStatusResponse:
    """Return current watcher state."""
    watcher = request.app.state.watcher
    return WatcherStatusResponse(
        running=watcher.is_running,
        watched_count=len(watcher.watched_paths),
        folders=watcher.watched_paths,
    )
