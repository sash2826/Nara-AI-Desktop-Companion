"""Repository for indexed document metadata stored in SQLite."""

from __future__ import annotations

import os
from dataclasses import dataclass

import aiosqlite


def _like_prefix(folder_path: str) -> str:
    """Return a LIKE pattern that matches any file_path under folder_path.

    Strips trailing separators, appends the OS separator, then escapes the
    two LIKE wildcards (% and _) that could appear in real folder names.
    The pattern ends with a bare % so SQLite does a prefix scan.
    """
    base = folder_path.rstrip("/\\") + os.sep
    escaped = base.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return escaped + "%"


@dataclass(frozen=True)
class IndexedDocument:
    id: str
    workspace_path: str
    file_path: str
    file_hash: str
    char_count: int
    chunk_count: int
    indexed_at: str


class DocumentRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def upsert(self, doc: IndexedDocument) -> None:
        await self._conn.execute(
            """
            INSERT INTO documents (id, workspace_path, file_path, file_hash, char_count, chunk_count, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                workspace_path = excluded.workspace_path,
                file_hash      = excluded.file_hash,
                char_count     = excluded.char_count,
                chunk_count    = excluded.chunk_count,
                indexed_at     = excluded.indexed_at
            """,
            (
                doc.id,
                doc.workspace_path,
                doc.file_path,
                doc.file_hash,
                doc.char_count,
                doc.chunk_count,
                doc.indexed_at,
            ),
        )
        await self._conn.commit()

    async def get_by_path(self, file_path: str) -> IndexedDocument | None:
        async with self._conn.execute(
            "SELECT id, workspace_path, file_path, file_hash, char_count, chunk_count, indexed_at "
            "FROM documents WHERE file_path = ?",
            (file_path,),
        ) as cur:
            row = await cur.fetchone()
        if row is None:
            return None
        return IndexedDocument(**dict(row))

    async def list_by_workspace(self, workspace_path: str) -> list[IndexedDocument]:
        """Return all documents belonging to workspace_path.

        Uses both exact workspace_path equality AND a file_path prefix match so
        that minor path variations (trailing separator, case differences between
        the stored workspace_path and the one supplied by the caller) never
        cause the purge to silently return an empty list.
        """
        async with self._conn.execute(
            "SELECT id, workspace_path, file_path, file_hash, char_count, chunk_count, indexed_at "
            "FROM documents "
            "WHERE workspace_path = ?1 OR file_path LIKE ?2 ESCAPE '\\' "
            "ORDER BY file_path ASC",
            (workspace_path, _like_prefix(workspace_path)),
        ) as cur:
            rows = await cur.fetchall()
        return [IndexedDocument(**dict(row)) for row in rows]

    async def delete_all_under_path(self, folder_path: str) -> int:
        """Bulk-delete every document whose file_path falls under folder_path.

        Acts as a safety net after the per-document purge loop in case a document
        was missed (e.g. a partial failure mid-loop left the row behind).
        Returns the number of rows deleted.
        """
        cursor = await self._conn.execute(
            "DELETE FROM documents "
            "WHERE workspace_path = ?1 OR file_path LIKE ?2 ESCAPE '\\'",
            (folder_path, _like_prefix(folder_path)),
        )
        await self._conn.commit()
        return cursor.rowcount or 0

    async def list_all(self, limit: int = 500, offset: int = 0) -> list[IndexedDocument]:
        async with self._conn.execute(
            "SELECT id, workspace_path, file_path, file_hash, char_count, chunk_count, indexed_at "
            "FROM documents ORDER BY indexed_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cur:
            rows = await cur.fetchall()
        return [IndexedDocument(**dict(row)) for row in rows]

    async def delete_by_path(self, file_path: str) -> None:
        await self._conn.execute("DELETE FROM documents WHERE file_path = ?", (file_path,))
        await self._conn.commit()

    async def update_path(self, old_path: str, new_path: str) -> None:
        """Update the stored file_path without touching any other record."""
        await self._conn.execute(
            "UPDATE documents SET file_path = ? WHERE file_path = ?",
            (new_path, old_path),
        )
        await self._conn.commit()
