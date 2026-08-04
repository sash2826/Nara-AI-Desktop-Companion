# Phase 04: AI Context & Intelligence

**Phase:** 04

**Status:** In Progress (Epic 4.4 complete; Epics 4.0–4.3, 4.5 in Session A)

**Estimated Duration:** 4-6 Days

---

# Purpose

Phase 04 elevates the Enterprise AI Companion from a retrieval-augmented chatbot into a genuinely context-aware AI assistant.

Phase 00 established the conversation interface. Phase 01 connected the LLM. Phase 02 built the search and indexing infrastructure. Phase 03 surfaced workspace management in the UI. What is still missing is the intelligence layer that ties them together — the AI currently receives raw retrieved chunks but has no understanding of the user's current context, recent activity, workspace structure, or the quality of retrieved evidence.

At the completion of this phase, the assistant should:

- Understand what the user is currently working on (active workspace, recent documents)
- Retrieve relevant context intelligently before every response
- Cite sources accurately and consistently
- Summarise and reason across multiple documents rather than returning isolated chunks
- Provide a Home page dashboard that reflects the user's knowledge state

---

# Objectives

Upon completion of this phase, the application should provide:

* Intelligent context assembly before every LLM call
* Multi-document reasoning across retrieved chunks
* Accurate, consistent source citation in every response
* Conversation memory — the assistant recalls what was discussed earlier in the session
* Active workspace awareness — the assistant scopes retrieval to the user's current folder
* Document summarisation on demand
* Home page dashboard (recent documents, indexed stats, suggested queries)
* Retrieval quality scoring and filtering (drop low-confidence chunks)
* Streaming response improvements (token-level status, cancellation)

---

# Prerequisites

Before beginning this phase:

* Phase 00 must be completed.
* Phase 01 must be completed.
* Phase 02 must be completed.
* Phase 03 must be completed.
* LLM provider must be operational.
* Semantic and keyword search must be functional.
* Indexing pipeline must be stable.

---

# Epic 4.0 — Context Assembly Service

The current pipeline retrieves chunks and injects them verbatim into the system prompt. This epic replaces that with a structured `ContextAssembler` that builds a rich, ranked context payload before every LLM call.

## Deliverables

### `ContextAssembler` (`capabilities/ai/context_assembler.py`)

Responsible for producing a `ContextPayload` from the current conversation state and workspace:

```python
@dataclass
class ContextPayload:
    retrieved_chunks: list[RankedChunk]     # top-k semantically ranked
    active_workspace: str | None            # current folder scope
    recent_documents: list[str]             # recently indexed file paths
    conversation_summary: str | None        # compressed prior turns
    total_tokens_estimate: int
```

### Retrieval quality filtering

- Chunks below a configurable `min_score` threshold (default: 0.45) are excluded
- Deduplication: chunks with >85% content overlap are collapsed to the highest-scoring representative
- Token budget enforcement: chunks are trimmed from the bottom of the ranked list to stay within the LLM context window

### Active workspace scoping

- The assistant scopes retrieval to the user's active watched folder by default
- A "search all workspaces" override remains available via conversation context

---

# Epic 4.1 — Conversation Memory

The assistant currently has no memory of prior turns beyond the raw message list. This epic adds session-level memory so the assistant can reference earlier conclusions without re-deriving them.

## Deliverables

### Conversation summariser

- After every 10 assistant turns, the oldest 8 turns are summarised by the LLM into a compressed `conversation_summary` string
- The summary is stored in the conversation record in SQLite
- The summary is prepended to the system message on subsequent turns, ahead of retrieved context

### Turn count tracking

- `conversations` table gains a `turn_count` integer column (migration 005)
- Incremented on every assistant message save

---

# Epic 4.2 — Multi-Document Reasoning

Single-chunk retrieval is insufficient for questions that span multiple documents or require synthesis. This epic enables the assistant to reason across a curated set of chunks rather than treating each in isolation.

## Deliverables

### Chunk reranking

A cross-encoder reranking step is applied after initial retrieval:

- Initial retrieval fetches top 20 candidates via hybrid search (RRF)
- A lightweight cross-encoder scores each candidate against the query
- Top 5 reranked chunks are passed to the LLM

Initial implementation may use a simple similarity-based heuristic reranker (cosine between query embedding and chunk embedding with position bias) if a cross-encoder model is too heavy for the corporate environment. The interface must be abstracted so a proper cross-encoder can be substituted.

### Synthesis prompt template

The system message is restructured to explicitly instruct the LLM to:

1. Synthesise across all provided chunks (not just the most similar one)
2. Identify and surface conflicting information across documents
3. Distinguish between information found in the knowledge base vs. general knowledge

---

# Epic 4.3 — Source Citation

Source citation was partially implemented in Phase 03. This epic makes it reliable and consistent.

## Deliverables

### Citation enforcement

- System prompt instructs the LLM to cite every factual claim with the exact file path in brackets: `[C:\path\to\file.pdf]`
- Post-processing pass on the streamed response strips any `[citation needed]` or uncited claims and flags them
- Frontend `FilePathChip` already handles clickable rendering — no frontend change required

