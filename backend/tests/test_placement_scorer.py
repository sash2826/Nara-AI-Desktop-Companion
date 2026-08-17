"""Unit tests for PlacementScorer.

All tests use in-memory fakes — no database, no Qdrant required.
The fakes implement the port interfaces so the scoring algorithm is
exercised in full isolation from storage details.
"""

from __future__ import annotations

import os
import pytest

from enterprise_ai_companion.capabilities.organisation.placement_ports import (
    GraphScorePort,
    RerankPort,
)
from enterprise_ai_companion.capabilities.organisation.placement_scorer import (
    PlacementScorer,
    _GENERIC_TERMS,
    _GRAPH_GATE_THRESHOLD,
    _GRAPH_WEIGHT,
    _LABEL_GOOD,
    _LABEL_POSSIBLE,
    _LABEL_STRONG,
    _RERANK_WEIGHT,
    _SCORE_GOOD_THRESHOLD,
    _SCORE_MIN_THRESHOLD,
    _SCORE_STRONG_THRESHOLD,
)


# ---------------------------------------------------------------------------
# In-memory fakes
# ---------------------------------------------------------------------------

class FakeGraphScorePort(GraphScorePort):
    """Returns pre-configured canonical sets without touching a database."""

    def __init__(
        self,
        doc_canonicals: dict[str, set[str]] | None = None,
        folder_canonicals: dict[str, set[str]] | None = None,
        known_folders: list[str] | None = None,
    ) -> None:
        self._doc_canonicals = doc_canonicals or {}
        self._folder_canonicals = folder_canonicals or {}
        self._known_folders = known_folders or []

    async def get_canonicals_for_document(
        self, document_id: str, file_path: str
    ) -> set[str]:
        return self._doc_canonicals.get(document_id, set())

    async def get_canonicals_for_folder(self, folder_path: str) -> set[str]:
        return self._folder_canonicals.get(folder_path, set())

    async def get_known_folder_paths(
        self,
        exclude_paths: set[str] | None = None,
        max_candidates: int = 150,
    ) -> list[str]:
        exclude = exclude_paths or set()
        return [f for f in self._known_folders if f not in exclude]


class FakeRerankPort(RerankPort):
    """Returns a fixed rerank score per (document_id, folder_path) pair."""

    def __init__(self, scores: dict[tuple[str, str], float] | None = None) -> None:
        # scores keyed by (document_id, folder_path); default 0.0
        self._scores = scores or {}

    async def rerank(self, document_id: str, folder_path: str, top_k: int = 30) -> float:
        return self._scores.get((document_id, folder_path), 0.0)


def make_scorer(
    doc_canonicals: dict[str, set[str]] | None = None,
    folder_canonicals: dict[str, set[str]] | None = None,
    known_folders: list[str] | None = None,
    rerank_scores: dict[tuple[str, str], float] | None = None,
) -> PlacementScorer:
    return PlacementScorer(
        graph_score_port=FakeGraphScorePort(doc_canonicals, folder_canonicals, known_folders),
        rerank_port=FakeRerankPort(rerank_scores),
    )


# ---------------------------------------------------------------------------
# Graph score — overlap coefficient
# ---------------------------------------------------------------------------

