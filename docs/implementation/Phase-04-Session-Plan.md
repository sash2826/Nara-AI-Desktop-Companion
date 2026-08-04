# Phase 04 — Parallel Session Plan

**Phase:** 04 — AI Context & Intelligence  
**Status:** In Progress  
**Last Updated:** 2026-08-04

This document defines which epics can run in parallel sessions and which must be sequenced.
Both sessions update the checklist below after completing each epic.

---

## Session Map

```
Session A (Intelligence Core)          Session B (Home Dashboard)
─────────────────────────────          ──────────────────────────
Epic 4.0 — Context Assembler           Epic 4.4 — Home Page Dashboard
     │
Epic 4.1 — Conversation Memory         (complete — merge into main)
     │
Epic 4.2 — Multi-Document Reranking
     │
Epic 4.3 — Source Citation
     │
Epic 4.5 — Streaming Improvements

(all in sequence — each epic builds
 on the output of the prior one)
```

Session B can start immediately and finish independently.
Session A must proceed in order: 4.0 → 4.1 → 4.2 → 4.3 → 4.5.

---

## Why These Sessions Cannot Be Merged

**Epic 4.4 is fully isolated:**

- New files only: `HomePage.tsx`, `frontend/src/components/home/*`, `backend/routers/ai_context.py`, `capabilities/ai/suggested_queries_service.py`
- No existing file touched by Session A is modified
- No database migration required (reads existing `documents` and `chunks` tables)
- Safe to develop, commit, and merge at any time

**Epics 4.0–4.5 form a dependency chain:**

| Epic | Depends On | Shared Files |
|---|---|---|
| 4.0 | — | `capabilities/ai/`, `useConversation.ts`, `ConversationService.ts` |
| 4.1 | 4.0 complete | `conversations.py` router, migration 005, `ConversationService.ts` |
| 4.2 | 4.0 complete | `capabilities/ai/reranker.py`, `useConversation.ts` |
| 4.3 | 4.0 complete | `MessageBubble.tsx`, `ConversationService.ts`, `llm_client.py` |
| 4.5 | 4.3 complete | `AssistantHeader.tsx`, `MessageBubble.tsx`, `llm_client.py` |

Attempting to run any two of 4.0–4.5 in parallel would produce merge conflicts
in `useConversation.ts`, `ConversationService.ts`, and `llm_client.py`.

---

## File Ownership

### Session A — owns exclusively

```
backend/src/enterprise_ai_companion/capabilities/ai/
  context_assembler.py          (new — Epic 4.0)
  conversation_memory.py        (new — Epic 4.1)
  reranker.py                   (new — Epic 4.2)

backend/src/enterprise_ai_companion/api/routers/
  conversations.py              (modify — Epic 4.1)

database/migrations/
  005_conversation_memory.sql   (new — Epic 4.1)

frontend/src/hooks/
  useConversation.ts            (modify — Epics 4.0, 4.2)

frontend/src/services/conversation/
  ConversationService.ts        (modify — Epics 4.0, 4.1, 4.3)

frontend/src/components/assistant/
  AssistantHeader.tsx           (modify — Epic 4.5)
  MessageBubble.tsx             (modify — Epics 4.3, 4.5)
  CitationChip.tsx              (new — Epic 4.3)

backend/src/enterprise_ai_companion/capabilities/ai/
  llm_client.py                 (modify — Epic 4.5)
```

### Session B — owns exclusively

```
frontend/src/pages/
  HomePage.tsx                  (rewrite — Epic 4.4)

frontend/src/components/home/   (new directory — Epic 4.4)
  QuickStats.tsx
  RecentDocuments.tsx
  SuggestedQueries.tsx
  ActiveWorkspaceCard.tsx

backend/src/enterprise_ai_companion/capabilities/ai/
  suggested_queries_service.py  (new — Epic 4.4)

backend/src/enterprise_ai_companion/api/routers/
  ai_context.py                 (new — Epic 4.4)
```

### Shared — READ ONLY by both sessions

```
backend/src/enterprise_ai_companion/api/app.py
  (Session A registers migration 005 + ContextAssembler)
  (Session B registers ai_context router)
  — coordinate: whichever session finishes last does a non-conflicting add
```

---

## Progress Checklist

Sessions must update this file after each epic is merged.
Mark with `[x]` when the epic is fully merged into main and verified.

