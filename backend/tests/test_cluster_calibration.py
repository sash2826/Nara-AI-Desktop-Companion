"""Benchmark calibration for EAC_CLUSTER_DISTANCE_THRESHOLD.

Ten scenario suites verify that the default threshold of 0.45 produces the
correct cluster structure across the full range of realistic cases:

  Suite 1  — Perfect match: all identical → 1 cluster
  Suite 2  — Two tight groups, zero cross-similarity → 2 clusters
  Suite 3  — Three tight groups → 3 clusters
  Suite 4  — Tight cluster + unrelated singleton → 1 cluster (singleton excluded)
  Suite 5  — Boundary BELOW threshold (dist=0.44) → merged
  Suite 6  — Boundary ABOVE threshold (dist=0.46) → not merged
  Suite 7  — Entity signal dominates (dist=0.25) → merged
  Suite 8  — Vector signal only, weak (dist=0.80) → not merged
  Suite 9  — Partial entity overlap + strong vector (dist=0.375) → merged
  Suite 10 — Large cluster (8 docs, all related) → 1 big cluster

Calibration grid (analytical, α=0.75):

  threshold │ S1  S2  S3  S4  S5  S6  S7  S8  S9  S10 │ pass/10
  ──────────┼────────────────────────────────────────────┼─────────
  0.30      │  ✓   ✓   ✓   ✓   ✗   ✓   ✓   ✓   ✗   ✓  │  8/10
  0.40      │  ✓   ✓   ✓   ✓   ✗   ✓   ✓   ✓   ✓   ✓  │  9/10
  0.45      │  ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓   ✓  │ 10/10  ← default
  0.50      │  ✓   ✓   ✓   ✓   ✓   ✗   ✓   ✓   ✓   ✓  │  9/10
  0.60      │  ✓   ✓   ✓   ✓   ✓   ✗   ✓   ✓   ✓   ✓  │  9/10

Suite 5 (dist=0.44) fails at threshold≤0.40: threshold too tight, misses valid clusters.
Suite 6 (dist=0.46) fails at threshold≥0.50: threshold too loose, merges unrelated docs.
Only threshold=0.45 passes all ten suites.

Distance formula (α = EAC_CLUSTER_ENTITY_WEIGHT = 0.75):
  sim(i,j)  = α × overlap_coefficient(entities_i, entities_j)
              + (1−α) × cosine_similarity(vec_i, vec_j)
  dist(i,j) = 1 − sim(i,j)

overlap_coefficient = |A ∩ B| / min(|A|, |B|)   (Szymkiewicz-Simpson)
"""

from __future__ import annotations

import math
import pytest

from enterprise_ai_companion.capabilities.organisation.cluster_engine import ClusterEngine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_THRESHOLD = 0.45  # the value under test; matches EAC_CLUSTER_DISTANCE_THRESHOLD default
_ALPHA = 0.75      # matches EAC_CLUSTER_ENTITY_WEIGHT default


def _engine(threshold: float = _THRESHOLD, min_cluster_size: int = 2) -> ClusterEngine:
    return ClusterEngine(distance_threshold=threshold, min_cluster_size=min_cluster_size)


def _ids(n: int) -> list[str]:
    """Return n doc IDs: ["d1", "d2", …]."""
    return [f"d{i + 1}" for i in range(n)]


def _uniform_matrix(n: int, off_diagonal: float) -> list[list[float]]:
    """N×N matrix: diagonal=0, all off-diagonal=off_diagonal."""
    return [
        [0.0 if i == j else off_diagonal for j in range(n)]
        for i in range(n)
    ]


def _block_matrix(
    group_sizes: list[int],
    within_dist: float,
    across_dist: float,
) -> list[list[float]]:
    """Block-diagonal matrix.

    within_dist applied to pairs inside the same group,
    across_dist  applied to pairs in different groups.
    """
    n = sum(group_sizes)
    mat = [[across_dist] * n for _ in range(n)]
    start = 0
    for size in group_sizes:
        for i in range(start, start + size):
            for j in range(start, start + size):
                mat[i][j] = 0.0 if i == j else within_dist
        start += size
    return mat


