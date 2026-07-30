"""Tests for the hybrid search orchestrator and /search/hybrid endpoint.

Covers three areas:
1. _rrf_merge() unit tests — pure function, no I/O.
2. HybridSearchOrchestrator.search() with mocked providers.
3. POST /search/hybrid FastAPI endpoint via TestClient.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from enterprise_ai_companion.api.app import app
from enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator import (
    HybridSearchOrchestrator,
    HybridSearchResult,
    _rrf_merge,
)
from enterprise_ai_companion.capabilities.retrieval.search_models import SearchResult


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_result(chunk_id: str, doc_id: str = "doc1", score: float = 1.0) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id,
        document_id=doc_id,
        document_path=f"/docs/{doc_id}.md",
        chunk_index=0,
        content=f"Content for {chunk_id}",
        score=score,
    )


# ─── _rrf_merge unit tests ────────────────────────────────────────────────────

class TestRrfMerge:
    def test_empty_inputs_returns_empty(self) -> None:
        results = _rrf_merge([], [])
        assert results == []

    def test_keyword_only_list(self) -> None:
        kw = [_make_result("c1"), _make_result("c2")]
        results = _rrf_merge(kw, [])
        assert len(results) == 2
        # All results should have semantic_rank=None
        for r in results:
            assert r.semantic_rank is None
            assert r.keyword_rank is not None

    def test_semantic_only_list(self) -> None:
        sem = [_make_result("c1"), _make_result("c2")]
        results = _rrf_merge([], sem)
        assert len(results) == 2
        for r in results:
            assert r.keyword_rank is None
            assert r.semantic_rank is not None

    def test_single_item_each_different_chunks(self) -> None:
        kw = [_make_result("c1")]
        sem = [_make_result("c2")]
        results = _rrf_merge(kw, sem)
        assert len(results) == 2

    def test_same_chunk_in_both_lists_scores_higher(self) -> None:
        # c1 appears in both; c2 and c3 appear in only one list.
        kw = [_make_result("c1"), _make_result("c2")]
        sem = [_make_result("c1"), _make_result("c3")]
        results = _rrf_merge(kw, sem)
        scores = {r.chunk_id: r.rrf_score for r in results}
        # c1 should score highest because it receives RRF contributions from both lists.
        assert scores["c1"] > scores["c2"]
        assert scores["c1"] > scores["c3"]

    def test_results_are_ordered_descending_by_rrf_score(self) -> None:
        kw = [_make_result(f"c{i}") for i in range(5)]
        sem = [_make_result("c0")]  # c0 appears in both → should rank first
        results = _rrf_merge(kw, sem)
        rrf_scores = [r.rrf_score for r in results]
        assert rrf_scores == sorted(rrf_scores, reverse=True)

    def test_rank_fields_populated_correctly(self) -> None:
        kw = [_make_result("c1"), _make_result("c2")]
        sem = [_make_result("c2"), _make_result("c3")]
        results = _rrf_merge(kw, sem)
        by_id = {r.chunk_id: r for r in results}

        assert by_id["c1"].keyword_rank == 1
        assert by_id["c1"].semantic_rank is None

        assert by_id["c2"].keyword_rank == 2
        assert by_id["c2"].semantic_rank == 1

        assert by_id["c3"].keyword_rank is None
        assert by_id["c3"].semantic_rank == 2

    def test_rrf_formula_value(self) -> None:
        """Verify the score for a chunk that appears at rank 1 in one list only."""
        kw = [_make_result("c1")]
        results = _rrf_merge(kw, [])
        # With K=60 and rank=1: score = 1 / (60 + 1) ≈ 0.01639
        expected = 1.0 / (60 + 1)
        assert abs(results[0].rrf_score - expected) < 1e-9

    def test_semantic_weight_doubles_semantic_contribution(self) -> None:
        kw = [_make_result("c1")]
        sem = [_make_result("c2")]
        default = _rrf_merge(kw, sem, semantic_weight=1.0, keyword_weight=1.0)
        weighted = _rrf_merge(kw, sem, semantic_weight=2.0, keyword_weight=1.0)

        default_scores = {r.chunk_id: r.rrf_score for r in default}
        weighted_scores = {r.chunk_id: r.rrf_score for r in weighted}

        # c2 is semantic-only; its score should double.
        assert abs(weighted_scores["c2"] - 2.0 * default_scores["c2"]) < 1e-9
        # c1 is keyword-only; weight=1.0 unchanged.
        assert abs(weighted_scores["c1"] - default_scores["c1"]) < 1e-9

    def test_keyword_weight_doubles_keyword_contribution(self) -> None:
        kw = [_make_result("c1")]
        sem = [_make_result("c2")]
        default = _rrf_merge(kw, sem, semantic_weight=1.0, keyword_weight=1.0)
        weighted = _rrf_merge(kw, sem, semantic_weight=1.0, keyword_weight=2.0)

        default_scores = {r.chunk_id: r.rrf_score for r in default}
        weighted_scores = {r.chunk_id: r.rrf_score for r in weighted}

        assert abs(weighted_scores["c1"] - 2.0 * default_scores["c1"]) < 1e-9
        assert abs(weighted_scores["c2"] - default_scores["c2"]) < 1e-9

    def test_zero_weight_removes_provider_contribution(self) -> None:
        kw = [_make_result("c1")]
        sem = [_make_result("c2")]
        results = _rrf_merge(kw, sem, semantic_weight=0.0, keyword_weight=1.0)
        scores = {r.chunk_id: r.rrf_score for r in results}
        # Semantic provider suppressed — c2 scores 0.
        assert scores["c2"] == 0.0
        assert scores["c1"] > 0.0

    def test_deduplication_by_chunk_id(self) -> None:
        """A chunk_id appearing in both lists should produce exactly one result."""
        kw = [_make_result("shared")]
        sem = [_make_result("shared")]
        results = _rrf_merge(kw, sem)
        chunk_ids = [r.chunk_id for r in results]
        assert len(chunk_ids) == len(set(chunk_ids))

    def test_result_type_is_hybrid_search_result(self) -> None:
        results = _rrf_merge([_make_result("c1")], [])
        assert isinstance(results[0], HybridSearchResult)


# ─── HybridSearchOrchestrator tests ──────────────────────────────────────────

class TestHybridSearchOrchestrator:
    def _make_orchestrator(
        self,
        keyword_results: list[SearchResult] | None = None,
        semantic_results: list[SearchResult] | None = None,
    ) -> HybridSearchOrchestrator:
        conn = MagicMock()
        qdrant_client = MagicMock()
        embedding_service = MagicMock()
        orchestrator = HybridSearchOrchestrator(
            conn=conn,
            qdrant_client=qdrant_client,
            embedding_service=embedding_service,
        )
        orchestrator._keyword.search = AsyncMock(return_value=keyword_results or [])
        orchestrator._semantic.search = AsyncMock(return_value=semantic_results or [])
        return orchestrator

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self) -> None:
        orchestrator = self._make_orchestrator()
        results = await orchestrator.search("   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_returns_at_most_top_k(self) -> None:
        chunks = [_make_result(f"c{i}") for i in range(20)]
        orchestrator = self._make_orchestrator(keyword_results=chunks, semantic_results=chunks)
        results = await orchestrator.search("test", top_k=5)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_merges_results_from_both_providers(self) -> None:
        kw = [_make_result("k1"), _make_result("k2")]
        sem = [_make_result("s1"), _make_result("s2")]
        orchestrator = self._make_orchestrator(keyword_results=kw, semantic_results=sem)
        results = await orchestrator.search("test", top_k=10)
        chunk_ids = {r.chunk_id for r in results}
        assert {"k1", "k2", "s1", "s2"} == chunk_ids

    @pytest.mark.asyncio
    async def test_keyword_provider_failure_returns_semantic_only(self) -> None:
        sem = [_make_result("s1")]
        orchestrator = self._make_orchestrator(semantic_results=sem)
        orchestrator._keyword.search = AsyncMock(side_effect=RuntimeError("DB unavailable"))
        results = await orchestrator.search("test")
        assert len(results) == 1
        assert results[0].chunk_id == "s1"

    @pytest.mark.asyncio
    async def test_semantic_provider_failure_returns_keyword_only(self) -> None:
        kw = [_make_result("k1")]
        orchestrator = self._make_orchestrator(keyword_results=kw)
        orchestrator._semantic.search = AsyncMock(side_effect=RuntimeError("Qdrant unavailable"))
        results = await orchestrator.search("test")
        assert len(results) == 1
        assert results[0].chunk_id == "k1"

    @pytest.mark.asyncio
    async def test_both_providers_fail_returns_empty(self) -> None:
        orchestrator = self._make_orchestrator()
        orchestrator._keyword.search = AsyncMock(side_effect=RuntimeError("fail"))
        orchestrator._semantic.search = AsyncMock(side_effect=RuntimeError("fail"))
        results = await orchestrator.search("test")
        assert results == []

    @pytest.mark.asyncio
    async def test_providers_receive_preprocessed_query(self) -> None:
        kw = [_make_result("k1")]
        orchestrator = self._make_orchestrator(keyword_results=kw)
        await orchestrator.search("hello world", top_k=5, workspace_path="/ws")
        call_kwargs = orchestrator._keyword.search.call_args
        assert call_kwargs.kwargs.get("workspace_path") == "/ws" or call_kwargs.args[2] == "/ws"

    @pytest.mark.asyncio
    async def test_result_order_by_rrf_score_descending(self) -> None:
        # c1 in both lists → higher RRF; c2 keyword-only, c3 semantic-only.
        kw = [_make_result("c1"), _make_result("c2")]
        sem = [_make_result("c1"), _make_result("c3")]
        orchestrator = self._make_orchestrator(keyword_results=kw, semantic_results=sem)
        results = await orchestrator.search("test", top_k=10)
        assert results[0].chunk_id == "c1"
        rrf_scores = [r.rrf_score for r in results]
        assert rrf_scores == sorted(rrf_scores, reverse=True)

    @pytest.mark.asyncio
    async def test_weight_parameters_passed_to_rrf(self) -> None:
        """semantic_weight=0 should suppress semantic contribution."""
        kw = [_make_result("k1")]
        sem = [_make_result("s1")]
        orchestrator = self._make_orchestrator(keyword_results=kw, semantic_results=sem)
        results = await orchestrator.search("test", top_k=10, semantic_weight=0.0)
        scores = {r.chunk_id: r.rrf_score for r in results}
        assert scores["s1"] == 0.0
        assert scores["k1"] > 0.0


# ─── POST /search/hybrid endpoint tests ──────────────────────────────────────

def _make_client() -> TestClient:
    """Return a TestClient with mocked app.state attributes."""
    mock_db = MagicMock()
    mock_qdrant = MagicMock()
    mock_qdrant.get_client.return_value = MagicMock()
    app.state.db = mock_db
    app.state.qdrant = mock_qdrant
    return TestClient(app)


class TestHybridSearchEndpoint:
    def test_empty_query_returns_422(self) -> None:
        client = _make_client()
        response = client.post("/search/hybrid", json={"query": "  "})
        assert response.status_code == 422

    def test_top_k_below_minimum_returns_422(self) -> None:
        client = _make_client()
        response = client.post("/search/hybrid", json={"query": "test", "top_k": 0})
        assert response.status_code == 422

    def test_top_k_above_maximum_returns_422(self) -> None:
        client = _make_client()
        response = client.post("/search/hybrid", json={"query": "test", "top_k": 51})
        assert response.status_code == 422

    def test_negative_semantic_weight_returns_422(self) -> None:
        client = _make_client()
        response = client.post(
            "/search/hybrid",
            json={"query": "test", "semantic_weight": -0.1},
        )
        assert response.status_code == 422

    def test_returns_200_with_empty_results_when_no_index(self) -> None:
        client = _make_client()
        with (
            patch(
                "enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator."
                "HybridSearchOrchestrator.search",
                new_callable=AsyncMock,
                return_value=[],
            )
        ):
            response = client.post("/search/hybrid", json={"query": "machine learning"})
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []

    def test_returns_hybrid_result_shape(self) -> None:
        mock_result = HybridSearchResult(
            chunk_id="c1",
            document_id="doc1",
            document_path="/docs/doc1.md",
            chunk_index=0,
            content="Machine learning fundamentals.",
            rrf_score=0.025,
            keyword_rank=1,
            semantic_rank=2,
        )
        client = _make_client()
        with patch(
            "enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator."
            "HybridSearchOrchestrator.search",
            new_callable=AsyncMock,
            return_value=[mock_result],
        ):
            response = client.post("/search/hybrid", json={"query": "machine learning"})

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        item = data["results"][0]
        assert item["chunk_id"] == "c1"
        assert item["document_id"] == "doc1"
        assert item["rrf_score"] == pytest.approx(0.025)
        assert item["keyword_rank"] == 1
        assert item["semantic_rank"] == 2

    def test_workspace_path_forwarded(self) -> None:
        client = _make_client()
        captured: list = []

        async def mock_search(self_inner, query, top_k=10, workspace_path=None, **kw):
            captured.append(workspace_path)
            return []

        with patch.object(HybridSearchOrchestrator, "search", mock_search):
            client.post(
                "/search/hybrid",
                json={"query": "test", "workspace_path": "/my/workspace"},
            )

        assert captured == ["/my/workspace"]

    def test_default_weights_accepted(self) -> None:
        client = _make_client()
        with patch(
            "enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator."
            "HybridSearchOrchestrator.search",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = client.post("/search/hybrid", json={"query": "neural network"})
        assert response.status_code == 200

    def test_custom_weights_accepted(self) -> None:
        client = _make_client()
        with patch(
            "enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator."
            "HybridSearchOrchestrator.search",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = client.post(
                "/search/hybrid",
                json={"query": "test", "semantic_weight": 2.0, "keyword_weight": 0.5},
            )
        assert response.status_code == 200

    def test_null_keyword_rank_serialised_correctly(self) -> None:
        mock_result = HybridSearchResult(
            chunk_id="c1",
            document_id="doc1",
            document_path="/docs/doc1.md",
            chunk_index=0,
            content="Semantic-only result.",
            rrf_score=0.016,
            keyword_rank=None,
            semantic_rank=1,
        )
        client = _make_client()
        with patch(
            "enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator."
            "HybridSearchOrchestrator.search",
            new_callable=AsyncMock,
            return_value=[mock_result],
        ):
            response = client.post("/search/hybrid", json={"query": "semantic search"})
        item = response.json()["results"][0]
        assert item["keyword_rank"] is None
        assert item["semantic_rank"] == 1
