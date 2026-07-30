"""Tests for the /graph API endpoints using NullGraphProvider injected into app.state."""

import pytest
from fastapi.testclient import TestClient

from enterprise_ai_companion.api.app import app
from enterprise_ai_companion.capabilities.graph.null_graph_provider import NullGraphProvider


def _make_client() -> TestClient:
    """Return a TestClient with NullGraphProvider pre-loaded into app.state."""
    app.state.graph = NullGraphProvider()
    return TestClient(app)


class TestGraphHealth:
    def test_returns_200(self) -> None:
        client = _make_client()
        response = client.get("/graph/health")
        assert response.status_code == 200

    def test_null_provider_is_connected(self) -> None:
        client = _make_client()
        data = client.get("/graph/health").json()
        assert data["connected"] is True
        assert data["provider"] == "NullGraphProvider"


class TestGetGraphEntity:
    def test_unknown_entity_returns_404(self) -> None:
        client = _make_client()
        response = client.get("/graph/entity/NonExistentEntity")
        assert response.status_code == 404

    def test_empty_entity_name_returns_422(self) -> None:
        client = _make_client()
        response = client.get("/graph/entity/%20")  # URL-encoded space
        assert response.status_code == 422

    def test_depth_out_of_range_returns_422(self) -> None:
        client = _make_client()
        response = client.get("/graph/entity/Volvo?depth=5")
        assert response.status_code == 422

    def test_depth_zero_returns_422(self) -> None:
        client = _make_client()
        response = client.get("/graph/entity/Volvo?depth=0")
        assert response.status_code == 422