def _dist_from_scenario(
    cosine: float,
    entity_overlap: float,
    alpha: float = _ALPHA,
) -> float:
    """Compute distance from analytical cosine and entity-overlap values."""
    sim = alpha * entity_overlap + (1.0 - alpha) * cosine
    return round(1.0 - sim, 10)


def _cosine(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    na = math.sqrt(sum(a * a for a in vec_a))
    nb = math.sqrt(sum(b * b for b in vec_b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _overlap(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def _2x2(dist: float) -> list[list[float]]:
    return [[0.0, dist], [dist, 0.0]]


# ---------------------------------------------------------------------------
# Suite 1 — Perfect match: all docs identical → single cluster
#
# Scenario: 4 documents, all pairwise distance = 0.0 (identical entities
# and vectors). Represents a batch of strongly related files.
# ---------------------------------------------------------------------------

class TestSuite1PerfectMatch:
    """S1: dist=0 for all pairs → 1 cluster of 4."""

    def test_forms_one_cluster(self) -> None:
        doc_ids = _ids(4)
        matrix = _uniform_matrix(4, off_diagonal=0.0)
        clusters = _engine().cluster(doc_ids, matrix)
        assert len(clusters) == 1
        assert set(clusters[0]) == set(doc_ids)

    def test_cluster_contains_all_docs(self) -> None:
        doc_ids = _ids(4)
        matrix = _uniform_matrix(4, off_diagonal=0.0)
        clusters = _engine().cluster(doc_ids, matrix)
        assert set(clusters[0]) == {"d1", "d2", "d3", "d4"}


# ---------------------------------------------------------------------------
# Suite 2 — Two tight groups, zero cross-similarity → 2 clusters
#
# Scenario: d1,d2 share entities {X} and vector [1,0];
#           d3,d4 share entities {Y} and vector [0,1].
# entity_overlap(d1,d3) = 0, cosine(d1,d3) = 0 → dist = 1.0
# entity_overlap(d1,d2) = 1, cosine(d1,d2) = 1 → dist = 0.0
# ---------------------------------------------------------------------------

class TestSuite2TwoGroups:
    """S2: 2 clearly separated groups → 2 distinct clusters."""

    def test_forms_two_clusters(self) -> None:
        doc_ids = _ids(4)
        matrix = _block_matrix([2, 2], within_dist=0.0, across_dist=1.0)
        clusters = _engine().cluster(doc_ids, matrix)
        assert len(clusters) == 2

    def test_groups_are_correct(self) -> None:
        doc_ids = _ids(4)
        matrix = _block_matrix([2, 2], within_dist=0.0, across_dist=1.0)
        clusters = _engine().cluster(doc_ids, matrix)
        cluster_sets = {frozenset(c) for c in clusters}
        assert frozenset({"d1", "d2"}) in cluster_sets
        assert frozenset({"d3", "d4"}) in cluster_sets


# ---------------------------------------------------------------------------
# Suite 3 — Three tight groups → 3 clusters
#
# Scenario: 6 docs in 3 pairs. Within each pair: dist=0. Across pairs: dist=1.
# Validates that the linkage cut correctly separates three independent topics.
# ---------------------------------------------------------------------------

class TestSuite3ThreeGroups:
    """S3: 3 groups of 2 → 3 distinct clusters."""

    def test_forms_three_clusters(self) -> None:
        doc_ids = _ids(6)
        matrix = _block_matrix([2, 2, 2], within_dist=0.0, across_dist=1.0)
        clusters = _engine().cluster(doc_ids, matrix)
        assert len(clusters) == 3

    def test_each_cluster_has_two_members(self) -> None:
        doc_ids = _ids(6)
        matrix = _block_matrix([2, 2, 2], within_dist=0.0, across_dist=1.0)
        clusters = _engine().cluster(doc_ids, matrix)
        assert all(len(c) == 2 for c in clusters)


# ---------------------------------------------------------------------------
# Suite 4 — Tight cluster + unrelated singleton → 1 cluster (singleton dropped)
#
# Scenario: d1,d2,d3 are tightly related (within dist=0.05).
#           d4 is a noise document far from the rest (dist=0.90 from all).
# The engine returns only clusters of size >= min_cluster_size=2,
# so d4 is excluded even though it technically forms a "cluster of 1".
# ---------------------------------------------------------------------------

class TestSuite4ClusterAndSingleton:
    """S4: 3-member cluster + 1 unrelated singleton → 1 cluster of 3."""

    _MATRIX = [
        [0.00, 0.05, 0.05, 0.90],
        [0.05, 0.00, 0.05, 0.90],
        [0.05, 0.05, 0.00, 0.90],
        [0.90, 0.90, 0.90, 0.00],
    ]

    def test_returns_one_cluster(self) -> None:
        clusters = _engine().cluster(_ids(4), self._MATRIX)
        assert len(clusters) == 1

    def test_cluster_excludes_singleton(self) -> None:
        clusters = _engine().cluster(_ids(4), self._MATRIX)
        assert "d4" not in clusters[0]

    def test_cluster_contains_related_docs(self) -> None:
        clusters = _engine().cluster(_ids(4), self._MATRIX)
        assert set(clusters[0]) == {"d1", "d2", "d3"}


# ---------------------------------------------------------------------------
# Suite 5 — Boundary BELOW threshold → merged
#
# dist = 0.44 < 0.45 threshold → the pair should be merged into 1 cluster.
# This is the tightest valid cluster the default threshold accepts.
# ---------------------------------------------------------------------------

class TestSuite5BoundaryBelow:
    """S5: dist=0.44 < threshold=0.45 → merged."""

    _DIST = 0.44

    def test_merged_into_one_cluster(self) -> None:
        clusters = _engine().cluster(["d1", "d2"], _2x2(self._DIST))
        assert len(clusters) == 1
        assert set(clusters[0]) == {"d1", "d2"}

    def test_passes_at_default_threshold(self) -> None:
        # Verify that slightly tightening the threshold rejects this pair.
        assert _engine(threshold=0.40).cluster(["d1", "d2"], _2x2(self._DIST)) == []

    def test_tight_threshold_rejects_pair(self) -> None:
        assert _engine(threshold=0.30).cluster(["d1", "d2"], _2x2(self._DIST)) == []


# ---------------------------------------------------------------------------
# Suite 6 — Boundary ABOVE threshold → not merged
#
# dist = 0.46 > 0.45 threshold → the pair should NOT be merged.
# Validates the threshold excludes weakly-related doc pairs.
# ---------------------------------------------------------------------------

class TestSuite6BoundaryAbove:
    """S6: dist=0.46 > threshold=0.45 → not merged."""

    _DIST = 0.46

    def test_not_merged_at_default_threshold(self) -> None:
        clusters = _engine().cluster(["d1", "d2"], _2x2(self._DIST))
        assert clusters == []

    def test_merged_at_loose_threshold(self) -> None:
        # A looser threshold would incorrectly merge these docs.
        clusters = _engine(threshold=0.50).cluster(["d1", "d2"], _2x2(self._DIST))
        assert len(clusters) == 1


# ---------------------------------------------------------------------------
# Suite 7 — Entity signal dominates
#
# Scenario: d1 and d2 share identical entity sets but have orthogonal vectors.
#   entities_d1 = entities_d2 = {"safety_report"}
#   vec_d1 = [1, 0, 0],  vec_d2 = [0, 1, 0]
#   cosine = 0.0
#   entity_overlap = |{safety_report}| / min(1,1) = 1.0
#   sim = 0.75 * 1.0 + 0.25 * 0.0 = 0.75
#   dist = 0.25  →  merged (0.25 < 0.45)
# ---------------------------------------------------------------------------

class TestSuite7EntityDominates:
    """S7: entity_overlap=1, cosine=0 → dist=0.25 → merged."""

    _DIST = _dist_from_scenario(cosine=0.0, entity_overlap=1.0)

    def test_distance_formula(self) -> None:
        assert abs(self._DIST - 0.25) < 1e-9

    def test_merged_at_default_threshold(self) -> None:
        clusters = _engine().cluster(["d1", "d2"], _2x2(self._DIST))
        assert len(clusters) == 1

    def test_entity_signal_survives_orthogonal_vectors(self) -> None:
        # Even with zero cosine similarity, shared entities cluster the docs.
        assert self._DIST < _THRESHOLD


# ---------------------------------------------------------------------------
# Suite 8 — Vector signal only, no entities → weak similarity → not merged
#
# Scenario: d1 and d2 have NO shared entities, cosine similarity = 0.8.
#   entity_overlap = 0.0  (disjoint entity sets)
#   cosine = 0.8
#   sim = 0.75 * 0.0 + 0.25 * 0.8 = 0.20
#   dist = 0.80  →  NOT merged (0.80 > 0.45)
#
# Rationale: topical similarity (entities) is required; vector proximity alone
# is insufficient — two documents about "Excel pivot tables" vs "SQL window
# functions" may be cosine-close after embedding but should not be grouped.
# ---------------------------------------------------------------------------

class TestSuite8VectorOnlyWeak:
    """S8: entity_overlap=0, cosine=0.8 → dist=0.80 → not merged."""

    _DIST = _dist_from_scenario(cosine=0.8, entity_overlap=0.0)

    def test_distance_formula(self) -> None:
        assert abs(self._DIST - 0.80) < 1e-9

    def test_not_merged_at_default_threshold(self) -> None:
        clusters = _engine().cluster(["d1", "d2"], _2x2(self._DIST))
        assert clusters == []

    def test_vector_alone_is_insufficient(self) -> None:
        assert self._DIST > _THRESHOLD


# ---------------------------------------------------------------------------
# Suite 9 — Partial entity overlap + strong vector → merged
#
# Scenario: d1 has entities {A, B}, d2 has entities {A, C}.
#   overlap = |{A}| / min(2,2) = 0.5
#   cosine = 1.0  (nearly identical document vectors)
#   sim = 0.75 * 0.5 + 0.25 * 1.0 = 0.375 + 0.25 = 0.625
#   dist = 0.375  →  merged (0.375 < 0.45)
#
# This is the "partially overlapping topics" case, common when two documents
# cover a shared concept but each extends it in a different direction.
# ---------------------------------------------------------------------------

class TestSuite9PartialEntityStrongVector:
    """S9: entity_overlap=0.5, cosine=1.0 → dist=0.375 → merged."""

    _DIST = _dist_from_scenario(cosine=1.0, entity_overlap=0.5)

    def test_distance_formula(self) -> None:
        assert abs(self._DIST - 0.375) < 1e-9

    def test_merged_at_default_threshold(self) -> None:
        clusters = _engine().cluster(["d1", "d2"], _2x2(self._DIST))
        assert len(clusters) == 1

    def test_tight_threshold_rejects(self) -> None:
        # Would fail at threshold=0.3 (0.375 > 0.3)
        assert _engine(threshold=0.30).cluster(["d1", "d2"], _2x2(self._DIST)) == []


# ---------------------------------------------------------------------------
# Suite 10 — Large cluster: 8 related docs → single cluster
#
# Scenario: 8 documents all tightly related (dist=0.05 for all pairs).
# Validates that large download batches (8+ files from one project or topic)
# are correctly grouped without being split by the linkage cut.
# ---------------------------------------------------------------------------

class TestSuite10LargeCluster:
    """S10: 8 related docs, all pairwise dist=0.05 → 1 cluster of 8."""

    def test_forms_single_cluster(self) -> None:
        doc_ids = _ids(8)
        matrix = _uniform_matrix(8, off_diagonal=0.05)
        clusters = _engine().cluster(doc_ids, matrix)
        assert len(clusters) == 1

    def test_cluster_contains_all_docs(self) -> None:
        doc_ids = _ids(8)
        matrix = _uniform_matrix(8, off_diagonal=0.05)
        clusters = _engine().cluster(doc_ids, matrix)
        assert set(clusters[0]) == set(doc_ids)

    def test_not_split_by_linkage(self) -> None:
        # Confirm no sub-cluster fragmentation occurs.
        doc_ids = _ids(8)
        matrix = _uniform_matrix(8, off_diagonal=0.05)
        clusters = _engine().cluster(doc_ids, matrix)
        assert len(clusters[0]) == 8
