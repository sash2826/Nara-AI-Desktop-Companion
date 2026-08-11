"""CRUD repository for file placement recommendations (migration 011).

Each recommendation is created when a new file arrives in the OS Downloads
folder and the placement scorer produces at least one scored candidate. It
stays in 'pending' status until the user accepts or dismisses it via the
orb overlay or the main-window Suggestions inbox.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PlacementRecommendation:
    """A single file-placement recommendation record."""

    id: str
    source_path: str
    status: str  # "pending" | "accepted" | "dismissed"
    recommendations: list[dict[str, Any]]  # [{folder, score, label}, ...]
    accepted_folder: str | None
    created_at: str
    resolved_at: str | None


class RecommendationRepository:
    """Persists and retrieves file placement recommendations from SQLite."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        source_path: str,
        recommendations: list[dict[str, Any]],
    ) -> PlacementRecommendation:
        """Persist a new pending recommendation and return it."""
        rec_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        rec_json = json.dumps(recommendations)

        await self._conn.execute(
            """
            INSERT INTO file_placement_recommendations
                (id, source_path, status, recommendations, accepted_folder, created_at, resolved_at)
            VALUES (?, ?, 'pending', ?, NULL, ?, NULL)
            """,
            (rec_id, source_path, rec_json, created_at),
        )
        await self._conn.commit()

        logger.info(
            "Created placement recommendation %s for %s (%d candidates)",
            rec_id,
            source_path,
            len(recommendations),
        )
        return PlacementRecommendation(
            id=rec_id,
            source_path=source_path,
            status="pending",
            recommendations=recommendations,
            accepted_folder=None,
            created_at=created_at,
            resolved_at=None,
        )

    async def get(self, rec_id: str) -> PlacementRecommendation | None:
        """Return a single recommendation by ID, or None if not found."""
        async with self._conn.execute(
            "SELECT id, source_path, status, recommendations, accepted_folder, "
            "created_at, resolved_at FROM file_placement_recommendations WHERE id = ?",
            (rec_id,),
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            return None
        return _row_to_recommendation(row)

    async def list_pending(self) -> list[PlacementRecommendation]:
        """Return all recommendations with status='pending', oldest first."""
        async with self._conn.execute(
            "SELECT id, source_path, status, recommendations, accepted_folder, "
            "created_at, resolved_at FROM file_placement_recommendations "
            "WHERE status = 'pending' ORDER BY created_at ASC"
        ) as cur:
            rows = await cur.fetchall()
        return [_row_to_recommendation(r) for r in rows]

    async def count_pending(self) -> int:
        """Return the number of pending recommendations."""
        async with self._conn.execute(
            "SELECT COUNT(*) FROM file_placement_recommendations WHERE status = 'pending'"
        ) as cur:
            row = await cur.fetchone()
        return int(row[0]) if row else 0

    async def set_accepted(self, rec_id: str, folder: str) -> None:
        """Mark a recommendation as accepted with the chosen folder."""
        resolved_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            "UPDATE file_placement_recommendations "
            "SET status='accepted', accepted_folder=?, resolved_at=? WHERE id=?",
            (folder, resolved_at, rec_id),
        )
        await self._conn.commit()

    async def set_dismissed(self, rec_id: str) -> None:
        """Mark a recommendation as dismissed (file stays in Downloads)."""
        resolved_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            "UPDATE file_placement_recommendations "
            "SET status='dismissed', resolved_at=? WHERE id=?",
            (resolved_at, rec_id),
        )
        await self._conn.commit()


def _row_to_recommendation(row: Any) -> PlacementRecommendation:
    try:
        recs = json.loads(row[3]) if row[3] else []
    except (json.JSONDecodeError, TypeError):
        recs = []
    return PlacementRecommendation(
        id=row[0],
        source_path=row[1],
        status=row[2],
        recommendations=recs,
        accepted_folder=row[4],
        created_at=row[5],
        resolved_at=row[6],
    )
