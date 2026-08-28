"""Dashboard statistics and AI-suggested query endpoints."""

from __future__ import annotations

import logging
from typing import Any

import socket

import aiosqlite
from fastapi import APIRouter, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.ai.llm_client import chat_complete
from enterprise_ai_companion.infrastructure.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class RecentFile(BaseModel):
    id: str
    file_path: str
    workspace_path: str
    chunk_count: int
    char_count: int
    indexed_at: str


class DashboardStats(BaseModel):
    document_count: int
    chunk_count: int
    total_chars: int
    conversation_count: int
    watched_folder_count: int
    indexing_error_count: int
    recent_files: list[RecentFile]


class SuggestionsRequest(BaseModel):
    recent_file_paths: list[str]
    max_suggestions: int = 5


class SuggestionsResponse(BaseModel):
    suggestions: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_stats(conn: aiosqlite.Connection) -> DashboardStats:
    """Run all aggregate queries and return a DashboardStats payload."""
    conn.row_factory = aiosqlite.Row

    async with conn.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(SUM(chunk_count),0) AS chunks, "
        "COALESCE(SUM(char_count),0) AS chars FROM documents"
    ) as cur:
        row = await cur.fetchone()
        document_count = row["cnt"]
        chunk_count = row["chunks"]
        total_chars = row["chars"]

    async with conn.execute("SELECT COUNT(*) AS cnt FROM conversations") as cur:
        row = await cur.fetchone()
        conversation_count = row["cnt"]

    async with conn.execute("SELECT COUNT(*) AS cnt FROM watched_folders") as cur:
        row = await cur.fetchone()
        watched_folder_count = row["cnt"]

    # Exclude stale errors for files that have since been indexed successfully.
    async with conn.execute(
        "SELECT COUNT(*) AS cnt FROM indexing_errors "
        "WHERE file_path NOT IN (SELECT file_path FROM documents)"
    ) as cur:
        row = await cur.fetchone()
        indexing_error_count = row["cnt"]

    async with conn.execute(
        "SELECT id, file_path, workspace_path, chunk_count, char_count, indexed_at "
        "FROM documents ORDER BY indexed_at DESC LIMIT 5"
    ) as cur:
        rows = await cur.fetchall()
        recent_files = [
            RecentFile(
                id=r["id"],
                file_path=r["file_path"],
                workspace_path=r["workspace_path"],
                chunk_count=r["chunk_count"],
                char_count=r["char_count"],
                indexed_at=r["indexed_at"],
            )
            for r in rows
        ]

    return DashboardStats(
        document_count=document_count,
        chunk_count=chunk_count,
        total_chars=total_chars,
        conversation_count=conversation_count,
        watched_folder_count=watched_folder_count,
        indexing_error_count=indexing_error_count,
        recent_files=recent_files,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("", response_model=DashboardStats)
async def get_stats(request: Request) -> DashboardStats:
    """Return aggregated workspace statistics for the home dashboard."""
    conn: aiosqlite.Connection = request.app.state.db
    return await _get_stats(conn)


@router.post("/suggestions", response_model=SuggestionsResponse)
async def get_suggested_queries(body: SuggestionsRequest) -> SuggestionsResponse:
    """Return AI-generated search query suggestions based on recent file names.

    The client caches the response for 1 hour — this endpoint is not called
    on every page load.
    """
    if not body.recent_file_paths:
        return SuggestionsResponse(suggestions=[])

    # Skip the LLM call entirely when no subscription key is configured — avoids
    # spurious DNS/network errors logged when the user hasn't entered a key yet.
    if not get_config().apim_subscription_key:
        return SuggestionsResponse(suggestions=[])

    file_list = "\n".join(f"- {p}" for p in body.recent_file_paths[:10])
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a search assistant. Given a list of recently indexed file paths, "
                "suggest concise, useful natural-language search queries the user might want "
                "to run against those documents. Return only a JSON array of strings — "
                "no markdown, no explanation."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Recently indexed files:\n{file_list}\n\n"
                f"Suggest {body.max_suggestions} useful search queries for these documents."
            ),
        },
    ]

    try:
        raw = await chat_complete(messages, max_tokens=256, temperature=0.4)
        # Strip markdown fences if the model wraps the JSON
        clean = raw.strip().strip("```json").strip("```").strip()
        import json
        suggestions: list[str] = json.loads(clean)
        if not isinstance(suggestions, list):
            raise ValueError("LLM did not return a JSON array")
        suggestions = [str(s) for s in suggestions[: body.max_suggestions]]
    except (socket.gaierror, OSError) as exc:
        # DNS resolution / network unreachable — expected when not on VPN.
        logger.debug("[stats] suggestion generation skipped — network unreachable: %s", exc)
        suggestions = []
    except Exception as exc:
        logger.warning("[stats] suggestion generation failed: %s", exc)
        suggestions = []

    return SuggestionsResponse(suggestions=suggestions)
