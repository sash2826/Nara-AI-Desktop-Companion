"""Agglomerative clustering engine for the new-folder discovery pipeline.

Takes a precomputed distance matrix from ClusterScorer and returns raw clusters
(groups of document IDs) using scipy's average-linkage agglomerative algorithm.

Design decisions (see ADR in docs/intelligent-folder-discovery-plan.md §12):
- scipy linkage/fcluster, not sklearn: metric-agnostic, accepts a precomputed
  condensed distance matrix so no raw vectors are needed here.
- Average linkage: balances inter-cluster separation and intra-cluster
  compactness; more robust than single or complete linkage on irregular clusters.
- min_cluster_size defaults to 2: a proposal requires at least two files so the
  system recommends a folder name with evidence, not a single-file alias.
"""

from __future__ import annotations

import logging

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

logger = logging.getLogger(__name__)

_DEFAULT_DISTANCE_THRESHOLD = 0.45
_DEFAULT_MIN_CLUSTER_SIZE = 2


class ClusterEngine:
    """Groups documents into raw clusters via average-linkage agglomerative clustering.

    Input is a precomputed N×N distance matrix (from ClusterScorer).
    Output is a list of clusters, each a list of document IDs.

    Singletons and clusters below ``min_cluster_size`` are discarded. The caller
    (ClusterDiscoveryService) applies the proposal gate before surfacing results.
    """

    def __init__(
        self,
        distance_threshold: float = _DEFAULT_DISTANCE_THRESHOLD,
        min_cluster_size: int = _DEFAULT_MIN_CLUSTER_SIZE,
    ) -> None:
        if not 0.0 < distance_threshold <= 1.0:
            raise ValueError(
                f"distance_threshold must be in (0, 1]; got {distance_threshold}"
            )
        if min_cluster_size < 2:
            raise ValueError(
                f"min_cluster_size must be >= 2; got {min_cluster_size}"
            )
        self._threshold = distance_threshold
        self._min_size = min_cluster_size

    def cluster(
        self,
        doc_ids: list[str],
        distance_matrix: list[list[float]],
    ) -> list[list[str]]:
        """Return non-singleton clusters from agglomerative clustering.

        Args:
            doc_ids: Ordered list of document IDs matching the matrix rows/cols.
            distance_matrix: N×N symmetric distance matrix from ClusterScorer.
                             Must be non-negative with zero diagonal.

        Returns:
            List of clusters; each cluster is a list of doc IDs from ``doc_ids``.
            Clusters below ``min_cluster_size`` are excluded. Order of clusters
            and order within each cluster are both deterministic (index order).
        """
        n = len(doc_ids)
        if n < 2:
            return []

        matrix = np.array(distance_matrix, dtype=float)

        # scipy's linkage requires a 1-D condensed distance array.
        # squareform converts our N×N symmetric matrix; checks=False avoids
        # the symmetry/diagonal assertion which can fail on float rounding.
        condensed = squareform(matrix, checks=False)

        # Average linkage on the condensed distance array.
        Z = linkage(condensed, method="average")

        # Cut the dendrogram: any pairs that merged at distance > threshold
        # are placed into separate clusters.
        labels: np.ndarray = fcluster(Z, t=self._threshold, criterion="distance")

        # Group doc_ids by cluster label. Labels are 1-based integers from scipy.
        groups: dict[int, list[str]] = {}
        for idx, label in enumerate(labels):
            groups.setdefault(int(label), []).append(doc_ids[idx])

        raw_clusters = list(groups.values())
        result = [g for g in raw_clusters if len(g) >= self._min_size]

        logger.debug(
            "[CLUSTER] %d doc(s) → %d raw cluster(s) → %d cluster(s) >= min_size %d",
            n,
            len(raw_clusters),
            len(result),
            self._min_size,
        )
        return result
