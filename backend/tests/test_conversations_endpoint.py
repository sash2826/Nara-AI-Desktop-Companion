"""Tests for the conversations FastAPI endpoints using an in-memory database."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from enterprise_ai_companion.api.app import app
from enterprise_ai_companion.capabilities.indexing.conversation_repository import (
    ConversationRepository,
    Message,
    ConversationSummary,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _mock_db_app():
    """Return a TestClient with a mock db in app.state."""
    mock_db = MagicMock()
    app.state.db = mock_db
    return TestClient(app), mock_db


def _make_message(**kwargs) -> Message:
    defaults = dict(
        id="msg-1",
        conversation_id="conv-1",
        role="user",
        content="hello",
        status="complete",
        created_at="2026-07-29T12:00:00+00:00",
    )
    defaults.update(kwargs)
    return Message(**defaults)


# ── POST /conversations/{id}/messages ─────────────────────────────────────────


class TestSaveMessageEndpoint:
    def test_saves_message_and_returns_200(self) -> None:
        client, mock_db = _mock_db_app()
        saved = _make_message()
        repo_mock = MagicMock(spec=ConversationRepository)
        repo_mock.save_message = AsyncMock(return_value=saved)

        import enterprise_ai_companion.api.routers.conversations as conv_module

        original = conv_module.ConversationRepository
        conv_module.ConversationRepository = lambda _db: repo_mock  # type: ignore[assignment]
        try:
            response = client.post(
                "/conversations/conv-1/messages",
                json={"message_id": "msg-1", "role": "user", "content": "hello"},
            )
        finally:
            conv_module.ConversationRepository = original

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "msg-1"
        assert data["role"] == "user"

    def test_rejects_empty_content(self) -> None:
        client, _ = _mock_db_app()
        response = client.post(
            "/conversations/conv-1/messages",
            json={"message_id": "msg-1", "role": "user", "content": ""},
        )
        assert response.status_code == 422

    def test_rejects_empty_message_id(self) -> None:
        client, _ = _mock_db_app()
        response = client.post(
            "/conversations/conv-1/messages",
            json={"message_id": "", "role": "user", "content": "hello"},
        )
        assert response.status_code == 422

    def test_rejects_invalid_role(self) -> None:
        client, _ = _mock_db_app()
        response = client.post(
            "/conversations/conv-1/messages",
            json={"message_id": "m1", "role": "system", "content": "hello"},
        )
        assert response.status_code == 422


# ── GET /conversations/{id} ───────────────────────────────────────────────────


class TestLoadConversationEndpoint:
    def test_returns_messages_for_known_conversation(self) -> None:
        client, mock_db = _mock_db_app()
        msgs = [_make_message(id="m1"), _make_message(id="m2", role="assistant")]
        repo_mock = MagicMock(spec=ConversationRepository)
        repo_mock.load_conversation = AsyncMock(return_value=msgs)

        import enterprise_ai_companion.api.routers.conversations as conv_module

        original = conv_module.ConversationRepository
        conv_module.ConversationRepository = lambda _db: repo_mock  # type: ignore[assignment]
        try:
            response = client.get("/conversations/conv-1")
        finally:
            conv_module.ConversationRepository = original

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "conv-1"
        assert len(data["messages"]) == 2

    def test_returns_empty_messages_for_unknown_conversation(self) -> None:
        client, mock_db = _mock_db_app()
        repo_mock = MagicMock(spec=ConversationRepository)
        repo_mock.load_conversation = AsyncMock(return_value=[])

        import enterprise_ai_companion.api.routers.conversations as conv_module

        original = conv_module.ConversationRepository
        conv_module.ConversationRepository = lambda _db: repo_mock  # type: ignore[assignment]
        try:
            response = client.get("/conversations/conv-unknown")
        finally:
            conv_module.ConversationRepository = original

        assert response.status_code == 200
        assert response.json()["messages"] == []


# ── GET /conversations ────────────────────────────────────────────────────────


class TestListConversationsEndpoint:
    def test_returns_list(self) -> None:
        client, mock_db = _mock_db_app()
        summaries = [ConversationSummary(id="conv-1", created_at="2026-07-29T12:00:00+00:00", message_count=2)]
        repo_mock = MagicMock(spec=ConversationRepository)
        repo_mock.list_conversations = AsyncMock(return_value=summaries)

        import enterprise_ai_companion.api.routers.conversations as conv_module

        original = conv_module.ConversationRepository
        conv_module.ConversationRepository = lambda _db: repo_mock  # type: ignore[assignment]
        try:
            response = client.get("/conversations")
        finally:
            conv_module.ConversationRepository = original

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "conv-1"
        assert data[0]["message_count"] == 2
