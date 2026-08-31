"""Unit tests for ClusterEngine.

Pure computation — no database, no Qdrant, no async required.
Tests construct explicit distance matrices and assert on the resulting clusters.
"""

from __future__ import annotations

import pytest

from enterprise_ai_companion.capabilities.organisation.cluster_engine import (
    ClusterEngine,
)


def _zero_matrix(n: int) -> list[list[float]]:
    """N×N matrix of zeros (all docs identical — distance 0)."""
    return [[0.0] * n for _ in range(n)]


def _identity_distance(n: int) -> list[list[float]]:
    """N×N matrix where distance between any two different docs is 1.0."""
    m = [[1.0] * n for _ in range(n)]
    for i in range(n):
        m[i][i] = 0.0
    return m


def _two_doc_matrix(dist: float) -> list[list[float]]:
    return [[0.0, dist], [dist, 0.0]]


def _three_doc_matrix(d01: float, d02: float, d12: float) -> list[list[float]]:
    return [
        [0.0, d01, d02],
        [d01, 0.0, d12],
        [d02, d12, 0.0],
    ]


class TestClusterEngineConstruction:
    def test_valid_construction(self) -> None:
        e = ClusterEngine(distance_threshold=0.5, min_cluster_size=2)
        assert e is not None

    def test_invalid_threshold_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="distance_threshold"):
            ClusterEngine(distance_threshold=0.0)

    def test_invalid_threshold_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="distance_threshold"):
            ClusterEngine(distance_threshold=1.5)

    def test_threshold_exactly_one_is_valid(self) -> None:
        ClusterEngine(distance_threshold=1.0)  # no exception

    def test_min_cluster_size_one_raises(self) -> None:
        with pytest.raises(ValueError, match="min_cluster_size"):
            ClusterEngine(min_cluster_size=1)

    def test_min_cluster_size_two_is_valid(self) -> None:
        ClusterEngine(min_cluster_size=2)  # no exception


class TestClusterEngineEdgeCases:
    def test_empty_doc_list_returns_empty(self) -> None:
        engine = ClusterEngine()
        assert engine.cluster([], []) == []

    def test_single_doc_returns_empty(self) -> None:
        engine = ClusterEngine()
        result = engine.cluster(["d1"], [[0.0]])
        assert result == []

    def test_two_identical_docs_form_one_cluster(self) -> None:
        engine = ClusterEngine(distance_threshold=0.5)
        result = engine.cluster(["d1", "d2"], _two_doc_matrix(0.0))
        assert len(result) == 1
        assert set(result[0]) == {"d1", "d2"}

    def test_two_far_docs_produce_no_clusters(self) -> None:
        """Distance > threshold → two singletons → filtered out."""
        engine = ClusterEngine(distance_threshold=0.3)
        result = engine.cluster(["d1", "d2"], _two_doc_matrix(0.9))
        assert result == []

    def test_two_docs_exactly_at_threshold_are_merged(self) -> None:
        """fcluster with criterion='distance' merges when dist <= threshold."""
        engine = ClusterEngine(distance_threshold=0.5)
        result = engine.cluster(["d1", "d2"], _two_doc_matrix(0.5))
        assert len(result) == 1

    def test_two_docs_just_above_threshold_are_not_merged(self) -> None:
        engine = ClusterEngine(distance_threshold=0.5)
        result = engine.cluster(["d1", "d2"], _two_doc_matrix(0.51))
        assert result == []