### Session B

- [x] **4.4** Home Page Dashboard
  - [x] `backend/api/routers/stats.py` created — `GET /stats` (SQL aggregates) + `POST /stats/suggestions` (LLM-generated queries with graceful failure); replaces planned `suggested_queries_service.py` + `ai_context.py`
  - [x] `GET /stats` returns `document_count`, `chunk_count`, `total_chars`, `conversation_count`, `watched_folder_count`, `indexing_error_count`, `recent_files` (last 5)
  - [x] `POST /stats/suggestions` calls LLM with recent file paths; returns `[]` on any failure; strips markdown fences before JSON parse
  - [x] Rust IPC: `DashboardStatsResponse`, `RecentFileResponse`, `SuggestionsRequest`, `SuggestionsResponse` structs; `get_stats` + `get_suggested_queries` commands registered in `invoke_handler!`
  - [x] TypeScript: `DashboardStats`, `RecentFile`, `SuggestionsResponse` interfaces; `getStats()`, `getSuggestedQueries()` added to `IPCClient`
  - [x] `StatTile.tsx` — K/M formatting, `accent` prop (default/warning/success)
  - [x] `RecentFilesList.tsx` — open-on-hover button, dashed empty state
  - [x] `SuggestedQueries.tsx` — pill buttons that pre-fill search query and navigate to Search page
  - [x] `useDashboard.ts` — loads stats on mount, chains suggestions load, 1-hour `localStorage` cache (`eac-suggested-queries`)
  - [x] `HomePage.tsx` rewritten — 6-tile stats grid (Errors tile turns `accent="warning"` when errors > 0), loading skeletons, 2-column lower section (Recent Files + Suggested Queries), Refresh button
  - [x] `app.py` updated to register `stats` router
  - [x] Manual verification: `npx tsc --noEmit` — 0 errors from Session B files (8 pre-existing errors in Session A files are unrelated)

### Session A — Epic 4.0

- [x] **4.0** Context Assembly Service
  - [x] `ContextPayload` dataclass defined (`capabilities/ai/context_assembler.py`)
  - [x] `ContextAssembler` built with quality filtering (min RRF 0.004) and deduplication
  - [x] Token budget enforcement implemented (5 chunks / 12 000 chars)
  - [x] Active workspace scoping wired (passes `activeProjectFolder` to `searchHybrid`)
  - [x] `ContextEngine.ts` extended with typed `RetrievedChunk` and `retrievedChunks` field
  - [x] `NullContextEngine` and `WorkspaceContextEngine` updated to include new field
  - [x] `useConversation.ts` upgraded: `searchHybrid(20)`, client-side filter/dedup/budget
  - [x] `ConversationService.buildSystemMessage` strengthened with numbered citations + synthesis rules
  - [x] Tests updated — all fixtures include `retrievedChunks: null`; label assertions updated
  - [x] `npx tsc --noEmit` passes with zero errors

### Session A — Epic 4.1

- [x] **4.1** Conversation Memory
  - [x] Migration 005 written (`turn_count INTEGER DEFAULT 0`, `summary TEXT` on `conversations`)
  - [x] `ConversationRepository` extended: `get_memory_state()`, `increment_turn_count()`, `save_summary()`, `load_oldest_messages()`
  - [x] `conversation_memory.py` — `ConversationMemoryService` with `on_assistant_turn_saved()` (triggers at every 10th turn) and `get_summary_prefix()`
  - [x] `conversations.py` router: `save_message` fires `on_assistant_turn_saved` as background `asyncio.Task` for assistant messages; new `GET /{id}/memory` endpoint returns `turn_count` + `summary`
  - [x] `ContextSnapshot` extended with `conversationSummary: string | null`
  - [x] `NullContextEngine` and `WorkspaceContextEngine` updated
  - [x] `IPCClient.getConversationMemory()` added
  - [x] Rust: `ConversationMemoryResponse` struct + `get_conversation_memory` command registered
  - [x] `useConversation.ts`: per-conversation summary cache (`useRef<Map>`), fetched once on first send, injected into snapshot; cache cleared on `clearMessages`
  - [x] `ConversationService.buildSystemMessage`: summary prepended as `CONVERSATION MEMORY` block ahead of retrieved context and workspace signals
  - [x] Test fixtures updated — all include `conversationSummary: null`
  - [x] `npx tsc --noEmit` passes with zero errors

