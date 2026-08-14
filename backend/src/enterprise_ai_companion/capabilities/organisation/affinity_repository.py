"""Repository for entity-folder affinity weights (Phase 09b: Adaptive Placement Learning).

Stores per-(entity_name, folder_path) EMA weights updated from user feedback signals:
  - Accept (signal=1.0): user confirmed the folder was correct.
  - Dismiss (signal=0.0): user rejected all suggested folders.
  - Correction (signal=1.0 for chosen, 0.0 for wrong suggestions).

The weight converges toward 1.0 (neutral/positive) on accepts and toward 0.0
(suppression) on dismisses. The effective_weight formula applies a soft ramp
(first 5 observations scale linearly) and a 90-day half-life lazy time decay,
both applied at query time rather than write time.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

import aiosqlite

logger = logging.getLogger(__name__)

_EMA_ALPHA = 0.2
_NEUTRAL_WEIGHT = 1.0


class AffinityRepository:
    """Persists and retrieves entity-folder affinity weights from SQLite."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get_weights(
        self,
        entity_names: set[str],
        folder_path: str,
    ) -> dict[str, tuple[float, int, str]]:
        """Return affinity records for entities that have prior feedback against *folder_path*.

        Returns ``{entity_name: (weight, observations, updated_at)}`` for entities
        that have at least one feedback record. Entities with no record are absent
        from the result (caller interprets absence as neutral weight=1.0).
        """
        if not entity_names:
            return {}

        names_list = list(entity_names)
        placeholders = ",".join("?" * len(names_list))
        async with self._conn.execute(
            f"SELECT entity_name, weight, observations, updated_at "
            f"FROM entity_folder_affinity "
            f"WHERE folder_path = ? AND entity_name IN ({placeholders})",
            [folder_path, *names_list],
        ) as cur:
            rows = await cur.fetchall()

        return {row[0]: (row[1], row[2], row[3]) for row in rows}

    async def update_weights_bulk(
        self,
        entity_names: set[str],
        folder_path: str,
        signal: float,
    ) -> None:
        """Apply EMA weight update for all *entity_names* against *folder_path*.

        ``signal`` is 1.0 for positive feedback (accept/correction-chosen) or 0.0
        for negative feedback (dismiss/correction-wrong). For each entity the new
        weight is: ``alpha * signal + (1 - alpha) * old_weight`` where old_weight
        defaults to 1.0 (neutral) for entities without an existing record.
        """
        if not entity_names:
            return

        names_list = list(entity_names)
        now = datetime.now(UTC).isoformat()

        # Batch-read existing weights to avoid N round-trips.
        placeholders = ",".join("?" * len(names_list))
        async with self._conn.execute(
            f"SELECT entity_name, weight FROM entity_folder_affinity "
            f"WHERE folder_path = ? AND entity_name IN ({placeholders})",
            [folder_path, *names_list],
        ) as cur:
            existing: dict[str, float] = {row[0]: row[1] async for row in cur}

        for entity_name in names_list:
            old_weight = existing.get(entity_name, _NEUTRAL_WEIGHT)
            new_weight = _EMA_ALPHA * signal + (1 - _EMA_ALPHA) * old_weight
            await self._conn.execute(
                """
                INSERT INTO entity_folder_affinity
                    (entity_name, folder_path, weight, observations, updated_at)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(entity_name, folder_path) DO UPDATE SET
                    weight       = ?,
                    observations = observations + 1,
                    updated_at   = ?
                """,
                (entity_name, folder_path, new_weight, now, new_weight, now),
            )

        await self._conn.commit()
        logger.debug(
            "Updated affinity weights: folder=%s entities=%d signal=%.1f",
            folder_path, len(names_list), signal,
        )

    async def get_scorer_config(self, key: str) -> str | None:
        """Return a scorer_config value by key, or None if not set."""
        async with self._conn.execute(
            "SELECT value FROM scorer_config WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else None

    async def set_scorer_config(self, key: str, value: str) -> None:
        """Upsert a scorer_config entry."""
        now = datetime.now(UTC).isoformat()
        await self._conn.execute(
            """
            INSERT INTO scorer_config (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
            """,
            (key, value, now, value, now),
        )
        await self._conn.commit()
