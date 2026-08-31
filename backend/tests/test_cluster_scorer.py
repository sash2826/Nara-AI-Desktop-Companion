"""Unit tests for ClusterScorer.

Pure in-memory fakes — no database, no Qdrant required.
"""

from __future__ import annotations

import math

import pytest

from enterprise_ai_companion.capabilities.organisation.cluster_scorer import (
    ClusterScorer,
    _cosine_similarity,
    _overlap_coefficient,
)
from enterprise_ai_companion.capabilities.organisation.placement_ports import GraphScorePort


# ---------------------------------------------------------------------------
# Fake GraphScorePort
# ---------------------------------------------------------------------------

class _FakeGraphPort(GraphScorePort):
    def __init__(self, entities: dict[str, set[str]]) -> None:
        self._entities = entities

    async def get_canonicals_for_document(self, document_id: str) -> set[str]:
        return self._entities.get(document_id, set())

    async def get_canonicals_for_folder(self, folder_path: str) -> set[str]:
        return set()

    async def get_known_folder_paths(self) -> list[str]:
        return []


# ---------------------------------------------------------------------------
# _cosine_similarity — sync tests
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_identical_vectors_return_one(self) -> None:
        assert _cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self) -> None:
        assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors_return_minus_one(self) -> None:
        assert _cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_zero_vector_a_returns_zero(self) -> None:
        assert _cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

    def test_zero_vector_b_returns_zero(self) -> None:
        assert _cosine_similarity([1.0, 1.0], [0.0, 0.0]) == 0.0

    def test_general_case(self) -> None:
        a = [3.0, 4.0]
        b = [4.0, 3.0]
        expected = (12 + 12) / (5 * 5)
        assert _cosine_similarity(a, b) == pytest.approx(expected)

    def test_normalised_vectors_equal_dot_product(self) -> None:
        a = [1 / math.sqrt(2), 1 / math.sqrt(2)]
        b = [1.0, 0.0]
        assert _cosine_similarity(a, b) == pytest.approx(1 / math.sqrt(2))


# ---------------------------------------------------------------------------
# _overlap_coefficient — sync tests
# ---------------------------------------------------------------------------

class TestOverlapCoefficient:
    def test_identical_sets_return_one(self) -> None:
        s = frozenset({"alpha", "beta"})
        assert _overlap_coefficient(s, s) == pytest.approx(1.0)

    def test_disjoint_sets_return_zero(self) -> None:
        assert _overlap_coefficient(frozenset({"a"}), frozenset({"b"})) == 0.0

    def test_empty_set_a_returns_zero(self) -> None:
        assert _overlap_coefficient(frozenset(), frozenset({"a"})) == 0.0

    def test_empty_set_b_returns_zero(self) -> None:
        assert _overlap_coefficient(frozenset({"a"}), frozenset()) == 0.0

    def test_subset_returns_one(self) -> None:
        # Smaller set fully contained in larger → overlap = 1.0
        small = frozenset({"alpha"})
        large = frozenset({"alpha", "beta", "gamma"})
        assert _overlap_coefficient(small, large) == pytest.approx(1.0)

    def test_partial_overlap(self) -> None:
        a = frozenset({"alpha", "beta", "gamma"})
        b = frozenset({"beta", "gamma", "delta"})
        # intersection = {beta, gamma}, min(3, 3) = 3 → 2/3
        assert _overlap_coefficient(a, b) == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# ClusterScorer.compute_distance_matrix
# ---------------------------------------------------------------------------