class TestClusterEngineGrouping:
    def test_three_docs_two_close_one_far(self) -> None:
        """d1 and d2 are close; d3 is far from both → one cluster {d1, d2}."""
        matrix = _three_doc_matrix(d01=0.1, d02=0.9, d12=0.9)
        engine = ClusterEngine(distance_threshold=0.5)
        result = engine.cluster(["d1", "d2", "d3"], matrix)
        assert len(result) == 1
        assert set(result[0]) == {"d1", "d2"}

    def test_three_docs_all_close_form_one_cluster(self) -> None:
        matrix = _three_doc_matrix(d01=0.1, d02=0.1, d12=0.1)
        engine = ClusterEngine(distance_threshold=0.5)
        result = engine.cluster(["d1", "d2", "d3"], matrix)
        assert len(result) == 1
        assert set(result[0]) == {"d1", "d2", "d3"}

    def test_four_docs_two_pairs_become_two_clusters(self) -> None:
        """Two tight pairs far from each other → two clusters."""
        #   d1-d2 close, d3-d4 close, but inter-pair distance is large.
        dist = [
            [0.0, 0.1, 0.9, 0.9],
            [0.1, 0.0, 0.9, 0.9],
            [0.9, 0.9, 0.0, 0.1],
            [0.9, 0.9, 0.1, 0.0],
        ]
        engine = ClusterEngine(distance_threshold=0.5)
        result = engine.cluster(["d1", "d2", "d3", "d4"], dist)
        assert len(result) == 2
        cluster_sets = [set(c) for c in result]
        assert {"d1", "d2"} in cluster_sets
        assert {"d3", "d4"} in cluster_sets

    def test_all_identical_docs_form_one_large_cluster(self) -> None:
        ids = ["a", "b", "c", "d", "e"]
        engine = ClusterEngine(distance_threshold=0.5)
        result = engine.cluster(ids, _zero_matrix(5))
        assert len(result) == 1
        assert set(result[0]) == set(ids)

    def test_all_distant_docs_return_no_clusters(self) -> None:
        ids = ["a", "b", "c"]
        engine = ClusterEngine(distance_threshold=0.1)
        result = engine.cluster(ids, _identity_distance(3))
        assert result == []


class TestClusterEngineMinSize:
    def test_singleton_clusters_always_filtered(self) -> None:
        """Even with min_cluster_size=2, singletons must be gone."""
        dist = [
            [0.0, 0.9, 0.9],
            [0.9, 0.0, 0.1],
            [0.9, 0.1, 0.0],
        ]
        engine = ClusterEngine(distance_threshold=0.5, min_cluster_size=2)
        result = engine.cluster(["d1", "d2", "d3"], dist)
        assert len(result) == 1
        assert set(result[0]) == {"d2", "d3"}
        for cluster in result:
            assert len(cluster) >= 2

    def test_min_cluster_size_three_filters_pairs(self) -> None:
        """With min_size=3, a pair cluster is suppressed."""
        dist = _three_doc_matrix(d01=0.1, d02=0.9, d12=0.9)
        engine = ClusterEngine(distance_threshold=0.5, min_cluster_size=3)
        result = engine.cluster(["d1", "d2", "d3"], dist)
        assert result == []

    def test_min_cluster_size_three_passes_large_cluster(self) -> None:
        dist = _three_doc_matrix(d01=0.1, d02=0.1, d12=0.1)
        engine = ClusterEngine(distance_threshold=0.5, min_cluster_size=3)
        result = engine.cluster(["d1", "d2", "d3"], dist)
        assert len(result) == 1
        assert set(result[0]) == {"d1", "d2", "d3"}


class TestClusterEngineThreshold:
    def test_lower_threshold_produces_fewer_clusters(self) -> None:
        """Tighter threshold → only very close pairs merge."""
        dist = _three_doc_matrix(d01=0.2, d02=0.4, d12=0.4)
        engine_tight = ClusterEngine(distance_threshold=0.15)
        engine_loose = ClusterEngine(distance_threshold=0.45)
        result_tight = engine_tight.cluster(["d1", "d2", "d3"], dist)
        result_loose = engine_loose.cluster(["d1", "d2", "d3"], dist)
        # Tight: no pairs below 0.15 → no clusters
        # Loose: d01=0.2 < 0.45 → at least {d1, d2}
        assert len(result_tight) <= len(result_loose)

    def test_threshold_one_merges_everything(self) -> None:
        """threshold=1.0 means merge until all are in one group."""
        ids = ["a", "b", "c", "d"]
        engine = ClusterEngine(distance_threshold=1.0)
        result = engine.cluster(ids, _identity_distance(4))
        assert len(result) == 1
        assert set(result[0]) == set(ids)
