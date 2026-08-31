"""Document-level vector retrieval for the clustering pipeline.

Qdrant stores one vector per chunk; this service aggregates chunk vectors
into a single document vector via average pooling so the clustering engine
can operate on document-level representations.
"""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import TYPE_CHECKING

from qdrant_client.models import FieldCondition, Filter, MatchValue

from enterprise_ai_companion.infrastructure.qdrant_provider import CHUNKS_COLLECTION

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

_CHUNKS_PER_PAGE = 200


class DocumentVectorService:
    """Retrieves document-level embedding vectors from Qdrant.

    Chunks are stored per-document in Qdrant. This service aggregates chunk
    vectors into a single document vector via average pooling, suitable for
    cosine-distance-based agglomerative clustering.

    Documents with no indexed chunks are silently omitted from the result.
    """

    def __init__(self, qdrant_client: "QdrantClient") -> None:
        self._qdrant = qdrant_client

    async def get_vectors(self, doc_ids: list[str]) -> dict[str, list[float]]:
        """Return a document_id → averaged vector mapping.

        Args:
            doc_ids: Document IDs whose vectors are needed. Duplicates are
                     deduplicated before querying Qdrant.

        Returns:
            Mapping of document_id to its average-pooled chunk vector.
            Documents with no Qdrant data are absent from the result.
        """
        if not doc_ids:
            return {}

        unique_ids = list(dict.fromkeys(doc_ids))  # deduplicate, preserve order
        result: dict[str, list[float]] = {}
        loop = asyncio.get_running_loop()

        for doc_id in unique_ids:
            chunk_vectors = await loop.run_in_executor(
                None,
                functools.partial(self._fetch_chunk_vectors, doc_id),
            )
            if chunk_vectors:
                result[doc_id] = _average_pool(chunk_vectors)
            else:
                logger.debug("[VECTOR] No Qdrant vectors found for document %s", doc_id)

        logger.debug(
            "[VECTOR] Retrieved vectors for %d/%d document(s)",
            len(result),
            len(unique_ids),
        )
        return result

    def _fetch_chunk_vectors(self, doc_id: str) -> list[list[float]]:
        """Synchronous helper — must be called via run_in_executor.

        Scrolls all Qdrant points for this document, collecting their vectors.
        Paginates until the collection is exhausted or no more points are returned.
        """
        doc_filter = Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=doc_id))]
        )
        vectors: list[list[float]] = []
        offset = None

        while True:
            points, next_offset = self._qdrant.scroll(
                CHUNKS_COLLECTION,
                scroll_filter=doc_filter,
                with_vectors=True,
                limit=_CHUNKS_PER_PAGE,
                offset=offset,
            )
            for point in points:
                if isinstance(point.vector, list) and point.vector:
                    vectors.append(point.vector)

            if next_offset is None:
                break
            offset = next_offset

        return vectors


def _average_pool(vectors: list[list[float]]) -> list[float]:
    """Return the component-wise mean of a non-empty list of equal-length vectors."""
    dim = len(vectors[0])
    result = [0.0] * dim
    for vec in vectors:
        for i, v in enumerate(vec):
            result[i] += v
    n = len(vectors)
    return [x / n for x in result]
