"""API endpoints for triggering and monitoring workspace indexing."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

import aiosqlite
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.indexing.file_indexer import FileIndexer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/indexing", tags=["indexing"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class StartIndexingRequest(BaseModel):
    workspace_path: str

    @field_validator("workspace_path")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("workspace_path must not be empty")
        return v.strip()


class StartIndexingResponse(BaseModel):
    task_id: str
    status: str


class IndexingStatusResponse(BaseModel):
    task_id: str
    status: str
    files_found: int
    files_indexed: int
    files_skipped: int
    errors: list[str]


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def _get_db(request: Request) -> aiosqlite.Connection:
    return request.app.state.db  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Background task runner
# ---------------------------------------------------------------------------

async def _run_indexing(
    task_id: str,
    workspace_path: str,
    tasks: dict[str, Any],
    db: aiosqlite.Connection,
    qdrant_provider: Any,
) -> None:
    tasks[task_id]["status"] = "running"
    try:
        doc_repo = DocumentRepository(db)
        chunk_repo = ChunkRepository(db, qdrant_provider.get_client())
        embedding_service = EmbeddingService()
        indexer = FileIndexer(doc_repo, chunk_repo, embedding_service)

        result = await indexer.index_workspace(workspace_path)

        tasks[task_id].update(
            {
                "status": result.status,
                "files_found": result.files_found,
                "files_indexed": result.files_indexed,
                "files_skipped": result.files_skipped,
                "errors": result.errors,
            }
        )
    except Exception as exc:
        logger.exception("Indexing task %s failed", task_id)
        tasks[task_id].update({"status": "failed", "errors": [str(exc)]})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/start", response_model=StartIndexingResponse, status_code=202)
async def start_indexing(body: StartIndexingRequest, request: Request) -> StartIndexingResponse:
    """Begin indexing a workspace directory in the background."""
    task_id = str(uuid.uuid4())
    tasks: dict[str, Any] = request.app.state.indexing_tasks

    tasks[task_id] = {
        "status": "queued",
        "files_found": 0,
        "files_indexed": 0,
        "files_skipped": 0,
        "errors": [],
    }

    asyncio.create_task(
        _run_indexing(
            task_id=task_id,
            workspace_path=body.workspace_path,
            tasks=tasks,
            db=_get_db(request),
            qdrant_provider=request.app.state.qdrant,
        )
    )

    return StartIndexingResponse(task_id=task_id, status="queued")


@router.get("/status/{task_id}", response_model=IndexingStatusResponse)
async def get_indexing_status(task_id: str, request: Request) -> IndexingStatusResponse:
    """Return the current status of an indexing task."""
    tasks: dict[str, Any] = request.app.state.indexing_tasks
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return IndexingStatusResponse(
        task_id=task_id,
        status=task["status"],
        files_found=task["files_found"],
        files_indexed=task["files_indexed"],
        files_skipped=task["files_skipped"],
        errors=task["errors"],
    )
