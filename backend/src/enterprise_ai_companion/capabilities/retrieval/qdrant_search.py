"""Semantic vector search provider backed by Qdrant."""

from __future__ import annotations

import logging

import aiosqlite
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from enterprise_ai_companion.capabilities.indexing.chunk_repository import ChunkRepository
from enterprise_ai_companion.capabilities.indexing.document_repository import DocumentRepository
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.retrieval.search_models import SearchResult
from enterprise_ai_companion.infrastructure.qdrant_provider import CHUNKS_COLLECTION

logger = logging.getLogger(__name__)


class QdrantSearchProvider:
    """Embeds a query with BGE-M3 and retrieves the nearest document chunks from Qdrant.

    After vector retrieval, chunk content and document metadata are hydrated from
    SQLite so callers receive fully populated SearchResult objects.
    """

    def __init__(
        self,
        conn: aiosqlite.Connection,
        qdrant_client: QdrantClient,
        embedding_service: EmbeddingService,
    ) -> None:
        self._chunk_repo = ChunkRepository(conn, qdrant_client)
        self._doc_repo = DocumentRepository(conn)
        self._qdrant = qdrant_client
        self._embedding_service = embedding_service

    async def search(
        self,
        query: str,
        top_k: int = 5,
        workspace_path: str | None = None,
    ) -> list[SearchResult]:
        """Return top_k chunks most semantically similar to query.

        Args:
            query: Natural-language query string.
            top_k: Maximum number of results to return.
            workspace_path: Optional workspace filter — only chunks whose parent
                document belongs to this workspace are returned.
        """
        if not query.strip():
            return []

        query_vector = self._embedding_service.generate(query)

        qdrant_filter: Filter | None = None
        if workspace_path:
            # Qdrant payload filter requires workspace_path stored per-point.
            # We filter post-hoc via document lookup since workspace_path lives in SQLite.
            pass

        hits = self._qdrant.search(
            collection_name=CHUNKS_COLLECTION,
            query_vector=query_vector,
            limit=top_k * 2 if workspace_path else top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        if not hits:
            return []

        chunk_ids = [str(hit.payload["chunk_id"]) for hit in hits if hit.payload]
        score_by_chunk_id = {
            str(hit.payload["chunk_id"]): hit.score
            for hit in hits
            if hit.payload
        }

        chunks = await self._chunk_repo.get_by_ids(chunk_ids)

        results: list[SearchResult] = []
        for chunk in chunks:
            doc = await self._doc_repo.get_by_path(
                await self._get_file_path_for_document(chunk.document_id)
            )
            if doc is None:
                continue
            if workspace_path and doc.workspace_path != workspace_path:
                continue
            results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_path=doc.file_path,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=score_by_chunk_id.get(chunk.id, 0.0),
                )
            )
            if len(results) >= top_k:
                break

        results.sort(key=lambda r: r.score, reverse=True)
        return results

    async def _get_file_path_for_document(self, document_id: str) -> str:
        """Look up the file_path for a document_id from SQLite."""
        async with self._chunk_repo._conn.execute(
            "SELECT file_path FROM documents WHERE id = ?", (document_id,)
        ) as cur:
            row = await cur.fetchone()
        return str(row[0]) if row else ""
