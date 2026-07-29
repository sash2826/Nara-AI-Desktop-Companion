"""Unit tests for EmbeddingService.

These tests load the real BGE-M3 model via fastembed. The model is downloaded
on first run (~500 MB) and cached locally by fastembed. Subsequent runs are fast.

Shape validation and determinism are the primary assertions — we do not test
the semantic quality of the embeddings.
"""

import pytest

from enterprise_ai_companion.capabilities.indexing.embedding_service import (
    EMBEDDING_DIM,
    EmbeddingService,
)


@pytest.fixture(scope="module")
def service() -> EmbeddingService:
    """Module-scoped fixture so the model is loaded once for all tests."""
    return EmbeddingService()


class TestGenerate:
    def test_returns_correct_dimension(self, service: EmbeddingService) -> None:
        vector = service.generate("hello world")
        assert len(vector) == EMBEDDING_DIM

    def test_returns_list_of_floats(self, service: EmbeddingService) -> None:
        vector = service.generate("enterprise AI")
        assert isinstance(vector, list)
        assert all(isinstance(v, float) for v in vector)

    def test_deterministic(self, service: EmbeddingService) -> None:
        text = "determinism check"
        first = service.generate(text)
        second = service.generate(text)
        assert first == second

    def test_different_texts_produce_different_vectors(self, service: EmbeddingService) -> None:
        v1 = service.generate("apple")
        v2 = service.generate("submarine")
        assert v1 != v2

    def test_rejects_empty_string(self, service: EmbeddingService) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            service.generate("")


class TestGenerateBatch:
    def test_batch_returns_correct_count(self, service: EmbeddingService) -> None:
        texts = ["first", "second", "third"]
        result = service.generate_batch(texts)
        assert len(result) == len(texts)

    def test_batch_each_vector_correct_dimension(self, service: EmbeddingService) -> None:
        result = service.generate_batch(["alpha", "beta"])
        assert all(len(v) == EMBEDDING_DIM for v in result)

    def test_batch_consistent_with_single(self, service: EmbeddingService) -> None:
        text = "consistency test"
        single = service.generate(text)
        batch = service.generate_batch([text])
        assert single == batch[0]

    def test_batch_rejects_empty_list(self, service: EmbeddingService) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            service.generate_batch([])

    def test_batch_rejects_empty_string_in_list(self, service: EmbeddingService) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            service.generate_batch(["valid", ""])
