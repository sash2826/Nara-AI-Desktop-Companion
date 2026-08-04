"""API endpoints for triggering and monitoring workspace indexing."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from enterprise_ai_companion.capabilities.indexing.file_indexer import FileIndexer, IndexingResult

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


class IndexingErrorResponse(BaseModel):
    id: str
    workspace_path: str
    file_path: str
    error_message: str
    failed_at: str


# ---------------------------------------------------------------------------
# Background task runner
# ---------------------------------------------------------------------------

async def _run_indexing(
    task_id: str,
    workspace_path: str,
    tasks: dict[str, Any],
    indexer: FileIndexer,
) -> None:
    tasks[task_id]["status"] = "running"

    def _progress(result: IndexingResult) -> None:
        if tasks[task_id]["status"] == "cancelled":
            return
        tasks[task_id]["files_found"] = result.files_found
        tasks[task_id]["files_indexed"] = result.files_indexed
        tasks[task_id]["files_skipped"] = result.files_skipped
        tasks[task_id]["errors"] = list(result.errors)

    try:
        result = await indexer.index_workspace(workspace_path, progress_cb=_progress)
        # Only write final status if we weren't cancelled mid-run.
        if tasks[task_id]["status"] != "cancelled":
            tasks[task_id].update(
                {
                    "status": result.status,
                    "files_found": result.files_found,
                    "files_indexed": result.files_indexed,
                    "files_skipped": result.files_skipped,
                    "errors": result.errors,
                }
            )
    except asyncio.CancelledError:
        tasks[task_id]["status"] = "cancelled"
        logger.info("Indexing task %s was cancelled", task_id)
    except Exception as exc:
        logger.exception("Indexing task %s failed", task_id)
        tasks[task_id].update({"status": "failed", "errors": [str(exc)]})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/start", response_model=StartIndexingResponse, status_code=202)
async def start_indexing(body: StartIndexingRequest, request: Request) -> StartIndexingResponse:
    """Begin indexing a workspace directory in the background.

    The folder is automatically registered as a watched folder (if not already)
    so it appears in the Workspace > Folders tab and receives auto-reindex on
    future file changes — without triggering a second redundant indexing run.
    """
    task_id = str(uuid.uuid4())
    tasks: dict[str, Any] = request.app.state.indexing_tasks

    tasks[task_id] = {
        "status": "queued",
        "files_found": 0,
        "files_indexed": 0,
        "files_skipped": 0,
        "errors": [],
        "_task": None,
    }

    # Register the folder as watched before starting the index job so that the
    # Folders tab reflects it immediately. register_folder is idempotent (INSERT OR IGNORE).
    watcher = getattr(request.app.state, "watcher", None)
    if watcher is not None:
        try:
            await watcher.register_folder(body.workspace_path)
        except ValueError:
            # Path doesn't exist or isn't a directory — indexing will surface this error itself.
            pass
        except Exception as exc:
            logger.warning("Failed to register folder as watched: %s", exc)

    bg_task = asyncio.create_task(
        _run_indexing(
            task_id=task_id,
            workspace_path=body.workspace_path,
            tasks=tasks,
            indexer=request.app.state.file_indexer,
        )
    )
    tasks[task_id]["_task"] = bg_task

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


@router.delete("/cancel/{task_id}", status_code=204)
async def cancel_indexing(task_id: str, request: Request) -> None:
    """Cancel a running or queued indexing task."""
    tasks: dict[str, Any] = request.app.state.indexing_tasks
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    status = task["status"]
    if status not in ("queued", "running"):
        raise HTTPException(
            status_code=409,
            detail=f"Task '{task_id}' cannot be cancelled (status: {status}).",
        )

    task["status"] = "cancelled"
    bg_task: asyncio.Task | None = task.get("_task")
    if bg_task is not None and not bg_task.done():
        bg_task.cancel()

    logger.info("Cancellation requested for indexing task %s", task_id)


@router.get("/errors", response_model=list[IndexingErrorResponse])
async def list_indexing_errors(request: Request) -> list[IndexingErrorResponse]:
    """Return the list of persisted per-file indexing failures."""
    error_repo = getattr(request.app.state, "indexing_error_repo", None)
    if error_repo is None:
        return []
    errors = await error_repo.list_all()
    return [
        IndexingErrorResponse(
            id=e.id,
            workspace_path=e.workspace_path,
            file_path=e.file_path,
            error_message=e.error_message,
            failed_at=e.failed_at,
        )
        for e in errors
    ]


@router.delete("/errors", status_code=204)
async def clear_indexing_errors(request: Request) -> None:
    """Delete all persisted indexing errors."""
    error_repo = getattr(request.app.state, "indexing_error_repo", None)
    if error_repo is not None:
        await error_repo.clear()