class TestClusterScorer:

    @pytest.mark.asyncio
    async def test_empty_doc_list_returns_empty_matrix(self) -> None:
        scorer = ClusterScorer(_FakeGraphPort({}))
        result = await scorer.compute_distance_matrix([], {})
        assert result == []

    @pytest.mark.asyncio
    async def test_single_doc_returns_one_by_one_zero_matrix(self) -> None:
        scorer = ClusterScorer(_FakeGraphPort({"d1": {"alpha"}}))
        result = await scorer.compute_distance_matrix(["d1"], {"d1": [1.0, 0.0]})
        assert result == [[0.0]]

    @pytest.mark.asyncio
    async def test_identical_docs_have_zero_distance(self) -> None:
        entities = {"d1": {"alpha", "beta"}, "d2": {"alpha", "beta"}}
        vectors = {"d1": [1.0, 0.0], "d2": [1.0, 0.0]}
        scorer = ClusterScorer(_FakeGraphPort(entities))
        matrix = await scorer.compute_distance_matrix(["d1", "d2"], vectors)
        assert matrix[0][1] == pytest.approx(0.0)
        assert matrix[1][0] == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_disjoint_docs_have_distance_one(self) -> None:
        # No entity overlap, orthogonal vectors → combined_sim = 0 → distance = 1
        entities = {"d1": {"alpha"}, "d2": {"beta"}}
        vectors = {"d1": [1.0, 0.0], "d2": [0.0, 1.0]}
        scorer = ClusterScorer(_FakeGraphPort(entities))
        matrix = await scorer.compute_distance_matrix(["d1", "d2"], vectors)
        assert matrix[0][1] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_matrix_is_symmetric(self) -> None:
        entities = {"d1": {"alpha", "beta"}, "d2": {"beta", "gamma"}}
        vectors = {"d1": [0.6, 0.8], "d2": [0.8, 0.6]}
        scorer = ClusterScorer(_FakeGraphPort(entities))
        matrix = await scorer.compute_distance_matrix(["d1", "d2"], vectors)
        assert matrix[0][1] == pytest.approx(matrix[1][0])

    @pytest.mark.asyncio
    async def test_diagonal_is_zero(self) -> None:
        entities = {"d1": {"a"}, "d2": {"b"}, "d3": {"c"}}
        vectors = {"d1": [1.0, 0.0], "d2": [0.0, 1.0], "d3": [0.5, 0.5]}
        scorer = ClusterScorer(_FakeGraphPort(entities))
        matrix = await scorer.compute_distance_matrix(
            ["d1", "d2", "d3"], vectors
        )
        assert matrix[0][0] == 0.0
        assert matrix[1][1] == 0.0
        assert matrix[2][2] == 0.0

    @pytest.mark.asyncio
    async def test_entity_weight_and_cosine_weight_combine_correctly(self) -> None:
        # entity_overlap = 1.0 (identical sets), cosine_sim = 0.0 (orthogonal)
        # entity_weight=0.75 → similarity = 0.75 × 1.0 + 0.25 × 0.0 = 0.75
        # distance = 1 − 0.75 = 0.25
        entities = {"d1": {"alpha"}, "d2": {"alpha"}}
        vectors = {"d1": [1.0, 0.0], "d2": [0.0, 1.0]}
        scorer = ClusterScorer(_FakeGraphPort(entities), entity_weight=0.75)
        matrix = await scorer.compute_distance_matrix(["d1", "d2"], vectors)
        assert matrix[0][1] == pytest.approx(0.25)

    @pytest.mark.asyncio
    async def test_pure_cosine_weight_when_entity_weight_is_zero(self) -> None:
        # entity_weight=0 → distance depends only on cosine
        entities = {"d1": {"alpha"}, "d2": {"alpha"}}  # same entities, ignored
        vectors = {"d1": [1.0, 0.0], "d2": [0.0, 1.0]}  # orthogonal → cosine=0
        scorer = ClusterScorer(_FakeGraphPort(entities), entity_weight=0.0)
        matrix = await scorer.compute_distance_matrix(["d1", "d2"], vectors)
        assert matrix[0][1] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_missing_vector_treats_cosine_as_zero(self) -> None:
        # d2 has no vector — cosine contribution is 0
        # entity_overlap = 1.0 (same entities), weight=0.75
        # similarity = 0.75 × 1.0 + 0.25 × 0.0 = 0.75 → distance = 0.25
        entities = {"d1": {"alpha"}, "d2": {"alpha"}}
        vectors = {"d1": [1.0, 0.0]}  # d2 absent
        scorer = ClusterScorer(_FakeGraphPort(entities), entity_weight=0.75)
        matrix = await scorer.compute_distance_matrix(["d1", "d2"], vectors)
        assert matrix[0][1] == pytest.approx(0.25)

    @pytest.mark.asyncio
    async def test_distance_values_are_clamped_to_zero_one(self) -> None:
        # cosine_similarity can return negative values (anti-correlated vectors).
        # Distance = 1 − sim should be clamped to max(0, ...).
        entities: dict = {}
        vectors = {"d1": [1.0, 0.0], "d2": [-1.0, 0.0]}  # cosine = -1
        scorer = ClusterScorer(_FakeGraphPort(entities), entity_weight=0.0)
        matrix = await scorer.compute_distance_matrix(["d1", "d2"], vectors)
        assert matrix[0][1] >= 0.0  # must not go negative

    @pytest.mark.asyncio
    async def test_three_by_three_matrix_shape(self) -> None:
        ids = ["a", "b", "c"]
        entities = {d: set() for d in ids}
        vectors = {d: [1.0, 0.0] for d in ids}
        scorer = ClusterScorer(_FakeGraphPort(entities))
        matrix = await scorer.compute_distance_matrix(ids, vectors)
        assert len(matrix) == 3
        assert all(len(row) == 3 for row in matrix)

    def test_invalid_entity_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="entity_weight"):
            ClusterScorer(_FakeGraphPort({}), entity_weight=1.5)

    def test_entity_weight_zero_is_valid(self) -> None:
        ClusterScorer(_FakeGraphPort({}), entity_weight=0.0)  # no exception

    def test_entity_weight_one_is_valid(self) -> None:
        ClusterScorer(_FakeGraphPort({}), entity_weight=1.0)  # no exception
