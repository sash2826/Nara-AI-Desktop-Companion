"""REST endpoints for file organisation — placement recommendations.

These endpoints are called by the Rust IPC layer, which bridges to the
orb notification overlay and the main-window Suggestions inbox.

Routes:
    GET  /organisation/recommendations/pending/count
    GET  /organisation/recommendations/pending
    POST /organisation/recommendations/{id}/accept
    POST /organisation/recommendations/{id}/dismiss
    GET  /organisation/scorer/diagnostic
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.organisation.placement_scorer import _SCORE_MIN_THRESHOLD
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
    label: str  # "Most Likely" | "Likely" | "Possible"


class PendingRecommendationResponse(BaseModel):
    """Shape consumed by OrbNotificationOverlay.tsx and the main-window inbox."""

    id: str
    source_path: str
    candidates: list[CandidateItem]


class AcceptBody(BaseModel):
    folder: str


class ScorerDiagnosticResponse(BaseModel):
    current_threshold: float
    accept_count: int
    mean_accepted_top_score: float | None
    suggested_threshold: float | None
    min_sample_met: bool


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
    """Accept a recommendation — physically move the file, update the record, learn from feedback."""
    repo = request.app.state.recommendation_repo
    mover = request.app.state.file_mover
    recommendation_service = request.app.state.recommendation_service
    audit = getattr(request.app.state, "audit_logger", None)

    rec = await repo.get(recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=409, detail=f"Recommendation is already {rec.status}")

    try:
        new_path = await mover.move(rec.source_path, body.folder)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except OSError as exc:
        logger.error("File move failed for %s: %s", rec.source_path, exc)
        raise HTTPException(status_code=500, detail="File move failed") from exc

    await repo.set_accepted(recommendation_id, body.folder)

    # Update entity-folder affinity weights from the accept signal.
    await recommendation_service.record_accept(recommendation_id, body.folder)

    if audit:
        await audit.log(
            "organisation.file_moved",
            {
                "recommendation_id": recommendation_id,
                "source_path": rec.source_path,
                "target_path": new_path,
                "target_folder": body.folder,
            },
        )

    logger.info(
        "Recommendation %s accepted: %s → %s", recommendation_id, rec.source_path, new_path
    )


@router.post("/recommendations/{recommendation_id}/dismiss", status_code=204)
async def dismiss_recommendation(
    recommendation_id: str,
    request: Request,
) -> None:
    """Dismiss a recommendation without moving the file, and update affinity weights."""
    repo = request.app.state.recommendation_repo
    recommendation_service = request.app.state.recommendation_service

    rec = await repo.get(recommendation_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if rec.status != "pending":
        raise HTTPException(status_code=409, detail=f"Recommendation is already {rec.status}")

    # Update entity-folder affinity weights before marking dismissed (rec is still readable).
    await recommendation_service.record_dismiss(recommendation_id)

    await repo.set_dismissed(recommendation_id)
    logger.info(
        "Recommendation %s dismissed — file stays at %s", recommendation_id, rec.source_path
    )


@router.get("/scorer/diagnostic", response_model=ScorerDiagnosticResponse)
async def scorer_diagnostic(request: Request) -> Any:
    """Return threshold calibration diagnostic data.

    Computes accept statistics from historical recommendations and proposes a
    suggested threshold when at least 10 accepts have been recorded. The
    suggested value is never applied automatically — it is surfaced for review
    only (Q4=B decision).
    """
    repo = request.app.state.recommendation_repo
    db = request.app.state.db

    _MIN_SAMPLE = 10

    async with db.execute(
        "SELECT recommendations, accepted_folder "
        "FROM file_placement_recommendations "
        "WHERE status = 'accepted' AND accepted_folder IS NOT NULL"
    ) as cur:
        rows = await cur.fetchall()

    accept_count = len(rows)
    min_sample_met = accept_count >= _MIN_SAMPLE

    mean_accepted_top_score: float | None = None
    suggested_threshold: float | None = None

    if min_sample_met:
        scores: list[float] = []
        for recs_json, accepted_folder in rows:
            try:
                candidates = json.loads(recs_json) if recs_json else []
                # Find the score of the accepted folder in the candidate list.
                for c in candidates:
                    if c.get("folder") == accepted_folder:
                        scores.append(float(c["score"]))
                        break
                else:
                    # Accepted folder not found in candidates (edge case): use top-1 score.
                    if candidates:
                        scores.append(float(candidates[0].get("score", 0.0)))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass

        if scores:
            mean_accepted_top_score = round(sum(scores) / len(scores), 4)
            # Suggested threshold: 80% of the minimum accepted score. This places
            # the floor just below the least-confident recommendation the user accepted,
            # preserving coverage while reducing low-signal false positives.
            suggested_threshold = round(min(scores) * 0.8, 4)

    logger.info(
        "Scorer diagnostic: accepts=%d min_sample_met=%s suggested_threshold=%s",
        accept_count, min_sample_met, suggested_threshold,
    )
    return ScorerDiagnosticResponse(
        current_threshold=_SCORE_MIN_THRESHOLD,
        accept_count=accept_count,
        mean_accepted_top_score=mean_accepted_top_score,
        suggested_threshold=suggested_threshold,
        min_sample_met=min_sample_met,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _to_response(rec: PlacementRecommendation) -> PendingRecommendationResponse:
    return PendingRecommendationResponse(
        id=rec.id,
        source_path=rec.source_path,
        candidates=[
            CandidateItem(
                folder=c.get("folder", ""),
                score=float(c.get("score", 0.0)),
                label=c.get("label", "Possible"),
            )
            for c in rec.recommendations
        ],
    )
