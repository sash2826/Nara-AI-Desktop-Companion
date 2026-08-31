"""Persistence layer for indexing errors."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import aiosqlite


@dataclass
class IndexingError:
    id: str
    workspace_path: str
    file_path: str
    error_message: str
    failed_at: str


class IndexingErrorRepository:
    """Persists per-file indexing failures to SQLite."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def save(
        self, workspace_path: str, file_path: str, error_message: str
    ) -> IndexingError:
        error = IndexingError(
            id=str(uuid.uuid4()),
            workspace_path=workspace_path,
            file_path=file_path,
            error_message=error_message,
            failed_at=datetime.now(UTC).isoformat(),
        )
        # Keep only the latest error per file — a retried/re-run failure replaces
        # the previous row instead of stacking duplicates.
        await self._conn.execute(
            "DELETE FROM indexing_errors WHERE file_path = ?", (file_path,)
        )
        await self._conn.execute(
            "INSERT INTO indexing_errors (id, workspace_path, file_path, error_message, failed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (error.id, error.workspace_path, error.file_path, error.error_message, error.failed_at),
        )
        await self._conn.commit()
        return error

    async def delete_by_path(self, file_path: str) -> None:
        """Clear any stored error for a file — called once it indexes successfully."""
        await self._conn.execute(
            "DELETE FROM indexing_errors WHERE file_path = ?", (file_path,)
        )
        await self._conn.commit()

    async def list_all(self, limit: int = 500) -> list[IndexingError]:
        # Self-heal: an error is stale the moment its file appears in `documents`
        # (successfully indexed since). Drop those rows before returning.
        await self._conn.execute(
            "DELETE FROM indexing_errors "
            "WHERE file_path IN (SELECT file_path FROM documents)"
        )
        await self._conn.commit()
        async with self._conn.execute(
            "SELECT id, workspace_path, file_path, error_message, failed_at "
            "FROM indexing_errors ORDER BY failed_at DESC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
        return [IndexingError(**dict(row)) for row in rows]

    async def clear(self) -> None:
        await self._conn.execute("DELETE FROM indexing_errors")
        await self._conn.commit()
