"""Repository for indexed document metadata stored in SQLite."""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite


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
                id             = excluded.id,
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
        async with self._conn.execute(
            "SELECT id, workspace_path, file_path, file_hash, char_count, chunk_count, indexed_at "
            "FROM documents WHERE workspace_path = ? ORDER BY file_path ASC",
            (workspace_path,),
        ) as cur:
            rows = await cur.fetchall()
        return [IndexedDocument(**dict(row)) for row in rows]

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
