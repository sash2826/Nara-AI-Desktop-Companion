"""Repository for document chunks stored in SQLite and Qdrant."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import aiosqlite
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from enterprise_ai_companion.infrastructure.qdrant_provider import CHUNKS_COLLECTION

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    chunk_index: int
    content: str
    char_start: int
    char_end: int


class ChunkRepository:
    def __init__(self, conn: aiosqlite.Connection, qdrant_client: QdrantClient) -> None:
        self._conn = conn
        self._qdrant = qdrant_client

    async def save_batch(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        """Persist chunks to SQLite (for content retrieval) and Qdrant (for vector search).

        Both stores are populated atomically from the caller's perspective — SQLite
        first, then Qdrant. A partial failure leaves SQLite rows without vectors, which
        is tolerable; the indexer will re-index the document on the next run.
        """
        if not chunks:
            return

        await self._conn.executemany(
            """
            INSERT INTO chunks (id, document_id, chunk_index, content, char_start, char_end)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                content     = excluded.content,
                char_start  = excluded.char_start,
                char_end    = excluded.char_end
            """,
            [
                (c.id, c.document_id, c.chunk_index, c.content, c.char_start, c.char_end)
                for c in chunks
            ],
        )
        # FTS5 mirror — delete stale rows first to avoid duplicates on re-index.
        chunk_ids = [c.id for c in chunks]
        placeholders = ",".join("?" * len(chunk_ids))
        await self._conn.execute(
            f"DELETE FROM chunks_fts WHERE chunk_id IN ({placeholders})", chunk_ids
        )
        await self._conn.executemany(
            "INSERT INTO chunks_fts (content, chunk_id) VALUES (?, ?)",
            [(c.content, c.id) for c in chunks],
        )
        await self._conn.commit()

        # Upsert vectors into Qdrant with file_path and chunk_index in the payload
        # so searches can filter by workspace and retrieve document context.
        points = [
            PointStruct(
                id=_chunk_id_to_qdrant_id(chunk.id),
                vector=embedding,
                payload={
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        self._qdrant.upsert(collection_name=CHUNKS_COLLECTION, points=points)
        logger.debug("Saved %d chunks to SQLite and Qdrant.", len(chunks))

    async def delete_by_document(self, document_id: str) -> None:
        """Remove all chunks for a document from SQLite and Qdrant."""
        async with self._conn.execute(
            "SELECT id FROM chunks WHERE document_id = ?", (document_id,)
        ) as cur:
            rows = await cur.fetchall()

        if not rows:
            return

        chunk_ids = [row[0] for row in rows]
        qdrant_ids = [_chunk_id_to_qdrant_id(cid) for cid in chunk_ids]

        await self._conn.execute(
            "DELETE FROM chunks WHERE document_id = ?", (document_id,)
        )
        placeholders = ",".join("?" * len(chunk_ids))
        await self._conn.execute(
            f"DELETE FROM chunks_fts WHERE chunk_id IN ({placeholders})", chunk_ids
        )
        await self._conn.commit()

        self._qdrant.delete(
            collection_name=CHUNKS_COLLECTION,
            points_selector=qdrant_ids,
        )

    async def get_by_ids(self, chunk_ids: list[str]) -> list[Chunk]:
        """Fetch chunks by their string IDs (used to hydrate Qdrant search results)."""
        if not chunk_ids:
            return []
        placeholders = ",".join("?" * len(chunk_ids))
        async with self._conn.execute(
            f"SELECT id, document_id, chunk_index, content, char_start, char_end "
            f"FROM chunks WHERE id IN ({placeholders})",
            chunk_ids,
        ) as cur:
            rows = await cur.fetchall()
        return [Chunk(**dict(row)) for row in rows]


def _chunk_id_to_qdrant_id(chunk_id: str) -> int:
    """Convert a string chunk ID to a stable integer Qdrant point ID via hash."""
    return abs(hash(chunk_id)) % (2**53)
