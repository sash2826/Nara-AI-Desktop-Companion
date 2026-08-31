"""Pairwise document distance matrix for agglomerative clustering.

Combines two signals into a single similarity score and converts to a
distance matrix (1 − similarity) suitable for scipy's linkage function.

  combined_similarity(i, j) = α × entity_overlap(i, j)
                             + (1 − α) × cosine_similarity(i, j)

  distance(i, j) = 1 − combined_similarity(i, j)

entity_overlap  — Szymkiewicz-Simpson overlap coefficient between the two
                  documents' canonical entity sets from the knowledge graph.
                  Mirrors the formula used by PlacementScorer.

cosine_similarity — Cosine similarity between the two document vectors
                    supplied by DocumentVectorService.

α = EAC_CLUSTER_ENTITY_WEIGHT (default 0.75). The calibrated value from
Phase I benchmark Suite 1 overrides this default.
"""

from __future__ import annotations

import logging
import math

from enterprise_ai_companion.capabilities.organisation.placement_ports import GraphScorePort

logger = logging.getLogger(__name__)

# Default entity-weight mirrors PlacementScorer's _GRAPH_WEIGHT. Overridden at
# construction time from EAC_CLUSTER_ENTITY_WEIGHT so the caller controls it.
_DEFAULT_ENTITY_WEIGHT = 0.75


class ClusterScorer:
    """Builds a pairwise distance matrix from entity overlap and cosine similarity.

    The graph score port supplies canonical entity sets. Document vectors are
    passed directly (they come from DocumentVectorService which owns Qdrant I/O).
    """

    def __init__(
        self,
        graph_score_port: GraphScorePort,
        entity_weight: float = _DEFAULT_ENTITY_WEIGHT,
    ) -> None:
        if not 0.0 <= entity_weight <= 1.0:
            raise ValueError(
                f"entity_weight must be in [0, 1]; got {entity_weight}"
            )
        self._graph = graph_score_port
        self._entity_weight = entity_weight
        self._cosine_weight = 1.0 - entity_weight

    async def compute_distance_matrix(
        self,
        doc_ids: list[str],
        vectors: dict[str, list[float]],
    ) -> list[list[float]]:
        """Return an N×N symmetric distance matrix for the supplied documents.

        Args:
            doc_ids: Ordered list of document IDs; defines the row/column order.
            vectors: doc_id → averaged embedding vector (from DocumentVectorService).
                     Documents absent from ``vectors`` receive cosine_similarity 0.

        Returns:
            N×N matrix where entry [i][j] = distance(doc_ids[i], doc_ids[j]).
            Diagonal is always 0.0. Values are in [0, 1].
        """
        n = len(doc_ids)
        if n == 0:
            return []

        # Fetch all canonical entity sets in parallel.
        entity_sets = await self._fetch_entity_sets(doc_ids)

        # Build the matrix. Only compute the upper triangle; mirror to lower.
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._pairwise_similarity(
                    doc_ids[i], doc_ids[j], vectors, entity_sets
                )
                dist = max(0.0, 1.0 - sim)  # clamp to [0, 1]
                matrix[i][j] = dist
                matrix[j][i] = dist

        return matrix

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_entity_sets(
        self, doc_ids: list[str]
    ) -> dict[str, frozenset[str]]:
        """Fetch canonical entity sets for all documents."""
        result: dict[str, frozenset[str]] = {}
        for doc_id in doc_ids:
            try:
                canonicals = await self._graph.get_canonicals_for_document(doc_id)
                result[doc_id] = frozenset(canonicals)
            except Exception as exc:
                logger.warning(
                    "[CLUSTER] Could not fetch entities for %s: %s", doc_id, exc
                )
                result[doc_id] = frozenset()
        return result

    def _pairwise_similarity(
        self,
        id_a: str,
        id_b: str,
        vectors: dict[str, list[float]],
        entity_sets: dict[str, frozenset[str]],
    ) -> float:
        vec_a = vectors.get(id_a)
        vec_b = vectors.get(id_b)
        cosine_sim = (
            _cosine_similarity(vec_a, vec_b)
            if vec_a is not None and vec_b is not None
            else 0.0
        )
        entity_sim = _overlap_coefficient(
            entity_sets.get(id_a, frozenset()),
            entity_sets.get(id_b, frozenset()),
        )
        return self._entity_weight * entity_sim + self._cosine_weight * cosine_sim


# ---------------------------------------------------------------------------
# Pure helpers — no I/O, fully testable standalone
# ---------------------------------------------------------------------------

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity in [−1, 1]. Returns 0.0 for zero-norm vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _overlap_coefficient(a: frozenset[str], b: frozenset[str]) -> float:
    """Szymkiewicz-Simpson overlap coefficient: |A ∩ B| / min(|A|, |B|).

    Returns 0.0 when either set is empty. Mirrors PlacementScorer's formula.
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))
