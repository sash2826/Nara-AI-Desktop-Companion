"""Unit tests for DocumentVectorService.

All tests use an in-memory FakeQdrantClient — no real Qdrant process required.
The fake implements only the subset of the QdrantClient interface used by
DocumentVectorService: scroll().
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from enterprise_ai_companion.capabilities.organisation.document_vector_service import (
    DocumentVectorService,
    _average_pool,
)


# ---------------------------------------------------------------------------
# Fake Qdrant client
# ---------------------------------------------------------------------------

class _FakeQdrantClient:
    """Minimal Qdrant scroll stub keyed by document_id payload field."""

    def __init__(self, data: dict[str, list[list[float]]]) -> None:
        # data: {doc_id: [vector, vector, ...]}
        self._data = data

    def scroll(
        self,
        collection_name: str,
        *,
        scroll_filter=None,
        with_vectors: bool = False,
        limit: int = 10,
        offset=None,
    ):
        doc_id = scroll_filter.must[0].match.value
        vectors = self._data.get(doc_id, [])
        points = [SimpleNamespace(vector=v) for v in vectors]
        return (points, None)  # no pagination needed in unit tests


# ---------------------------------------------------------------------------
# _average_pool (pure function — sync tests)
# ---------------------------------------------------------------------------

class TestAveragePool:
    def test_single_vector_is_returned_unchanged(self) -> None:
        assert _average_pool([[1.0, 2.0, 3.0]]) == [1.0, 2.0, 3.0]

    def test_two_vectors_are_averaged(self) -> None:
        result = _average_pool([[1.0, 0.0], [0.0, 1.0]])
        assert result == pytest.approx([0.5, 0.5])

    def test_three_vectors_are_averaged(self) -> None:
        result = _average_pool([[3.0, 0.0], [0.0, 3.0], [0.0, 0.0]])
        assert result == pytest.approx([1.0, 1.0])

    def test_preserves_vector_dimension(self) -> None:
        vecs = [[float(i)] * 384 for i in range(5)]
        result = _average_pool(vecs)
        assert len(result) == 384


# ---------------------------------------------------------------------------
# DocumentVectorService.get_vectors
# ---------------------------------------------------------------------------

class TestGetVectors:

    @pytest.mark.asyncio
    async def test_empty_input_returns_empty_dict(self) -> None:
        svc = DocumentVectorService(_FakeQdrantClient({}))
        result = await svc.get_vectors([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_doc_with_no_chunks_is_omitted(self) -> None:
        svc = DocumentVectorService(_FakeQdrantClient({}))
        result = await svc.get_vectors(["doc-missing"])
        assert "doc-missing" not in result

    @pytest.mark.asyncio
    async def test_single_chunk_doc_returns_that_vector(self) -> None:
        vec = [0.1, 0.2, 0.3]
        svc = DocumentVectorService(_FakeQdrantClient({"doc-1": [vec]}))
        result = await svc.get_vectors(["doc-1"])
        assert result["doc-1"] == pytest.approx(vec)

    @pytest.mark.asyncio
    async def test_multi_chunk_doc_is_average_pooled(self) -> None:
        svc = DocumentVectorService(_FakeQdrantClient({
            "doc-1": [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
        }))
        result = await svc.get_vectors(["doc-1"])
        assert result["doc-1"] == pytest.approx([2 / 3, 2 / 3], abs=1e-6)

    @pytest.mark.asyncio
    async def test_multiple_documents_returned_independently(self) -> None:
        svc = DocumentVectorService(_FakeQdrantClient({
            "doc-a": [[1.0, 0.0]],
            "doc-b": [[0.0, 1.0]],
        }))
        result = await svc.get_vectors(["doc-a", "doc-b"])
        assert result["doc-a"] == pytest.approx([1.0, 0.0])
        assert result["doc-b"] == pytest.approx([0.0, 1.0])

    @pytest.mark.asyncio
    async def test_mix_of_present_and_absent_docs(self) -> None:
        svc = DocumentVectorService(_FakeQdrantClient({
            "doc-present": [[0.5, 0.5]],
        }))
        result = await svc.get_vectors(["doc-present", "doc-absent"])
        assert "doc-present" in result
        assert "doc-absent" not in result

    @pytest.mark.asyncio
    async def test_duplicate_doc_ids_are_deduplicated(self) -> None:
        call_count = {"n": 0}
        original_data = {"doc-1": [[1.0, 0.0]]}

        class _CountingClient(_FakeQdrantClient):
            def scroll(self, *args, **kwargs):
                call_count["n"] += 1
                return super().scroll(*args, **kwargs)

        svc = DocumentVectorService(_CountingClient(original_data))
        result = await svc.get_vectors(["doc-1", "doc-1", "doc-1"])
        assert "doc-1" in result
        assert call_count["n"] == 1  # Qdrant queried exactly once

    @pytest.mark.asyncio
    async def test_returned_vectors_have_correct_dimension(self) -> None:
        vec = [float(i) / 384 for i in range(384)]
        svc = DocumentVectorService(_FakeQdrantClient({"doc-1": [vec]}))
        result = await svc.get_vectors(["doc-1"])
        assert len(result["doc-1"]) == 384

    @pytest.mark.asyncio
    async def test_average_pool_produces_unit_range_values(self) -> None:
        """Averaged vector components must not exceed the range of inputs."""
        vecs = [[0.8, 0.2], [0.4, 0.6]]
        svc = DocumentVectorService(_FakeQdrantClient({"doc-1": vecs}))
        result = await svc.get_vectors(["doc-1"])
        for val in result["doc-1"]:
            assert 0.0 <= val <= 1.0