class TestGraphScore:
    @pytest.mark.asyncio
    async def test_exact_match_returns_1(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan", "photography"}},
            folder_canonicals={"/folder": {"japan", "photography"}},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        # graph_s = 1.0, gate cleared, rerank=0.0 → combined = 0.75
        assert result[0]["score"] == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_overlap_coefficient_uses_smaller_set_as_denominator(self):
        # doc has 2 entities, folder has 10; 1 overlaps → 1/2 = 0.5 (not 1/11 Jaccard)
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan", "photography"}},
            folder_canonicals={"/folder": {"japan", "travel", "asia", "culture",
                                           "food", "nature", "urban", "tradition",
                                           "history", "art"}},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        # effective doc: {japan, photography} (neither generic)
        # effective folder: the 10 terms minus generic = all 10
        # intersection = {japan} → 1; denominator = min(2, 10) = 2 → graph_s = 0.5
        # gate 0.5 >= 0.10 ✓; combined = 0.75 * 0.5 + 0.25 * 0.0 = 0.375
        assert result[0]["score"] == pytest.approx(0.375)

    @pytest.mark.asyncio
    async def test_generic_terms_stripped_before_overlap(self):
        # Both doc and folder share only generic terms — should score 0
        generic_pair = set(list(_GENERIC_TERMS)[:3])
        scorer = make_scorer(
            doc_canonicals={"doc1": generic_pair},
            folder_canonicals={"/folder": generic_pair},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_doc_canonicals_returns_zero(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": set()},
            folder_canonicals={"/folder": {"japan", "photography"}},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_folder_canonicals_returns_zero(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan", "photography"}},
            folder_canonicals={"/folder": set()},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert result == []

    @pytest.mark.asyncio
    async def test_no_intersection_returns_zero(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan", "photography"}},
            folder_canonicals={"/folder": {"finance", "budget", "accounting"}},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert result == []


# ---------------------------------------------------------------------------
# Graph gate — rerank is suppressed when graph_score < threshold
# ---------------------------------------------------------------------------

class TestGraphGate:
    @pytest.mark.asyncio
    async def test_rerank_not_added_when_graph_below_gate(self):
        # Overlap coefficient = intersection / min(|doc|, |folder|).
        # With both sets size 12 and 1 overlap: 1/12 ≈ 0.083 < gate (0.10).
        # Even with rerank=1.0 the gate blocks the rerank signal → score=0.0 → suppressed.
        doc_ents = {f"term{i}" for i in range(12)}
        folder_ents = {"term0"} | {f"other{i}" for i in range(11)}  # 1 overlap, 12 total
        scorer = make_scorer(
            doc_canonicals={"doc1": doc_ents},
            folder_canonicals={"/folder": folder_ents},
            rerank_scores={("doc1", "/folder"): 1.0},  # high rerank, should be ignored
        )
        result = await scorer.score_all("doc1", ["/folder"])
        # score=0.0, below _SCORE_MIN_THRESHOLD → suppressed
        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_added_when_graph_meets_gate(self):
        # 1 entity overlapping out of 5 → graph_s = 0.20, above gate 0.10
        scorer = make_scorer(
            doc_canonicals={"doc1": {"a", "b", "c", "d", "e"}},
            folder_canonicals={"/folder": {"a", "x", "y", "z", "w"}},
            rerank_scores={("doc1", "/folder"): 0.5},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        # graph_s = 1/5 = 0.2; combined = 0.75*0.2 + 0.25*0.5 = 0.15 + 0.125 = 0.275
        # 0.275 >= 0.20 → returned
        assert len(result) == 1
        assert result[0]["score"] == pytest.approx(0.275)


# ---------------------------------------------------------------------------
# Combined score weighting
# ---------------------------------------------------------------------------

class TestCombinedScore:
    @pytest.mark.asyncio
    async def test_weight_formula_is_correct(self):
        graph_s = 0.8
        rerank_s = 0.6
        # Set up exactly: 4/5 overlap (graph_s=0.8) and rerank returns 0.6
        scorer = make_scorer(
            doc_canonicals={"doc1": {"a", "b", "c", "d", "e"}},
            folder_canonicals={"/folder": {"a", "b", "c", "d", "z"}},
            rerank_scores={("doc1", "/folder"): rerank_s},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        expected = _GRAPH_WEIGHT * graph_s + _RERANK_WEIGHT * rerank_s
        assert result[0]["score"] == pytest.approx(expected, abs=1e-4)

    @pytest.mark.asyncio
    async def test_zero_rerank_does_not_break_scoring(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan", "photography"}},
            folder_canonicals={"/folder": {"japan", "photography"}},
            rerank_scores={},  # defaults to 0.0
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert result[0]["score"] == pytest.approx(_GRAPH_WEIGHT * 1.0)


# ---------------------------------------------------------------------------
# Label assignment
# ---------------------------------------------------------------------------

class TestLabels:
    @pytest.mark.asyncio
    async def test_strong_label_above_threshold(self):
        # Need combined >= 0.60. graph_s=1.0, rerank=0 → 0.75 ✓
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan", "photography"}},
            folder_canonicals={"/folder": {"japan", "photography"}},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert result[0]["label"] == _LABEL_STRONG

    @pytest.mark.asyncio
    async def test_good_label_in_middle_band(self):
        # Need 0.30 <= combined < 0.60.
        # graph_s = 2/5 = 0.4, rerank=0 → combined = 0.75*0.4 = 0.30 exactly
        scorer = make_scorer(
            doc_canonicals={"doc1": {"a", "b", "c", "d", "e"}},
            folder_canonicals={"/folder": {"a", "b", "x", "y", "z"}},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert result[0]["label"] == _LABEL_GOOD

    @pytest.mark.asyncio
    async def test_possible_label_just_above_min_threshold(self):
        # graph_s = 1/5 = 0.2, rerank=0.1 → combined = 0.75*0.2 + 0.25*0.1 = 0.175
        # 0.175 < _SCORE_MIN_THRESHOLD (0.20) → suppressed
        # Adjust: need combined ≥ 0.20 but < 0.30
        # graph_s = 1/4 = 0.25, rerank=0 → combined = 0.1875 < 0.20 — still suppressed
        # graph_s = 2/5 = 0.40 gives GOOD. Use rerank to nudge differently:
        # graph_s=0.25 (1 of 4), rerank=0.15 → 0.75*0.25 + 0.25*0.15 = 0.225 ≥ 0.20 → POSSIBLE
        scorer = make_scorer(
            doc_canonicals={"doc1": {"a", "b", "c", "d"}},
            folder_canonicals={"/folder": {"a", "x", "y", "z"}},
            rerank_scores={("doc1", "/folder"): 0.15},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert len(result) == 1
        assert result[0]["label"] == _LABEL_POSSIBLE


# ---------------------------------------------------------------------------
# score_all — top-3 cap, min threshold filtering, sorting
# ---------------------------------------------------------------------------

class TestScoreAll:
    @pytest.mark.asyncio
    async def test_returns_at_most_three_results(self):
        folders = [f"/folder{i}" for i in range(6)]
        # Each folder shares half its entities with the doc
        scorer = make_scorer(
            doc_canonicals={"doc1": {"a", "b", "c", "d"}},
            folder_canonicals={f: {"a", "b", "x", "y"} for f in folders},
        )
        result = await scorer.score_all("doc1", folders)
        assert len(result) <= 3

    @pytest.mark.asyncio
    async def test_results_sorted_descending(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": {"a", "b", "c"}},
            folder_canonicals={
                "/low": {"a", "x", "y"},         # 1/3 overlap
                "/mid": {"a", "b", "x"},          # 2/3 overlap
                "/high": {"a", "b", "c"},          # 3/3 overlap
            },
        )
        result = await scorer.score_all("doc1", ["/low", "/mid", "/high"])
        scores = [r["score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_below_min_threshold_suppressed(self):
        # Overlap coefficient uses min(|doc|, |folder|) as denominator.
        # folder has 3 terms, doc has 3 terms, 1 overlaps → 1/3 ≈ 0.33, gate cleared.
        # To stay below _SCORE_MIN_THRESHOLD (0.20), need combined < 0.20.
        # Use a single shared term out of 12 on each side: 1/12 ≈ 0.083 < gate → score=0.
        doc_ents = {f"doc{i}" for i in range(12)}
        folder_ents = {"doc0"} | {f"fld{i}" for i in range(11)}
        scorer = make_scorer(
            doc_canonicals={"doc1": doc_ents},
            folder_canonicals={"/folder": folder_ents},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_candidates_returns_empty(self):
        scorer = make_scorer(doc_canonicals={"doc1": {"japan"}})
        result = await scorer.score_all("doc1", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_result_shape(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan", "photography"}},
            folder_canonicals={"/folder": {"japan", "photography"}},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        assert len(result) == 1
        assert set(result[0].keys()) == {"folder", "score", "label"}
        assert result[0]["folder"] == "/folder"


# ---------------------------------------------------------------------------
# score_one
# ---------------------------------------------------------------------------

class TestScoreOne:
    @pytest.mark.asyncio
    async def test_returns_float(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan", "photography"}},
            folder_canonicals={"/folder": {"japan", "photography"}},
        )
        score = await scorer.score_one("doc1", "/folder")
        assert isinstance(score, float)
        assert score == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_zero_for_no_overlap(self):
        scorer = make_scorer(
            doc_canonicals={"doc1": {"finance"}},
            folder_canonicals={"/folder": {"photography", "travel"}},
        )
        score = await scorer.score_one("doc1", "/folder")
        assert score == 0.0


# ---------------------------------------------------------------------------
# discover_candidate_folders — delegates to port
# ---------------------------------------------------------------------------

class TestDiscoverCandidateFolders:
    @pytest.mark.asyncio
    async def test_delegates_to_port(self):
        folders = ["/docs/finance", "/docs/hr", "/docs/it"]
        scorer = make_scorer(known_folders=folders)
        result = await scorer.discover_candidate_folders()
        assert result == folders

    @pytest.mark.asyncio
    async def test_exclude_paths_forwarded(self):
        import os
        from pathlib import Path
        downloads = str(Path.home() / "Downloads")
        folders = ["/docs/finance", downloads]
        scorer = make_scorer(known_folders=folders)
        result = await scorer.discover_candidate_folders(exclude_paths={downloads})
        assert downloads not in result
        assert "/docs/finance" in result


# ---------------------------------------------------------------------------
# Multi-word entity expansion (via scorer internals, verified via score_all)
# ---------------------------------------------------------------------------

class TestEntityExpansion:
    @pytest.mark.asyncio
    async def test_multi_word_entity_bridges_single_word_canonical(self):
        # Doc has multi-word entity "japan photography trip"; folder has "japan"
        # After expand_for_matching, doc gains "japan" as a token → overlap occurs
        scorer = make_scorer(
            doc_canonicals={"doc1": {"japan photography trip"}},
            folder_canonicals={"/folder": {"japan", "travel"}},
        )
        result = await scorer.score_all("doc1", ["/folder"])
        # "japan" extracted from multi-word → intersection = {"japan"}
        assert len(result) == 1
        assert result[0]["score"] > 0
