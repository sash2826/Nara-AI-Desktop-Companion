"""
Orb window API endpoints.

Provides a lightweight single-turn query endpoint used by the orb inline
query overlay. Unlike the full conversation endpoint, this is stateless —
no message history is persisted, no conversation ID is required.

RAG context is retrieved via HybridSearchOrchestrator, the same pipeline
used by the main search router, so the orb and the main app share the same
knowledge base.
"""

import logging
import re
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from enterprise_ai_companion.capabilities.ai.llm_client import chat_complete
from enterprise_ai_companion.capabilities.indexing.embedding_service import EmbeddingService
from enterprise_ai_companion.capabilities.retrieval.hybrid_orchestrator import HybridSearchOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orb", tags=["orb"])

# Minimum word count before we bother hitting the search pipeline.
# Greetings and very short queries can't produce meaningful RRF scores.
_MIN_QUERY_WORDS_FOR_RAG: int = 3

# Conversational patterns that should never trigger RAG.
_CONVERSATIONAL_RE = re.compile(
    r"^\s*(hi+|hello+|hey+|howdy|greetings?|good\s+(morning|afternoon|evening|day)|"
    r"thanks?|thank\s+you|thx|cheers|bye+|goodbye|ok+|okay|sure|yes|no|yep|nope|"
    r"who\s+are\s+you|what\s+are\s+you|help)\s*[.!?]?\s*$",
    re.IGNORECASE,
)


class OrbQueryRequest(BaseModel):
    query: str


class OrbSourceItem(BaseModel):
    path: str
    name: str


class OrbQueryResponse(BaseModel):
    response: str
    sources: list[OrbSourceItem] = []


@router.post("/query", response_model=OrbQueryResponse)
async def orb_query(request: Request, body: OrbQueryRequest) -> Any:
    """
    Single-turn LLM query for the orb inline overlay.

    Runs the query through the same hybrid search pipeline (HybridSearchOrchestrator)
    as the main app. Returns a concise answer plus a deduplicated list of source
    file paths so the overlay can offer direct open buttons.
    """
    query = body.query.strip()
    if not query:
        return OrbQueryResponse(response="", sources=[])

    context_text = ""
    sources: list[OrbSourceItem] = []

    # RAG: skip for conversational queries and very short inputs that cannot
    # meaningfully match indexed documents.
    word_count = len(query.split())
    is_conversational = bool(_CONVERSATIONAL_RE.match(query)) or word_count < _MIN_QUERY_WORDS_FOR_RAG

    if not is_conversational:
        try:
            preprocessor = getattr(request.app.state, "preprocessor", None)
            search_text = preprocessor.process(query).search_text if preprocessor else query

            orchestrator = HybridSearchOrchestrator(
                conn=request.app.state.db,
                qdrant_client=request.app.state.qdrant.get_client(),
                embedding_service=EmbeddingService(),
            )
            results = await orchestrator.search(
                query=search_text,
                top_k=20,
                workspace_path=None,
                semantic_weight=0.7,
                keyword_weight=0.3,
            )
            if results:
                snippets = []
                seen_paths: set[str] = set()
                for r in results[:8]:
                    path = r.document_path
                    parts = path.replace("\\", "/").split("/")
                    # Include parent folder so LLM sees project context:
                    # "Atlas-Workplace/Project_Overview.pdf" not just "Project_Overview.pdf"
                    label = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
                    name = parts[-1]
                    snippets.append(f"[{label}]\n{r.content[:600]}")
                    if path not in seen_paths:
                        seen_paths.add(path)
                        sources.append(OrbSourceItem(path=path, name=name))
                context_text = "\n\n".join(snippets[:5])
        except Exception:
            logger.debug("Orb RAG context fetch failed — proceeding without context")

    if context_text:
        system_content = (
            "You are a helpful AI assistant with access to the user's indexed knowledge base.\n"
            "The context below contains real excerpts from the user's files.\n"
            "Rules:\n"
            "- Name the specific document title and project (e.g. 'Atlas Workplace — Access Control Plan').\n"
            "- Use the exact names, people, document IDs, and terms as they appear in the sources.\n"
            "- If the source includes a document ID (e.g. 'AW-DOC-004'), mention it.\n"
            "- Answer concisely — 3–4 sentences max. No markdown headers or bullet lists.\n\n"
            f"Indexed files context:\n{context_text}"
        )
    else:
        system_content = (
            "You are a helpful AI assistant with access to the user's indexed knowledge base. "
            "No relevant files were found for this query. "
            "Answer concisely (3–4 sentences max). No markdown headers or bullet lists."
        )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": query},
    ]

    try:
        response_text = await chat_complete(messages, max_tokens=256, temperature=0.4)
    except Exception as exc:
        logger.error("Orb query LLM call failed: %s", exc)
        return OrbQueryResponse(
            response="Sorry, I couldn't process that query right now.", sources=[]
        )

    return OrbQueryResponse(response=response_text, sources=sources)
