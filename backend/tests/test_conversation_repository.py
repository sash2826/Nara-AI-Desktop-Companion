"""Unit tests for ConversationRepository using an in-memory SQLite database."""

import pytest
import aiosqlite

from enterprise_ai_companion.capabilities.indexing.conversation_repository import (
    ConversationRepository,
)
from enterprise_ai_companion.infrastructure.database import open_db


@pytest.fixture
async def db():
    """In-memory SQLite database with schema applied, closed after each test."""
    import os

    os.environ["EAC_DB_PATH"] = ":memory:"
    conn = await open_db()
    yield conn
    await conn.close()
    del os.environ["EAC_DB_PATH"]


@pytest.fixture
async def repo(db: aiosqlite.Connection) -> ConversationRepository:
    return ConversationRepository(db)


class TestGetOrCreateConversation:
    async def test_creates_new_conversation(self, repo: ConversationRepository) -> None:
        cid = await repo.get_or_create_conversation("conv-1")
        assert cid == "conv-1"

    async def test_idempotent_on_second_call(self, repo: ConversationRepository) -> None:
        await repo.get_or_create_conversation("conv-1")
        cid = await repo.get_or_create_conversation("conv-1")
        assert cid == "conv-1"


class TestSaveMessage:
    async def test_saves_and_returns_message(self, repo: ConversationRepository) -> None:
        msg = await repo.save_message("msg-1", "conv-1", "user", "hello", "complete")
        assert msg.id == "msg-1"
        assert msg.conversation_id == "conv-1"
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.status == "complete"
        assert msg.created_at  # non-empty ISO timestamp

    async def test_auto_creates_conversation(self, repo: ConversationRepository) -> None:
        # No explicit get_or_create_conversation call — save_message handles it.
        msg = await repo.save_message("msg-1", "conv-new", "user", "hi", "complete")
        assert msg.conversation_id == "conv-new"

    async def test_upsert_updates_content_on_duplicate_id(
        self, repo: ConversationRepository
    ) -> None:
        await repo.save_message("msg-1", "conv-1", "user", "original", "complete")
        await repo.save_message("msg-1", "conv-1", "user", "updated", "complete")
        messages = await repo.load_conversation("conv-1")
        assert messages[0].content == "updated"

    async def test_saves_assistant_role(self, repo: ConversationRepository) -> None:
        msg = await repo.save_message("msg-1", "conv-1", "assistant", "reply", "complete")
        assert msg.role == "assistant"


class TestLoadConversation:
    async def test_returns_empty_list_for_unknown_conversation(
        self, repo: ConversationRepository
    ) -> None:
        messages = await repo.load_conversation("conv-unknown")
        assert messages == []

    async def test_returns_messages_oldest_first(self, repo: ConversationRepository) -> None:
        await repo.save_message("msg-1", "conv-1", "user", "first", "complete")
        await repo.save_message("msg-2", "conv-1", "assistant", "second", "complete")
        messages = await repo.load_conversation("conv-1")
        assert len(messages) == 2
        assert messages[0].id == "msg-1"
        assert messages[1].id == "msg-2"

    async def test_does_not_return_messages_from_other_conversations(
        self, repo: ConversationRepository
    ) -> None:
        await repo.save_message("msg-1", "conv-A", "user", "a", "complete")
        await repo.save_message("msg-2", "conv-B", "user", "b", "complete")
        messages = await repo.load_conversation("conv-A")
        assert len(messages) == 1
        assert messages[0].id == "msg-1"


class TestListConversations:
    async def test_returns_empty_when_no_conversations(
        self, repo: ConversationRepository
    ) -> None:
        summaries = await repo.list_conversations()
        assert summaries == []

    async def test_returns_all_conversations(self, repo: ConversationRepository) -> None:
        await repo.get_or_create_conversation("conv-1")
        await repo.get_or_create_conversation("conv-2")
        summaries = await repo.list_conversations()
        assert len(summaries) == 2

    async def test_message_count_correct(self, repo: ConversationRepository) -> None:
        await repo.save_message("m1", "conv-1", "user", "hi", "complete")
        await repo.save_message("m2", "conv-1", "assistant", "hello", "complete")
        summaries = await repo.list_conversations()
        assert summaries[0].message_count == 2
