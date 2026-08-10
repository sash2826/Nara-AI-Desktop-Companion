"""Structured audit logging for security-relevant application events.

Events are persisted to the audit_events SQLite table (migration 009) and also
written to the standard Python logger so they appear in the application log.

Usage:
    audit = AuditLogger(db_connection)
    await audit.log("indexing.started", {"workspace_path": path, "task_id": tid})
    await audit.log("backup.created", {"backup_id": bid})
    await audit.log("credential.updated", {"key_name": "apim-key"})
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

# Keys whose values must never be recorded in audit details, even if callers
# accidentally pass them.  This is a last-resort safety net.
_SENSITIVE_KEYS: frozenset[str] = frozenset({
    "password",
    "secret",
    "key",
    "token",
    "credential",
    "subscription_key",
    "api_key",
    "auth",
})


def _scrub(details: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of details with sensitive values replaced by '<redacted>'."""
    return {
        k: "<redacted>" if any(s in k.lower() for s in _SENSITIVE_KEYS) else v
        for k, v in details.items()
    }


class AuditLogger:
    """Writes audit events to the audit_events table and the application log."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def log(
        self,
        event_type: str,
        details: dict[str, Any] | None = None,
        actor: str = "system",
    ) -> None:
        """Record a single audit event.

        Args:
            event_type: Dot-namespaced verb, e.g. "indexing.started".
            details:    Optional context dict. Sensitive keys are scrubbed.
            actor:      Identity performing the action (default "system").
        """
        safe_details = _scrub(details) if details else None
        details_json = json.dumps(safe_details) if safe_details is not None else None
        event_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()

        try:
            await self._conn.execute(
                "INSERT INTO audit_events (id, event_type, actor, details, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_id, event_type, actor, details_json, created_at),
            )
            await self._conn.commit()
        except Exception as exc:
            # Audit logging must never crash the calling operation.
            logger.warning("Failed to persist audit event '%s': %s", event_type, exc)
            return

        logger.info(
            "AUDIT event_type=%s actor=%s details=%s",
            event_type,
            actor,
            details_json or "{}",
        )

    async def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most recent audit events, newest first."""
        limit = max(1, min(limit, 1000))
        async with self._conn.execute(
            "SELECT id, event_type, actor, details, created_at "
            "FROM audit_events ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()

        return [
            {
                "id": row[0],
                "event_type": row[1],
                "actor": row[2],
                "details": json.loads(row[3]) if row[3] else None,
                "created_at": row[4],
            }
            for row in rows
        ]
