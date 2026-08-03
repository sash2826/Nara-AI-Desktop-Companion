"""API endpoints for managing watched folders and querying watcher state."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.indexing.file_watcher import WatchedFolder

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
    """Unregister a watched folder by its ID."""
    watcher = request.app.state.watcher
    try:
        await watcher.remove_folder(folder_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
