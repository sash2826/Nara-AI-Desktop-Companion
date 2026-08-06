"""Tracks the last successful knowledge graph build per document.

Allows FileIndexer to skip the (expensive) LLM-based graph build when a
document's content has not changed since the previous index run — the same
hash-based deduplication pattern used by DocumentRepository for chunks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import aiosqlite


@dataclass(frozen=True)
class GraphState:
    document_id: str
    file_hash: str
    built_at: str


class GraphStateRepository:
    """SQLite-backed store for per-document graph build state."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get_by_document(self, document_id: str) -> GraphState | None:
        """Return the stored graph state for document_id, or None if not found."""
        async with self._conn.execute(
            "SELECT document_id, file_hash, built_at FROM graph_state WHERE document_id = ?",
            (document_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None
        return GraphState(document_id=row[0], file_hash=row[1], built_at=row[2])

    async def save(self, document_id: str, file_hash: str) -> None:
        """Insert or replace the graph state for document_id."""
        built_at = datetime.now(UTC).isoformat()
        await self._conn.execute(
            "INSERT OR REPLACE INTO graph_state (document_id, file_hash, built_at) "
            "VALUES (?, ?, ?)",
            (document_id, file_hash, built_at),
        )
        await self._conn.commit()

    async def delete_by_document(self, document_id: str) -> None:
        """Remove the graph state entry for document_id."""
        await self._conn.execute(
            "DELETE FROM graph_state WHERE document_id = ?",
            (document_id,),
        )
        await self._conn.commit()
