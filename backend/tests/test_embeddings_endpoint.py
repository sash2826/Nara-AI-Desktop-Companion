"""Tests for the POST /embeddings FastAPI endpoint.

Uses FastAPI's TestClient (synchronous). The actual BGE-M3 model is mocked to
keep these tests fast and CI-friendly without requiring the model download.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from enterprise_ai_companion.api.app import app
from enterprise_ai_companion.capabilities.indexing.embedding_service import EMBEDDING_DIM

client = TestClient(app)

FAKE_VECTOR = [0.1] * EMBEDDING_DIM


def _patch_service(vector: list[float] = FAKE_VECTOR):
    """Patch the EmbeddingService singleton used by the router."""
    mock = MagicMock()
    mock.generate.return_value = vector
    return patch("enterprise_ai_companion.api.routers.embeddings._service", mock)


class TestEmbeddingsEndpoint:
    def test_returns_200_with_valid_text(self) -> None:
        with _patch_service():
            response = client.post("/embeddings", json={"text": "hello world"})
        assert response.status_code == 200

    def test_response_contains_embedding_and_dim(self) -> None:
        with _patch_service():
            response = client.post("/embeddings", json={"text": "test"})
        data = response.json()
        assert "embedding" in data
        assert "dim" in data

    def test_embedding_has_correct_length(self) -> None:
        with _patch_service():
            response = client.post("/embeddings", json={"text": "test"})
        data = response.json()
        assert data["dim"] == EMBEDDING_DIM
        assert len(data["embedding"]) == EMBEDDING_DIM

    def test_rejects_empty_text(self) -> None:
        response = client.post("/embeddings", json={"text": ""})
        assert response.status_code == 422

    def test_rejects_whitespace_only_text(self) -> None:
        response = client.post("/embeddings", json={"text": "   "})
        assert response.status_code == 422

    def test_rejects_missing_text_field(self) -> None:
        response = client.post("/embeddings", json={})
        assert response.status_code == 422

    def test_service_error_returns_500(self) -> None:
        mock = MagicMock()
        mock.generate.side_effect = RuntimeError("model exploded")
        with patch("enterprise_ai_companion.api.routers.embeddings._service", mock):
            response = client.post("/embeddings", json={"text": "valid"})
        assert response.status_code == 500
