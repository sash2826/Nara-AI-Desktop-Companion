"""API endpoints for triggering and monitoring workspace indexing."""

from __future__ import annotations

import asyncio
import logging
import re as _re
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from enterprise_ai_companion.capabilities.indexing.file_indexer import FileIndexer, IndexingResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/indexing", tags=["indexing"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

def _safe_error(exc: Exception) -> str:
    """Strip filesystem paths from exception messages before returning to the client."""
    msg = str(exc)
    msg = _re.sub(r"[A-Za-z]:\\[^\s,;\"']+", "<path>", msg)
    msg = _re.sub(r"/[^\s,;\"']{4,}", "<path>", msg)
    return msg[:300]


class StartIndexingRequest(BaseModel):
    workspace_path: str

    @field_validator("workspace_path")
    @classmethod
    def must_be_valid_directory(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("workspace_path must not be empty")
        resolved = Path(v).resolve()
        if not resolved.exists():
            raise ValueError("workspace_path does not exist")
        if not resolved.is_dir():
            raise ValueError("workspace_path must be a directory")
        return str(resolved)


class StartIndexingResponse(BaseModel):
    task_id: str
    status: str


class IndexingStatusResponse(BaseModel):
    task_id: str
    status: str
    stage: str  # "indexing" | "building_graph" | "linking_entities" | "completed"
    files_found: int
    files_indexed: int
    files_skipped: int
    errors: list[str]
    graph_files_total: int
    graph_files_processed: int


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
    app_state: Any,
) -> None:
    tasks[task_id]["status"] = "running"
    audit = getattr(app_state, "audit_logger", None)

    if audit is not None:
        await audit.log("indexing.started", {"task_id": task_id, "workspace_path": workspace_path})

    def _progress(result: IndexingResult) -> None:
        if tasks[task_id]["status"] == "cancelled":
            return
        tasks[task_id]["files_found"] = result.files_found
        tasks[task_id]["files_indexed"] = result.files_indexed
        tasks[task_id]["files_skipped"] = result.files_skipped
        tasks[task_id]["errors"] = list(result.errors)

    def _graph_progress(processed: int, total: int, stage: str) -> None:
        if tasks[task_id]["status"] == "cancelled":
            return
        tasks[task_id]["stage"] = stage
        tasks[task_id]["graph_files_processed"] = processed
        tasks[task_id]["graph_files_total"] = total

    try:
        result = await indexer.index_workspace(
            workspace_path,
            progress_cb=_progress,
            graph_progress_cb=_graph_progress,
        )
        # Only write final status if we weren't cancelled mid-run.
        if tasks[task_id]["status"] != "cancelled":
            tasks[task_id].update(
                {
                    "files_found": result.files_found,
                    "files_indexed": result.files_indexed,
                    "files_skipped": result.files_skipped,
                    "errors": result.errors,
                }
            )

            # Await Pass 2 + 3 (graph extraction + entity linking). The task was
            # already created inside index_workspace; awaiting it here keeps the
            # router task alive so the status endpoint reflects real progress
            # instead of showing "completed" while the graph is still building.
            if result.graph_task is not None and not result.graph_task.done():
                try:
                    await result.graph_task
                except asyncio.CancelledError:
                    result.graph_task.cancel()
                    raise

        if tasks[task_id]["status"] != "cancelled":
            tasks[task_id].update(
                {
                    "status": result.status,
                    "stage": "completed",
                }
            )
            if audit is not None:
                await audit.log(
                    "indexing.completed",
                    {
                        "task_id": task_id,
                        "files_found": result.files_found,
                        "files_indexed": result.files_indexed,
                        "files_skipped": result.files_skipped,
                        "error_count": len(result.errors),
                    },
                )
            # Reload dynamic abbreviation expansions from the newly indexed documents.
            abbrev_repo = getattr(app_state, "abbreviation_repo", None)
            preprocessor = getattr(app_state, "preprocessor", None)
            if abbrev_repo is not None and preprocessor is not None:
                try:
                    dynamic = await abbrev_repo.load_all()
                    preprocessor.merge_expansions(dynamic)
                    logger.info(
                        "Abbreviation expansions reloaded after indexing: %d entries",
                        len(dynamic),
                    )
                except Exception as exc:
                    logger.warning("Failed to reload abbreviation expansions: %s", exc)

            # Trigger organisation audit for newly indexed files so placement
            # recommendations appear without requiring a manual Organise trigger.
            audit_service = getattr(app_state, "audit_service", None)
            if audit_service is not None:
                asyncio.create_task(audit_service.run_audit())
    except asyncio.CancelledError:
        tasks[task_id]["status"] = "cancelled"
        logger.info("Indexing task %s was cancelled", task_id)
    except Exception as exc:
        logger.exception("Indexing task %s failed", task_id)
        tasks[task_id].update({"status": "failed", "errors": [_safe_error(exc)]})
        if audit is not None:
            await audit.log("indexing.failed", {"task_id": task_id, "error": _safe_error(exc)})


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
        "stage": "indexing",
        "workspace_path": body.workspace_path,
        "files_found": 0,
        "files_indexed": 0,
        "files_skipped": 0,
        "errors": [],
        "graph_files_total": 0,
        "graph_files_processed": 0,
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
            app_state=request.app.state,
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
        stage=task.get("stage", "indexing"),
        files_found=task["files_found"],
        files_indexed=task["files_indexed"],
        files_skipped=task["files_skipped"],
        errors=task["errors"],
        graph_files_total=task.get("graph_files_total", 0),
        graph_files_processed=task.get("graph_files_processed", 0),
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
