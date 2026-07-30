"""Local Qdrant vector store provider for the Enterprise AI Companion.

Uses QdrantClient in local file-based mode — no Docker or network service required.
The collection is created automatically on first initialisation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

logger = logging.getLogger(__name__)

CHUNKS_COLLECTION = "document_chunks"
EMBEDDING_DIM = 1024  # BGE-M3 output dimension


def _qdrant_data_dir() -> Path:
    env = os.environ.get("EAC_QDRANT_PATH")
    if env:
        return Path(env)
    # Default: repo root / qdrant_data
    return Path(__file__).parents[4] / "qdrant_data"


class QdrantProvider:
    """Manages the lifecycle of a local Qdrant client and the document_chunks collection."""

    def __init__(self) -> None:
        self._client: QdrantClient | None = None

    def initialize(self) -> None:
        """Open the local Qdrant store and ensure the collection exists."""
        data_dir = _qdrant_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)

        self._client = QdrantClient(path=str(data_dir))
        logger.info("Qdrant provider initialised at %s", data_dir)

        existing = {c.name for c in self._client.get_collections().collections}
        if CHUNKS_COLLECTION not in existing:
            self._client.create_collection(
                collection_name=CHUNKS_COLLECTION,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection '%s'", CHUNKS_COLLECTION)

    def get_client(self) -> QdrantClient:
        if self._client is None:
            raise RuntimeError("QdrantProvider.initialize() must be called before get_client().")
        return self._client

    def health(self) -> bool:
        """Return True if the client is initialised and the collection is reachable."""
        if self._client is None:
            return False
        try:
            self._client.get_collection(CHUNKS_COLLECTION)
            return True
        except Exception:
            return False

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("Qdrant provider closed.")