### Session A — Epic 4.2

- [x] **4.2** Multi-Document Reranking
  - [x] `reranker.py` — `ChunkReranker` ABC + `RankedChunk` dataclass + `HeuristicReranker` (bigram cosine × 0.7 + RRF position bonus × 0.3)
  - [x] `context_assembler.py` updated: injects `HeuristicReranker` by default; `assemble()` calls `reranker.rerank()` between hybrid search and `_filter_and_budget`; `_filter_and_budget` now accepts `list[RankedChunk]` pre-sorted by `rerank_score`
  - [x] `useConversation.ts`: module-level `tokenise()`, `ngramTf()`, `cosine()`, `heuristicRerank()` + `RankedCandidate` interface; retrieval block calls `heuristicRerank(trimmed, searchResponse.results)` and iterates reranked list through filter/dedup/budget
  - [x] `ConversationService.ts` synthesis prompt updated: mentions excerpts are ranked by relevance, instructs model to weight [1] highest while synthesising all, updates header line to "ordered by relevance, most relevant first"
  - [x] `npx tsc --noEmit` passes with zero errors

### Session A — Epic 4.3

- [x] **4.3** Source Citation
  - [x] `CitationMeta` interface added to `types/conversation.ts` (`chunkId`, `documentPath`, `chunkIndex`, `rrfScore`)
  - [x] `Message` type extended with optional `citations?: CitationMeta[] | null`
  - [x] `CitationChip.tsx` — chip shows filename + numbered index; hover tooltip reveals full path, chunk index, and score%; clicking opens file via Tauri shell
  - [x] `conversationStore.ts` — `updateMessageCitations(id, citations)` action added
  - [x] `useConversation.ts` — `onStreamComplete` converts `retrievedChunks` → `CitationMeta[]` and calls `updateMessageCitations`
  - [x] `MessageBubble.tsx` — citations bar rendered below assistant bubble content (hidden during streaming, hidden when no citations)
  - [x] System prompt citation rules already enforced in Epic 4.0 (`[path/to/file]` inline format); `FilePathChip` handles inline rendering
  - [x] `npx tsc --noEmit` passes with zero errors

### Session A — Epic 4.5

- [x] **4.5** Streaming Improvements
  - [x] `MessageStatus` extended with `"cancelled"`; `Message` gains optional `tokenCount?: number`
  - [x] `conversationStore` — `updateMessageTokenCount(id, n)` action added
  - [x] `useConversation.ts` — `onStreamChunk` updates token count (word-split heuristic) per chunk; `onStreamCancelled` sets status `"cancelled"` and persists partial response to SQLite; `cancelStream` callback exposed from hook
  - [x] `AssistantHeader.tsx` — stop button (`Square` icon, destructive colour) rendered while `isTyping || isStreaming`; hidden otherwise; `onCancelStream` prop added
  - [x] `AssistantWidget.tsx` — `cancelStream` wired to `onCancelStream` on `AssistantHeader`
  - [x] `MessageBubble.tsx` — streaming cursor replaced by cursor + live "N tokens" counter (`aria-live`); cancelled messages show inline "stopped" chip; `isCancelled` guard added
  - [x] `AbortController` already wired in `ConversationService` (Phase 00); `APIMProvider.cancel()` already triggers abort signal — no changes required
  - [x] `npx tsc --noEmit` passes with zero errors

---

## Merge Order Recommendation

1. Session B merges Epic 4.4 whenever it is complete — no dependencies.
2. Session A merges each epic immediately after completing it (4.0, then 4.1, etc.)
3. After Session A completes Epic 4.0, update `app.py` to register the assembler.
4. After Session B completes Epic 4.4, update `app.py` to register `ai_context` router.
   If Session A has already touched `app.py` by then, the Session B merge requires
   a one-line non-conflicting addition to the lifespan block.

---

## Phase Completion Gate

Phase 04 is complete when all boxes above are checked AND:

- [ ] `npx tsc --noEmit` passes with zero errors
- [ ] Pytest integration tests pass for all new backend endpoints
- [ ] No regression in search, indexing, or existing chat functionality
- [ ] Phase 04 spec `Phase-04-AI-Context-Intelligence.md` updated to `Status: Complete`