### Citation confidence display

Each citation chip in the chat UI gains a hover tooltip showing:
- File name and path
- Chunk index that was retrieved
- Retrieval score (e.g. "87% match")

This requires passing citation metadata alongside the message content.

---

# Epic 4.4 — Home Page Dashboard

The `HomePage` is currently a placeholder. This epic implements a meaningful dashboard that gives the user an at-a-glance view of their knowledge state.

## Deliverables

### Home page sections

| Section | Content |
|---|---|
| **Quick stats** | Total indexed documents, total chunks, last indexed time |
| **Recent documents** | Last 5 files indexed, clickable to open |
| **Active workspace** | Current watched folder, file count, index health |
| **Suggested queries** | 3–5 auto-generated questions based on recently indexed content |
| **Quick search** | Search input that navigates to Search page with the query pre-filled |

### Suggested queries generation

On each app start (or when the user navigates to Home), the backend generates 3–5 suggested questions by:

1. Sampling recent chunk content from SQLite
2. Asking the LLM to generate diverse questions a user might ask about that content
3. Caching the result for 1 hour to avoid repeated LLM calls

New backend endpoint: `GET /ai/suggested-queries?workspace_path=...`

---

# Epic 4.5 — Streaming & Cancellation Improvements

## Deliverables

### Per-token status indicator

The streaming cursor in `AssistantBubble` is replaced with a live token counter: "Generating… (142 tokens)" that updates as chunks arrive.

### Cancellable generation

- A stop button appears in `AssistantHeader` during streaming
- Clicking it calls `AbortController.abort()` on the fetch stream
- The partial response is preserved in the message with `status: "cancelled"` and a visual indicator

---

# Architecture Changes

## New files

```
backend/src/enterprise_ai_companion/capabilities/ai/
├── context_assembler.py          # Epic 4.0
├── conversation_memory.py        # Epic 4.1
├── reranker.py                   # Epic 4.2
└── suggested_queries_service.py  # Epic 4.4

backend/src/enterprise_ai_companion/api/routers/
└── ai_context.py                 # /ai/suggested-queries endpoint

database/migrations/
└── 005_conversation_memory.sql   # turn_count + summary columns

frontend/src/pages/
└── HomePage.tsx                  # Epic 4.4 (replaces placeholder)

frontend/src/components/home/
├── QuickStats.tsx
├── RecentDocuments.tsx
├── SuggestedQueries.tsx
└── ActiveWorkspaceCard.tsx

frontend/src/components/assistant/
└── CitationChip.tsx              # hover tooltip with match score
```

## Modified files

```
backend/src/.../capabilities/ai/llm_client.py         # cancellation support
backend/src/.../api/routers/conversations.py          # turn_count increment
frontend/src/hooks/useConversation.ts                 # context assembler integration
frontend/src/services/conversation/ConversationService.ts  # reranked context
frontend/src/components/assistant/AssistantBubble.tsx # token counter
frontend/src/components/assistant/AssistantHeader.tsx # stop button
frontend/src/components/assistant/MessageBubble.tsx   # CitationChip
```

---

# Completion Criteria

This phase is complete when:

- [ ] Every LLM response is grounded in retrieved workspace context (not general knowledge alone)
- [ ] Source citations appear in every response that uses indexed documents
- [ ] File path chips in responses are clickable and open the correct file
- [ ] Conversation memory summarises older turns and the summary appears in subsequent system messages
- [ ] Retrieval is scoped to the active workspace by default
- [ ] Chunks below the quality threshold are excluded from context
- [ ] Home page displays real stats, recent documents, and suggested queries
- [ ] Streaming can be cancelled mid-response
- [ ] Token counter updates during streaming
- [ ] All new backend endpoints are covered by integration tests
- [ ] No regression in existing search, indexing, or chat functionality

---

# Dependencies

Requires:

* Phase 00 — Assistant experience and conversation UI
* Phase 01 — LLM provider and streaming
* Phase 02 — Hybrid search and indexing pipeline
* Phase 03 — Workspace management and file watcher

Provides the intelligence foundation for:

* Phase 05 — Knowledge graph (graph-augmented retrieval via ContextAssembler)
* Phase 06 — Enterprise features (multi-user, permissions, audit)
* Phase 07 — Automation (workflow engine, task scheduling, event system)

---

# Related Documentation

* `docs/architecture/capability-model.md`
* `docs/architecture/application-layers.md`
* `docs/decisions/ADR-003-AI-Provider-Abstraction.md`
* `docs/decisions/ADR-008-Search-Architecture.md`
* `docs/decisions/ADR-010-Logging-and-Observability.md`

---

# Next Phase

After completing this phase, proceed to:

**Phase 05: Knowledge Graph**

The next phase introduces document summarisation on demand, structured document Q&A, drafting assistance, and clipboard/export capabilities that let users act on what the AI finds.
