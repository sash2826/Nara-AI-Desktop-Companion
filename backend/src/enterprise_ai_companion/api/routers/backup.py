"""API endpoints for backup management."""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from enterprise_ai_companion.infrastructure.backup import BackupService

router = APIRouter(prefix="/backup", tags=["backup"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class CreateBackupRequest(BaseModel):
    notes: str = ""


class BackupResultResponse(BaseModel):
    backup_id: str
    backup_path: str
    created_at: str
    sqlite_size_bytes: int
    qdrant_collections: list[str]
    status: str


class BackupSummaryResponse(BaseModel):
    backup_id: str
    backup_path: str
    created_at: str
    status: str
    sqlite_size_bytes: int


class DeleteBackupResponse(BaseModel):
    deleted: bool
    backup_id: str


# ---------------------------------------------------------------------------
# Dependency helper
# ---------------------------------------------------------------------------

def _get_service(request: Request) -> BackupService:
    conn: aiosqlite.Connection = request.app.state.db
    qdrant_client = request.app.state.qdrant.get_client() if request.app.state.qdrant else None
    return BackupService(db_conn=conn, qdrant_client=qdrant_client)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/create", response_model=BackupResultResponse)
async def create_backup(
    body: CreateBackupRequest, request: Request
) -> BackupResultResponse:
    """Create a timestamped backup of SQLite and Qdrant collection metadata."""
    service = _get_service(request)
    result = await service.create_backup(notes=body.notes)
    return BackupResultResponse(
        backup_id=result.backup_id,
        backup_path=result.backup_path,
        created_at=result.created_at,
        sqlite_size_bytes=result.sqlite_size_bytes,
        qdrant_collections=result.qdrant_collections,
        status=result.status,
    )


@router.get("/list", response_model=list[BackupSummaryResponse])
async def list_backups(request: Request) -> list[BackupSummaryResponse]:
    """Return all backups ordered most recent first."""
    service = _get_service(request)
    summaries = await service.list_backups()
    return [
        BackupSummaryResponse(
            backup_id=s.backup_id,
            backup_path=s.backup_path,
            created_at=s.created_at,
            status=s.status,
            sqlite_size_bytes=s.sqlite_size_bytes,
        )
        for s in summaries
    ]


@router.delete("/{backup_id}", response_model=DeleteBackupResponse)
async def delete_backup(backup_id: str, request: Request) -> DeleteBackupResponse:
    """Delete a backup by ID."""
    service = _get_service(request)
    deleted = await service.delete_backup(backup_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Backup '{backup_id}' not found.")
    return DeleteBackupResponse(deleted=True, backup_id=backup_id)
