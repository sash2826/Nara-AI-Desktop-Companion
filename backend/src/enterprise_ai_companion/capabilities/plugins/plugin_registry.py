"""SQLite-backed plugin registry.

Persists installed plugin metadata and their enabled/disabled state.
The registry is updated on every application startup during the plugin scan;
rows are upserted so re-installing or upgrading a plugin is idempotent.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import aiosqlite

from enterprise_ai_companion.capabilities.plugins.plugin_manifest import PluginManifest

logger = logging.getLogger(__name__)


@dataclass
class PluginRecord:
    """A plugin row as returned from the registry."""

    id: str
    display_name: str
    version: str
    description: str
    author: str
    permissions: list[str]
    enabled: bool
    installed_at: str


class PluginRegistry:
    """Read/write access to the plugins table."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def register(self, manifest: PluginManifest) -> None:
        """Insert or update a plugin row from *manifest*.

        Preserves the existing ``enabled`` state when a plugin is re-registered
        (e.g. after a version bump) so the user's choice is not lost.
        """
        manifest_json = json.dumps(
            {
                "name": manifest.name,
                "display_name": manifest.display_name,
                "version": manifest.version,
                "description": manifest.description,
                "author": manifest.author,
                "permissions": list(manifest.permissions),
                "entry_point": manifest.entry_point,
                "min_app_version": manifest.min_app_version,
            }
        )
        now = datetime.now(UTC).isoformat()

        await self._conn.execute(
            """
            INSERT INTO plugins (id, display_name, version, description, author,
                                 permissions, manifest_json, installed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                display_name  = excluded.display_name,
                version       = excluded.version,
                description   = excluded.description,
                author        = excluded.author,
                permissions   = excluded.permissions,
                manifest_json = excluded.manifest_json
            """,
            (
                manifest.name,
                manifest.display_name,
                manifest.version,
                manifest.description,
                manifest.author,
                json.dumps(list(manifest.permissions)),
                manifest_json,
                now,
            ),
        )
        await self._conn.commit()

    async def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        """Enable or disable a plugin by ID.

        Raises ``KeyError`` if the plugin is not registered.
        """
        async with self._conn.execute(
            "SELECT id FROM plugins WHERE id = ?", (plugin_id,)
        ) as cur:
            if await cur.fetchone() is None:
                raise KeyError(f"Plugin '{plugin_id}' is not registered")

        await self._conn.execute(
            "UPDATE plugins SET enabled = ? WHERE id = ?",
            (1 if enabled else 0, plugin_id),
        )
        await self._conn.commit()

    async def list_all(self) -> list[PluginRecord]:
        """Return all registered plugins, ordered by display_name."""
        async with self._conn.execute(
            "SELECT id, display_name, version, description, author, permissions, "
            "enabled, installed_at FROM plugins ORDER BY display_name"
        ) as cur:
            rows = await cur.fetchall()

        return [
            PluginRecord(
                id=row[0],
                display_name=row[1],
                version=row[2],
                description=row[3] or "",
                author=row[4] or "",
                permissions=json.loads(row[5]) if row[5] else [],
                enabled=bool(row[6]),
                installed_at=row[7],
            )
            for row in rows
        ]

    async def is_enabled(self, plugin_id: str) -> bool:
        """Return True if the plugin exists and is enabled."""
        async with self._conn.execute(
            "SELECT enabled FROM plugins WHERE id = ?", (plugin_id,)
        ) as cur:
            row = await cur.fetchone()
        return bool(row[0]) if row else False
