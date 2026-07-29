"""Local embedding service using BGE-M3 via fastembed (ONNX runtime)."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastembed import TextEmbedding

# BGE-M3 produces 1024-dimensional embeddings.
EMBEDDING_DIM = 1024
MODEL_NAME = "BAAI/bge-m3"


class EmbeddingService:
    """Generates dense text embeddings using BGE-M3 locally via ONNX runtime.

    The model is loaded once on first use (lazy singleton per instance).
    Subsequent calls reuse the loaded model — no repeated disk I/O.

    Thread safety: model initialisation is protected by a lock so concurrent
    calls do not double-load.
    """

    def __init__(self) -> None:
        self._model: TextEmbedding | None = None
        self._lock = threading.Lock()

    def _get_model(self) -> TextEmbedding:
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from fastembed import TextEmbedding

                    self._model = TextEmbedding(model_name=MODEL_NAME)
        return self._model

    def generate(self, text: str) -> list[float]:
        """Return a single embedding vector for the given text.

        Args:
            text: The input string to embed.

        Returns:
            A list of floats with length EMBEDDING_DIM (1024 for BGE-M3).
        """
        if not text:
            raise ValueError("text must be a non-empty string")

        model = self._get_model()
        embeddings = list(model.embed([text]))
        return embeddings[0].tolist()

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a list of texts.

        Args:
            texts: A non-empty list of input strings.

        Returns:
            A list of embedding vectors in the same order as the input.
        """
        if not texts:
            raise ValueError("texts must be a non-empty list")
        if any(not t for t in texts):
            raise ValueError("all texts must be non-empty strings")

        model = self._get_model()
        return [e.tolist() for e in model.embed(texts)]
