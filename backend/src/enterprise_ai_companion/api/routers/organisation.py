"""REST endpoints for file organisation — placement recommendations and audit.

These endpoints are called by the Rust IPC layer, which bridges to the
orb notification overlay and the main-window Suggestions inbox.

Routes:
    GET  /organisation/recommendations/pending/count
    GET  /organisation/recommendations/pending
    POST /organisation/recommendations/{id}/accept
    POST /organisation/recommendations/{id}/dismiss
    POST /organisation/audit
    GET  /organisation/audit/status
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.organisation.recommendation_repository import (
    PlacementRecommendation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organisation", tags=["organisation"])


# ---------------------------------------------------------------------------
# Response / request models
# ---------------------------------------------------------------------------


class CandidateItem(BaseModel):
    folder: str
    score: float
    label: str  # "Strong" | "Good" | "Possible"


class PendingRecommendationResponse(BaseModel):
    """Shape consumed by OrbNotificationOverlay.tsx and the main-window inbox."""

    id: str
    source_path: str
    candidates: list[CandidateItem]


class AcceptBody(BaseModel):
    folder: str
    conflict_strategy: str = "error"  # "error" | "replace" | "rename"


class AuditStatusResponse(BaseModel):
    running: bool
    analysed: int
    total: int
    found: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/recommendations/pending/count")
async def pending_count(request: Request) -> dict[str, int]:
    """Return the number of pending placement recommendations."""
    repo = request.app.state.recommendation_repo
    count = await repo.count_pending()
    return {"count": count}


@router.get("/recommendations/pending", response_model=list[PendingRecommendationResponse])
async def list_pending(request: Request) -> Any:
    """Return all pending recommendations, oldest first."""
    repo = request.app.state.recommendation_repo
    recs: list[PlacementRecommendation] = await repo.list_pending()
    return [_to_response(r) for r in recs]


@router.post("/recommendations/{recommendation_id}/accept", status_code=204)
async def accept_recommendation(
    recommendation_id: str,
    body: AcceptBody,
    request: Request,
) -> None:
    """Accept a recommendation — physically move the file and update the record."""
    repo = request.app.state.recommendation_repo
    mover = request.app.state.file_mover
    audit = getattr(request.app.state, "audit_logger", None)

    rec = await repo.get(recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=409, detail=f"Recommendation is already {rec.status}")

    try:
        new_path = await mover.move(rec.source_path, body.folder, body.conflict_strategy)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except OSError as exc:
        logger.error("File move failed for %s: %s", rec.source_path, exc)
        raise HTTPException(status_code=500, detail="File move failed") from exc

    # File is on disk at new_path — mark accepted even if the DB update fails so
    # we never return 500 to the client after a successful OS-level move.
    try:
        await repo.set_accepted(recommendation_id, body.folder)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "set_accepted failed for %s after successful move to %s: %s",
            recommendation_id, new_path, exc,
        )

    if audit:
        try:
            await audit.log(
                "organisation.file_moved",
                {
                    "recommendation_id": recommendation_id,
                    "source_path": rec.source_path,
                    "target_path": new_path,
                    "target_folder": body.folder,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Audit log failed for recommendation %s: %s", recommendation_id, exc)

    logger.info(
        "Recommendation %s accepted: %s → %s", recommendation_id, rec.source_path, new_path
    )


@router.post("/recommendations/{recommendation_id}/dismiss", status_code=204)
async def dismiss_recommendation(
    recommendation_id: str,
    request: Request,
) -> None:
    """Dismiss a recommendation without moving the file."""
    repo = request.app.state.recommendation_repo

    rec = await repo.get(recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=409, detail=f"Recommendation is already {rec.status}")

    await repo.set_dismissed(recommendation_id)
    logger.info("Recommendation %s dismissed — file stays at %s", recommendation_id, rec.source_path)


# ---------------------------------------------------------------------------
# Audit endpoints
# ---------------------------------------------------------------------------


@router.post("/audit", status_code=202)
async def run_audit(background_tasks: BackgroundTasks, request: Request) -> dict[str, str]:
    """Start an on-demand organisation audit. Returns 202 immediately.

    The audit runs as a background task and iterates all indexed documents,
    surfacing reorganisation suggestions via the placement scorer. Poll
    GET /organisation/audit/status for progress.
    """
    audit_service = getattr(request.app.state, "audit_service", None)
    if audit_service is None:
        raise HTTPException(status_code=503, detail="Audit service not available")

    if audit_service.state.running:
        return {"status": "already_running"}

    background_tasks.add_task(_run_audit_task, audit_service)
    logger.info("[AUDIT] Audit requested via API — starting background task")
    return {"status": "started"}


async def _run_audit_task(audit_service) -> None:
    """Thin wrapper so BackgroundTasks can call the async audit."""
    await audit_service.run_audit()


@router.get("/audit/status", response_model=AuditStatusResponse)
async def get_audit_status(request: Request) -> AuditStatusResponse:
    """Return the current audit progress."""
    audit_service = getattr(request.app.state, "audit_service", None)
    if audit_service is None:
        return AuditStatusResponse(running=False, analysed=0, total=0, found=0)

    state = audit_service.state
    return AuditStatusResponse(
        running=state.running,
        analysed=state.analysed,
        total=state.total,
        found=state.found,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _to_response(rec: PlacementRecommendation) -> PendingRecommendationResponse:
    label_map = {"Most Likely": "Strong", "Likely": "Good"}
    return PendingRecommendationResponse(
        id=rec.id,
        source_path=rec.source_path,
        candidates=[
            CandidateItem(
                folder=c.get("folder", ""),
                score=float(c.get("score", 0.0)),
                label=label_map.get(c.get("label", "Possible"), c.get("label", "Possible")),
            )
            for c in rec.recommendations
        ],
    )
