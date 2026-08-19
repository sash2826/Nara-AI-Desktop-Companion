"""Placement scorer for file organisation recommendations.

Combines two signals to score each candidate folder for a newly-indexed file:

  score = 0.75 × graph_score + 0.25 × rerank_score

graph_score — Overlap coefficient (Szymkiewicz-Simpson) between the new
  file's canonical entity names and those of documents already in the
  candidate folder, each set expanded 1 hop via graph relationships.

rerank_score — Mean RRF score returned by the rerank port when the new
  file's first chunk text is used as a query against each candidate folder's
  indexed content.

Only folders with a non-zero combined score are returned. The caller takes
the top-3 and attaches confidence labels.

Storage access is delegated to two injected ports so the scoring algorithm
can be tested without a database or Qdrant connection:

  GraphScorePort  — supplies canonical entity sets and candidate folders.
  RerankPort      — supplies the mean RRF score for a folder given a document.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from enterprise_ai_companion.capabilities.organisation.placement_ports import (
    GraphScorePort,
    RerankPort,
    expand_for_matching,
)

logger = logging.getLogger(__name__)

_GRAPH_WEIGHT = 0.75
_RERANK_WEIGHT = 0.25

_LABEL_STRONG = "Most Likely"
_LABEL_GOOD = "Likely"
_LABEL_POSSIBLE = "Possible"

_SCORE_STRONG_THRESHOLD = 0.60
_SCORE_GOOD_THRESHOLD = 0.30
# Candidates below this threshold are suppressed entirely — avoids spurious
# "Possible" suggestions when there is no meaningful topical overlap.
# Calibrated for Overlap coefficient scoring (not Jaccard). Files with zero
# intersection always score 0.0, so any positive threshold suffices to filter
# them. 0.20 filters out weak rerank-only signals and avoids spurious
# recommendations for unrelated files that share only generic terms.
_SCORE_MIN_THRESHOLD = 0.20

# Minimum combined score for the rerank-only fallback path. Higher than
# _SCORE_MIN_THRESHOLD because there is no graph gate backing this signal —
# we require the best folder's rerank_norm contribution to be meaningful.
# 0.25 × rerank_norm >= 0.18 means rerank_norm >= 0.72 (top folder must be
# clearly the best semantic match, not just marginally ahead).
_SCORE_RERANK_FALLBACK_THRESHOLD = 0.18

# Minimum raw rerank score the best-ranked folder must reach before the
# rerank-only fallback is activated. Higher than _RERANK_NORM_FLOOR (0.006)
# because the fallback has no graph gate backing it — we need a genuinely
# strong semantic signal, not just distinguishable noise. Calibrated against
# observed values: genuine matches produce ~0.014–0.016; noise is ~0.004–0.008.
_RERANK_FALLBACK_MIN_RAW = 0.012

# Minimum ratio of best-folder raw rerank to second-best before the fallback
# is activated. A genuine semantic match has one folder clearly ahead
# (observed ~4× for a matched file); an unrelated file has all folders
# roughly equal (~1.1–1.3×). Setting to 2.5 separates the two populations.
_RERANK_FALLBACK_RATIO = 2.5

# The graph score must reach this value before the rerank signal is added.
# Raising from >0.0 to >=0.10 eliminates false positives caused by a single
# coincidental shared entity (e.g. "photography" linking an equipment guide
# to a travel folder, or "data" linking a personal document to any project).
_GRAPH_GATE_THRESHOLD = 0.10

# Minimum raw rerank value the best folder must reach before normalisation is
# applied. Below this the scores are indistinguishable noise (~0.001–0.004
# from RRF rank arithmetic) and normalising them would amplify spurious matches.
_RERANK_NORM_FLOOR = 0.006

# Minimum number of entities that must overlap before a graph score is awarded.
# Set to 1: ancestor directories are now excluded from candidates, so a single
# overlapping domain-specific term (e.g. "atlas" linking Atlas_Meeting_Room.pdf
# to the Atlas-Workplace folder) is a meaningful signal rather than noise.
_MIN_INTERSECTION_COUNT = 1

# Generic business/document terms that appear in almost any file and cannot
# discriminate between project folders. Filtering them from the overlap
# computation prevents spurious matches caused by boilerplate vocabulary.
_GENERIC_TERMS: frozenset[str] = frozenset({
    # Document / business boilerplate
    "data", "report", "analysis", "management", "system",
    "process", "review", "plan", "strategy", "performance", "service",
    "solution", "information", "project", "team", "work", "business",
    "company", "organization", "requirement", "document", "guide",
    "overview", "update", "summary", "assessment", "evaluation",
    "implementation", "development", "application",
    "infrastructure", "technology", "digital", "enterprise", "global",
    "new", "key", "main", "core", "high", "low", "current", "future",
    "total", "list", "type", "use", "based", "level", "area",
    "structure", "approach", "objective", "result", "output", "input",
    "value", "quality", "standard", "policy", "procedure", "control",
    # Additional domain-generic terms that appear across all project types
    # and create false graph-overlap matches between unrelated folders.
    "framework", "monitoring", "reporting", "vendor", "supplier",
    "req",       # requirement abbreviation used as a doc-ID prefix everywhere
    # Cardinal directions and region labels extracted from spreadsheet columns
    # (e.g. "Region: North", "Zone: Central") — not project-discriminative.
    "north", "south", "east", "west", "central", "region", "zone",
})


@dataclass(frozen=True)
class FolderScore:
    """Score for a single candidate folder."""

    folder: str
    score: float
    label: str
    graph_score: float = 0.0
    rerank_score: float = 0.0


class PlacementScorer:
    """Scores candidate folders for a newly-indexed file.

    All storage access is delegated to the injected ports. The scoring
    algorithm (overlap coefficient, gate threshold, label assignment) lives
    entirely in this class and is independent of the storage implementation.
    """

    def __init__(
        self,
        graph_score_port: GraphScorePort,
        rerank_port: RerankPort,
    ) -> None:
        self._graph_score_port = graph_score_port
        self._rerank_port = rerank_port

    async def score_one(self, document_id: str, folder_path: str, file_path: str = "") -> float:
        """Return the combined score for a single folder against *document_id*.

        Used by the audit to get the current folder's score independently of
        the top-3 cap in score_all — without this, a file whose current folder
        ranks 4th or lower would have current_score=0.0, causing a false delta.
        """
        raw_canonicals = await self._graph_score_port.get_canonicals_for_document(
            document_id, file_path
        )
        new_file_canonicals = expand_for_matching(raw_canonicals)
        fs = await self._score_folder(
            document_id=document_id,
            folder_path=folder_path,
            new_file_canonicals=new_file_canonicals,
        )
        return fs.score

    async def score_all(
        self,
        document_id: str,
        candidate_folder_paths: list[str],
        file_path: str = "",
        graph_gate: float = _GRAPH_GATE_THRESHOLD,
    ) -> list[dict[str, Any]]:
        """Score every candidate folder and return up to 3 results sorted by score desc.

        Rerank scores are normalised within this call (best folder = 1.0) so
        the semantic signal is actually discriminative. Raw RRF values are
        ~0.005–0.02 and would contribute less than 0.005 to the combined
        score without normalisation — effectively making rerank a no-op.

        Returns a list of dicts suitable for JSON serialisation:
        ``[{"folder": str, "score": float, "label": str}, ...]``
        """
        if not candidate_folder_paths:
            return []

        raw_canonicals = await self._graph_score_port.get_canonicals_for_document(
            document_id, file_path
        )
        new_file_canonicals = expand_for_matching(raw_canonicals)

        logger.info(
            "[PLACEMENT] doc=%s canonical entities (%d → %d after expansion): %s",
            document_id, len(raw_canonicals), len(new_file_canonicals),
            sorted(new_file_canonicals)[:20],
        )

        # Pass 1 — collect raw (graph_s, rerank_s) for every folder in parallel.
        raw_pairs: list[tuple[float, float]] = list(
            await asyncio.gather(*[
                self._raw_scores(document_id, folder, new_file_canonicals)
                for folder in candidate_folder_paths
            ])
        )

        # Normalise rerank so the folder with the strongest semantic match
        # scores 1.0. Only normalise when max raw rerank clears the noise
        # floor — below it, all RRF scores are indistinguishable and
        # normalisation would amplify spurious matches.
        max_rerank = max((r for _, r in raw_pairs), default=0.0)

        # Pass 2 — apply graph gate and compute combined score.
        folder_scores: list[FolderScore] = []
        for folder, (graph_s, rerank_s) in zip(candidate_folder_paths, raw_pairs):
            rerank_norm = (
                (rerank_s / max_rerank)
                if max_rerank >= _RERANK_NORM_FLOOR
                else 0.0
            )
            if graph_s < graph_gate:
                combined = 0.0
                label = _LABEL_POSSIBLE
            else:
                combined = _GRAPH_WEIGHT * graph_s + _RERANK_WEIGHT * rerank_norm
                label = _label(combined)
            fs = FolderScore(
                folder=folder,
                score=combined,
                label=label,
                graph_score=graph_s,
                rerank_score=rerank_s,
            )
            folder_scores.append(fs)
            logger.info(
                "[PLACEMENT] folder=%s graph=%.4f rerank=%.4f rerank_norm=%.4f score=%.4f label=%s",
                fs.folder, graph_s, rerank_s, rerank_norm, combined, label,
            )

        scored = sorted(
            (fs for fs in folder_scores if fs.score >= _SCORE_MIN_THRESHOLD),
            key=lambda fs: fs.score,
            reverse=True,
        )

        sorted_reranks = sorted((r for _, r in raw_pairs), reverse=True)
        second_rerank = sorted_reranks[1] if len(sorted_reranks) > 1 else 0.0
        rerank_ratio = (max_rerank / second_rerank) if second_rerank > 0 else float("inf")

        if not scored and max_rerank >= _RERANK_FALLBACK_MIN_RAW and rerank_ratio >= _RERANK_FALLBACK_RATIO:
            # All folders were blocked by the graph gate (no entity overlap) but
            # one folder stands clearly ahead in semantic similarity (ratio check
            # ensures a single folder dominates, not all folders being equally noisy).
            # This catches semantically-placed files whose vocabulary doesn't match
            # graph entity sets — e.g. a data quality framework belonging in an
            # analytics folder but sharing no specific entity names with it.
            logger.info(
                "[PLACEMENT] Graph gate blocked all %d candidates — rerank-only fallback "
                "(max_rerank=%.5f ratio=%.2f)",
                len(folder_scores), max_rerank, rerank_ratio,
            )
            fallback_scores: list[FolderScore] = []
            for folder, (graph_s, rerank_s) in zip(candidate_folder_paths, raw_pairs):
                rerank_norm = rerank_s / max_rerank
                combined = _RERANK_WEIGHT * rerank_norm
                fallback_scores.append(FolderScore(
                    folder=folder,
                    score=combined,
                    label=_label(combined),
                    graph_score=graph_s,
                    rerank_score=rerank_s,
                ))
                logger.info(
                    "[PLACEMENT] fallback folder=%s rerank_norm=%.4f score=%.4f",
                    folder, rerank_norm, combined,
                )
            scored = sorted(
                (fs for fs in fallback_scores if fs.score >= _SCORE_RERANK_FALLBACK_THRESHOLD),
                key=lambda fs: fs.score,
                reverse=True,
            )

        if not scored:
            logger.info(
                "[PLACEMENT] All %d candidate(s) below threshold — no recommendation",
                len(folder_scores),
            )

        return [
            {"folder": fs.folder, "score": round(fs.score, 4), "label": fs.label}
            for fs in scored[:3]
        ]

    async def discover_candidate_folders(
        self,
        exclude_paths: set[str] | None = None,
        max_candidates: int = 150,
    ) -> list[str]:
        """Return unique parent directories discovered from indexed file paths."""
        return await self._graph_score_port.get_known_folder_paths(
            exclude_paths=exclude_paths,
            max_candidates=max_candidates,
        )

    # ------------------------------------------------------------------
    # Internal scoring
    # ------------------------------------------------------------------

    async def _raw_scores(
        self,
        document_id: str,
        folder_path: str,
        new_file_canonicals: set[str],
    ) -> tuple[float, float]:
        """Return (graph_s, rerank_s) without applying gate or weighting."""
        graph_s, rerank_s = await asyncio.gather(
            self._graph_score(folder_path, new_file_canonicals),
            self._rerank_port.rerank(document_id, folder_path),
        )
        return graph_s, rerank_s

    async def _score_folder(
        self,
        document_id: str,
        folder_path: str,
        new_file_canonicals: set[str],
        graph_gate: float = _GRAPH_GATE_THRESHOLD,
    ) -> FolderScore:
        graph_s, rerank_s = await asyncio.gather(
            self._graph_score(folder_path, new_file_canonicals),
            self._rerank_port.rerank(document_id, folder_path),
        )
        # Graph score is the gate. RRF rerank returns small positive scores for
        # ANY query, so rerank alone creates false positives for unrelated files.
        # We require graph_s >= graph_gate (default _GRAPH_GATE_THRESHOLD) so
        # that a single coincidental entity overlap is suppressed. Callers such
        # as AuditService may pass graph_gate=0.0 to allow rerank-only signals
        # for files whose vocabulary doesn't overlap the graph entity set.
        if graph_s < graph_gate:
            return FolderScore(
                folder=folder_path, score=0.0, label=_LABEL_POSSIBLE,
                graph_score=graph_s, rerank_score=rerank_s,
            )
        combined = _GRAPH_WEIGHT * graph_s + _RERANK_WEIGHT * rerank_s
        return FolderScore(
            folder=folder_path,
            score=combined,
            label=_label(combined),
            graph_score=graph_s,
            rerank_score=rerank_s,
        )

    async def _graph_score(
        self,
        folder_path: str,
        new_file_canonicals: set[str],
    ) -> float:
        """Overlap coefficient on canonical entity names between new file and folder.

        Uses min(|A|, |B|) as the denominator (Szymkiewicz-Simpson / overlap
        coefficient) rather than Jaccard's union. Jaccard penalises a genuine
        match when the folder has many more entities than the new file — e.g. a
        5-entity file with 1 matching term against a 30-entity folder gives
        Jaccard = 1/34 ≈ 0.03 but Overlap = 1/5 = 0.20, which correctly
        reflects that 20% of the new file's topics are represented.
        """
        if not new_file_canonicals:
            return 0.0

        folder_canonicals = await self._graph_score_port.get_canonicals_for_folder(folder_path)
        if not folder_canonicals:
            return 0.0

        # Strip generic boilerplate terms before computing overlap so that
        # words like "data", "report", "framework" cannot single-handedly
        # create a false match between an unrelated file and a project folder.
        effective_new = new_file_canonicals - _GENERIC_TERMS
        effective_folder = folder_canonicals - _GENERIC_TERMS

        intersection = effective_new & effective_folder

        if len(intersection) < _MIN_INTERSECTION_COUNT:
            logger.debug(
                "[PLACEMENT] graph_score folder=%s intersection=%d < min=%d — suppressed",
                folder_path, len(intersection), _MIN_INTERSECTION_COUNT,
            )
            return 0.0

        denominator = min(len(effective_new), len(effective_folder))
        logger.debug(
            "[PLACEMENT] graph_score folder=%s intersection=%d denominator=%d",
            folder_path, len(intersection), denominator,
        )
        return len(intersection) / denominator if denominator else 0.0


def _label(score: float) -> str:
    if score >= _SCORE_STRONG_THRESHOLD:
        return _LABEL_STRONG
    if score >= _SCORE_GOOD_THRESHOLD:
        return _LABEL_GOOD
    return _LABEL_POSSIBLE
