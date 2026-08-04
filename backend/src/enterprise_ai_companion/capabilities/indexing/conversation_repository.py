"""Conversation persistence repository.

Provides async CRUD operations over the conversations and messages tables.
All methods accept an aiosqlite connection so they remain testable with an
in-memory database.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Optional


@dataclass(frozen=True)
class Message:
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    status: Literal["complete", "streaming", "error"]
    created_at: str


@dataclass(frozen=True)
class ConversationSummary:
    id: str
    created_at: str
    message_count: int


@dataclass(frozen=True)
class ConversationMemoryState:
    """Memory state for a single conversation, read from the conversations table."""

    conversation_id: str
    turn_count: int
    summary: Optional[str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConversationRepository:
    """Async repository for conversation and message persistence."""

    def __init__(self, conn) -> None:  # type: ignore[no-untyped-def]
        self._conn = conn

    # ── Conversations ─────────────────────────────────────────────────────────

    async def get_or_create_conversation(self, conversation_id: str) -> str:
        """Return the conversation id, creating the row if it does not exist."""
        async with self._conn.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            await self._conn.execute(
                "INSERT INTO conversations (id, created_at) VALUES (?, ?)",
                (conversation_id, _utc_now()),
            )
            await self._conn.commit()

        return conversation_id

    async def list_conversations(self) -> list[ConversationSummary]:
        """Return all conversations, most recent first, with their message count."""
        async with self._conn.execute(
            """
            SELECT c.id, c.created_at, COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()

        return [
            ConversationSummary(
                id=row["id"],
                created_at=row["created_at"],
                message_count=row["message_count"],
            )
            for row in rows
        ]

    # ── Messages ──────────────────────────────────────────────────────────────

    async def save_message(
        self,
        message_id: str,
        conversation_id: str,
        role: Literal["user", "assistant"],
        content: str,
        status: Literal["complete", "streaming", "error"] = "complete",
    ) -> Message:
        """Persist a message, creating the parent conversation if needed."""
        await self.get_or_create_conversation(conversation_id)

        created_at = _utc_now()
        await self._conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                content    = excluded.content,
                status     = excluded.status
            """,
            (message_id, conversation_id, role, content, status, created_at),
        )
        await self._conn.commit()

        return Message(
            id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            status=status,
            created_at=created_at,
        )

    async def load_conversation(self, conversation_id: str) -> list[Message]:
        """Return all messages for a conversation, oldest first."""
        async with self._conn.execute(
            """
            SELECT id, conversation_id, role, content, status, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        ) as cursor:
            rows = await cursor.fetchall()

        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    # ── Memory ────────────────────────────────────────────────────────────────

    async def get_memory_state(self, conversation_id: str) -> ConversationMemoryState:
        """Return the turn_count and summary for a conversation.

        Creates the conversation row first if it does not exist so this method
        is always safe to call regardless of prior persistence state.
        """
        await self.get_or_create_conversation(conversation_id)

        async with self._conn.execute(
            "SELECT turn_count, summary FROM conversations WHERE id = ?",
            (conversation_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return ConversationMemoryState(
                conversation_id=conversation_id, turn_count=0, summary=None
            )

        return ConversationMemoryState(
            conversation_id=conversation_id,
            turn_count=row["turn_count"],
            summary=row["summary"],
        )

    async def increment_turn_count(self, conversation_id: str) -> int:
        """Atomically increment turn_count and return the new value."""
        await self._conn.execute(
            "UPDATE conversations SET turn_count = turn_count + 1 WHERE id = ?",
            (conversation_id,),
        )
        await self._conn.commit()

        async with self._conn.execute(
            "SELECT turn_count FROM conversations WHERE id = ?",
            (conversation_id,),
        ) as cursor:
            row = await cursor.fetchone()

        return int(row["turn_count"]) if row else 0

    async def save_summary(self, conversation_id: str, summary: str) -> None:
        """Persist a compressed summary for the conversation."""
        await self._conn.execute(
            "UPDATE conversations SET summary = ? WHERE id = ?",
            (summary, conversation_id),
        )
        await self._conn.commit()

    async def load_oldest_messages(
        self, conversation_id: str, limit: int
    ) -> list[Message]:
        """Return up to `limit` messages, oldest first, for summarisation."""
        async with self._conn.execute(
            """
            SELECT id, conversation_id, role, content, status, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (conversation_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()

        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
