"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from enterprise_ai_companion.api.app import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_content_type():
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]


def test_unknown_route_returns_404():
    response = client.get("/nonexistent")
    assert response.status_code == 404
