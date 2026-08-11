"""
Orb window API endpoints.

Provides a lightweight single-turn query endpoint used by the orb inline
query overlay. Unlike the full conversation endpoint, this is stateless —
no message history is persisted, no conversation ID is required.
"""

import logging
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.ai.llm_client import chat_complete

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orb", tags=["orb"])


class OrbQueryRequest(BaseModel):
    query: str


class OrbQueryResponse(BaseModel):
    response: str


@router.post("/query", response_model=OrbQueryResponse)
async def orb_query(request: Request, body: OrbQueryRequest) -> Any:
    """
    Single-turn LLM query for the orb inline overlay.

    Optionally enriches the response with RAG context if the search service
    is available on app.state. Returns a plain text answer suitable for the
    compact overlay (no citations, no markdown headers).
    """
    query = body.query.strip()
    if not query:
        return OrbQueryResponse(response="")

    context_text = ""

    # Best-effort RAG: search for relevant context without blocking on errors.
    try:
        search_service = getattr(request.app.state, "search_service", None)
        if search_service is not None:
            results = await search_service.hybrid_search(
                query=query,
                top_k=3,
                workspace_path=None,
                semantic_weight=0.7,
                keyword_weight=0.3,
            )
            if results:
                snippets = [r.content[:300] for r in results[:3]]
                context_text = "\n\n".join(snippets)
    except Exception:
        logger.debug("Orb RAG context fetch failed — proceeding without context")

    if context_text:
        system_content = (
            "You are a helpful AI assistant embedded in a desktop widget. "
            "Answer concisely — the response will appear in a compact overlay. "
            "Use at most 3–4 sentences. Do not use markdown headers or lists.\n\n"
            f"Relevant context from the user's knowledge base:\n{context_text}"
        )
    else:
        system_content = (
            "You are a helpful AI assistant embedded in a desktop widget. "
            "Answer concisely — the response will appear in a compact overlay. "
            "Use at most 3–4 sentences. Do not use markdown headers or lists."
        )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": query},
    ]

    try:
        response_text = await chat_complete(messages, max_tokens=256, temperature=0.4)
    except Exception as exc:
        logger.error("Orb query LLM call failed: %s", exc)
        return OrbQueryResponse(response="Sorry, I couldn't process that query right now.")

    return OrbQueryResponse(response=response_text)
