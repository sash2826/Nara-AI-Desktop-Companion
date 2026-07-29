"""Conversations router — conversation and message persistence endpoints."""

from __future__ import annotations

from typing import Annotated, Literal

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from enterprise_ai_companion.capabilities.indexing.conversation_repository import (
    ConversationRepository,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# ── Dependency ────────────────────────────────────────────────────────────────


def get_db(request: Request) -> aiosqlite.Connection:
    """Extract the shared database connection from app state."""
    conn = request.app.state.db
    if conn is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return conn


DB = Annotated[aiosqlite.Connection, Depends(get_db)]


# ── Request / response models ─────────────────────────────────────────────────


class SaveMessageRequest(BaseModel):
    message_id: str
    role: Literal["user", "assistant"]
    content: str
    status: Literal["complete", "streaming", "error"] = "complete"

    @field_validator("message_id", "content")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field must not be empty")
        return v


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    status: Literal["complete", "streaming", "error"]
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    messages: list[MessageResponse]


class ConversationSummaryResponse(BaseModel):
    id: str
    created_at: str
    message_count: int


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[ConversationSummaryResponse])
async def list_conversations(db: DB) -> list[ConversationSummaryResponse]:
    """List all conversations, most recent first."""
    repo = ConversationRepository(db)
    summaries = await repo.list_conversations()
    return [
        ConversationSummaryResponse(
            id=s.id, created_at=s.created_at, message_count=s.message_count
        )
        for s in summaries
    ]


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def save_message(
    conversation_id: str,
    body: SaveMessageRequest,
    db: DB,
) -> MessageResponse:
    """Persist a message, creating the conversation row if it does not exist."""
    if not conversation_id.strip():
        raise HTTPException(status_code=422, detail="conversation_id must not be empty")

    repo = ConversationRepository(db)
    try:
        msg = await repo.save_message(
            message_id=body.message_id,
            conversation_id=conversation_id,
            role=body.role,
            content=body.content,
            status=body.status,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        role=msg.role,
        content=msg.content,
        status=msg.status,
        created_at=msg.created_at,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def load_conversation(conversation_id: str, db: DB) -> ConversationResponse:
    """Return all messages for a conversation, oldest first."""
    repo = ConversationRepository(db)
    messages = await repo.load_conversation(conversation_id)
    return ConversationResponse(
        id=conversation_id,
        messages=[
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                status=m.status,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )
