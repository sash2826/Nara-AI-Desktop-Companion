# Phase 01: AI Integration

**Phase:** 01

**Status:** In Progress

**Estimated Duration:** 5–7 Days

---

# Purpose

Phase 01 connects the Enterprise AI Companion to real AI services.

Phase 00 established the complete user experience — Living Orb, Glass Prompt, conversation architecture, and all service interfaces — using a `MockProvider` that returns canned responses. The user can see the interface but the AI is not real.

Phase 01 makes the AI real.

At the completion of this phase, the Glass Prompt will respond with live intelligence via Azure API Management. The Python backend will be running as a sidecar process, connected to the Tauri desktop application through an IPC channel. Embeddings will be generated locally using BGE-M3. The context engine will begin enriching requests with real workspace signals.

---

# Objectives

Upon completion of this phase:

- The Glass Prompt streams real responses from Azure API Management.
- The `APIMProvider` is fully implemented (SSE parsing, auth, error handling, retry).
- The Tauri ↔ Python IPC channel is operational (command-based, typed contracts).
- The Python backend starts and shuts down with the Tauri application lifecycle.
- BGE-M3 embeddings are generated locally via the Python backend.
- The `ContextEngine` returns real workspace signals (active file path, recent documents).
- Conversation history is persisted to SQLite and survives application restarts.
- All Phase 00 mock infrastructure remains functional via `LLM_CONFIG.provider = "mock"`.

---

# Prerequisites

- Phase 00 complete (all ✅ items in Phase 00 checklist).
- Azure API Management endpoint and subscription key available.
- Python 3.11+ installed on the development machine.
- The `backend/` scaffold created in Phase 00 (`backend/pyproject.toml`, capability directories, smoke tests passing).

---

# Architecture

## Communication flow — Phase 01

```text
Glass Prompt (React)
        │
   useConversation
        │
  ConversationService
        │
   APIMProvider          ←── APIM endpoint + subscription key
        │                    (env vars, never hardcoded)
   Azure APIM
        │
  [GPT model behind APIM]
```

```text
Glass Prompt / ContextEngine (React)
        │
   Tauri IPC (invoke)
        │
   Python backend (sidecar)
        │
  ┌─────┴──────┐
  │            │
BGE-M3      SQLite
(embeddings) (persistence)
```

---

# Epics

## Epic 1.1 — APIMProvider Implementation

Complete the `APIMProvider` skeleton established in Phase 00.

### Tasks

**1.1.1 Environment configuration**

- Add `VITE_APIM_ENDPOINT` and `VITE_APIM_SUBSCRIPTION_KEY` to `.env.local` (gitignored).
- Update `src/config/ai.ts` to read these variables at startup.
- Switch `LLM_CONFIG.provider` to `"apim"` when the env vars are present; fall back to `"mock"` when they are absent.
- Document the env var names in `frontend/.env.example`.

**1.1.2 SSE streaming parser**

- Implement the `streamResponse` SSE parser in `APIMProvider.ts` (the TODO block on lines 112–147).
- Handle `data: {...}` lines, `data: [DONE]` sentinel, and empty/comment lines.
- Parse the OpenAI-compatible delta envelope: `choices[0].delta.content`.
- Yield `{ content, done: false }` per chunk; yield `{ content: "", done: true }` on `[DONE]`.

**1.1.3 `generateResponse` implementation**

- Implement the non-streaming path (the TODO block on lines 75–84).
- Parse `choices[0].message.content` from the JSON response.

**1.1.4 Auth header**

- Uncomment and wire `Ocp-Apim-Subscription-Key` header in `buildHeaders()`.
- Credential arrives from `APIMConfig.subscriptionKey` — never hardcoded.

**1.1.5 Retry and timeout**

- Implement exponential backoff for `429` (rate limit) and `503` (service unavailable).
- Add `AbortSignal.timeout()` to `fetchAPIM()` with a configurable timeout (default: 30 s).
- Add APIM error envelope parsing in `assertResponseOk()` — extract `apim-request-id` header.

**1.1.6 Conversation history**

- Extend `buildRequestBody()` to accept prior messages so APIM receives multi-turn context.
- Update `ConversationService.send()` to pass the current message history to the provider.
- Keep the change backward-compatible with `MockProvider` (history parameter optional).

**1.1.7 APIMProvider tests**

- Unit tests: SSE parser (valid chunks, `[DONE]`, malformed lines, empty delta).
- Unit tests: error mapping (401 → APIMError, 429 → retryable, 503 → retryable).
- Integration test: full `streamResponse` call against a local SSE mock server (MSW or similar).

---

## Epic 1.2 — Tauri ↔ Python IPC Bridge

Establish the IPC channel defined by ADR-007.

### Architecture

```text
React (frontend)
     │
  invoke("command_name", payload)    ← Tauri invoke API
     │
  Tauri command handler (Rust)
     │
  HTTP POST to Python sidecar        ← loopback, port configured at startup
     │
  Python FastAPI handler
     │
  Service / Capability
```

The Rust layer is a thin passthrough — it validates that the command exists and proxies to the Python sidecar. Business logic lives in Python.

### Tasks

**1.2.1 Python sidecar: FastAPI application**

- Add `fastapi` and `uvicorn` to `backend/pyproject.toml` dependencies.
- Create `backend/src/enterprise_ai_companion/api/app.py` — FastAPI application with health endpoint (`GET /health`).
- Create `backend/src/enterprise_ai_companion/api/server.py` — uvicorn startup / shutdown.
- Create `backend/src/enterprise_ai_companion/__main__.py` — entry point: `python -m enterprise_ai_companion`.

**1.2.2 Tauri sidecar configuration**

- Add the Python backend as a Tauri sidecar in `tauri.conf.json`.
- Tauri spawns and manages the Python process lifecycle (start on app launch, kill on exit).
- Port is assigned dynamically at startup and passed to the frontend via the `app-ready` event or a startup command.
- Update `frontend/src-tauri/src/lib.rs` (or `main.rs`) with the sidecar spawn logic.

**1.2.3 Tauri IPC client (TypeScript)**

- Create `frontend/src/services/ipc/IPCClient.ts` — typed wrapper around `@tauri-apps/api/core` `invoke`.
- Define `IPCRequest<TPayload>` and `IPCResponse<TData>` types.
- All IPC calls flow through this client — no component or service calls `invoke` directly.

**1.2.4 IPC command: `health_check`**

- Tauri command: `health_check` → proxies to `GET /health` on the Python sidecar.
- TypeScript: `IPCClient.healthCheck(): Promise<{ status: "ok" }>`.
- Integration test: Tauri dev build starts Python sidecar, `health_check` returns `{ status: "ok" }`.

**1.2.5 IPC tests**

- Unit tests for `IPCClient` (mock `invoke`, assert correct command names and payloads).
- Integration test for sidecar startup (requires Tauri dev environment).

---

## Epic 1.3 — BGE-M3 Embedding Service

Local embedding generation using BGE-M3, exposed over IPC.

### Tasks

**1.3.1 Python embedding capability**

- Add `FlagEmbedding` (BGE-M3) to `backend/pyproject.toml`.
- Create `backend/src/enterprise_ai_companion/capabilities/indexing/embedding_service.py`.
  - `EmbeddingService.generate(text: str) -> list[float]`
  - `EmbeddingService.generate_batch(texts: list[str]) -> list[list[float]]`
  - Model loaded once at startup (lazy singleton).
- Unit tests for `EmbeddingService` (shape validation, determinism).

**1.3.2 IPC command: `generate_embedding`**

- FastAPI endpoint: `POST /embeddings` — accepts `{ text: string }`, returns `{ embedding: number[] }`.
- Tauri command: `generate_embedding` → proxies to `/embeddings`.
- TypeScript: `IPCClient.generateEmbedding(text: string): Promise<number[]>`.

**1.3.3 Frontend embedding hook**

- Create `frontend/src/hooks/useEmbedding.ts` — thin wrapper around `IPCClient.generateEmbedding`.
- Used by the retrieval layer in Phase 02; stub in Phase 01.

---

## Epic 1.4 — Context Engine: Real Workspace Signals

Replace `NullContextEngine` with a live implementation that observes the active workspace.

### Tasks

**1.4.1 `WorkspaceContextEngine`**

- Create `frontend/src/services/context/WorkspaceContextEngine.ts` implementing `ContextEngine`.
- `getSnapshot()` returns:
  - `activeProjectFolder`: derived from the most recently focused file path (Tauri `fs` plugin).
  - `recentDocuments`: last 5 document paths accessed this session (tracked in memory).
  - `explicitContext`: always `null` in Phase 01 (Phase 03 adds manual context pinning).
- Wire `WorkspaceContextEngine` into `ConversationServiceProvider` in place of `NullContextEngine`.

**1.4.2 Context passed to `ConversationService`**

- `useConversation.sendMessage()` calls `contextEngine.getSnapshot()` before calling `service.send()`.
- `ConversationService.send()` passes the snapshot to `APIMProvider` as part of the system prompt.
- Update `buildRequestBody()` to inject context into a system message: `"Active folder: {folder}. Recent files: {files}."`.

**1.4.3 Context engine tests**

- Unit test: `WorkspaceContextEngine.getSnapshot()` returns `activeProjectFolder: null` when no file is active.
- Unit test: `recentDocuments` accumulates up to 5 paths, FIFO.

---

## Epic 1.5 — Conversation Persistence (SQLite)

Store conversation history to SQLite so conversations survive restarts.

### Tasks

**1.5.1 SQLite schema**

- Create `database/schemas/conversations.sql`:
  ```sql
  CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
  );

  CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'complete',
    created_at TEXT NOT NULL
  );
  ```

**1.5.2 Python persistence capability**

- Add `aiosqlite` to `backend/pyproject.toml`.
- Create `backend/src/enterprise_ai_companion/infrastructure/database.py` — connection management (async, single connection per process).
- Create `backend/src/enterprise_ai_companion/capabilities/indexing/conversation_repository.py`:
  - `save_message(conversation_id, message)`.
  - `load_conversation(conversation_id) -> list[Message]`.
  - `list_conversations() -> list[ConversationSummary]`.

**1.5.3 IPC commands: conversation CRUD**

- `POST /conversations` — create or return existing conversation.
- `POST /conversations/{id}/messages` — append a message.
- `GET /conversations/{id}` — load full message history.
- Tauri commands: `save_message`, `load_conversation`.
- TypeScript: `IPCClient.saveMessage(...)`, `IPCClient.loadConversation(...)`.

**1.5.4 Frontend persistence wiring**

- `useConversation` calls `IPCClient.saveMessage()` after each user message and assistant message completes.
- On `ConversationServiceProvider` mount, load the most recent conversation from SQLite and hydrate `conversationStore`.

**1.5.5 Persistence tests**

- Python unit tests: `ConversationRepository` CRUD (in-memory SQLite).
- TypeScript unit tests: `useConversation` calls `IPCClient.saveMessage` with correct payloads.

---

# Implementation Order

Execute epics in this sequence. Each epic produces a working, testable increment.

```
Epic 1.1 — APIMProvider     → Real AI responses in Glass Prompt
Epic 1.2 — IPC Bridge       → Python sidecar operational
Epic 1.3 — BGE-M3           → Local embeddings over IPC
Epic 1.4 — Context Engine   → Workspace context enriches requests
Epic 1.5 — Persistence      → Conversations survive restarts
```

Epic 1.1 has no backend dependency and can be verified immediately with the running Tauri app.
Epic 1.2 is a prerequisite for Epics 1.3, 1.4 (partial), and 1.5.
Epics 1.3 and 1.4 may be developed in parallel once Epic 1.2 is complete.
Epic 1.5 requires Epic 1.2.

---

# Non-Goals

The following are explicitly out of scope for Phase 01:

- Qdrant vector search (Phase 02).
- Neo4j knowledge graph (Phase 02 / Phase 04).
- OneDrive connector (Phase 02).
- Local file indexing pipeline (Phase 02).
- MSAL / Azure AD authentication (Phase 02 — subscription key auth is used in Phase 01).
- Workspace UI (Phase 03).
- File browser (Phase 03).

---

# Configuration

## Environment variables

| Variable | Description | Required |
|---|---|---|
| `VITE_APIM_ENDPOINT` | Azure APIM gateway URL | Yes (production) |
| `VITE_APIM_SUBSCRIPTION_KEY` | APIM subscription key | Yes (production) |
| `VITE_LLM_PROVIDER` | `"mock"` or `"apim"` | No (defaults to `"mock"`) |

Credentials are never committed to source control.
`frontend/.env.local` is gitignored.
`frontend/.env.example` documents the variable names without values.

---

# Deliverables

- `APIMProvider` fully implemented with SSE streaming, auth, retry, and timeout.
- `frontend/.env.example` with documented variable names.
- `LLM_CONFIG` auto-selects provider from environment.
- Tauri sidecar configuration (`tauri.conf.json`) launching the Python backend.
- `IPCClient.ts` — typed Tauri IPC wrapper.
- `health_check` IPC command operational.
- `EmbeddingService` (Python) + `generate_embedding` IPC command.
- `WorkspaceContextEngine` replacing `NullContextEngine`.
- SQLite schema for conversations and messages.
- `ConversationRepository` (Python) with async CRUD.
- Conversation persistence wired into `useConversation`.
- Unit tests for all new components.
- Integration tests for APIMProvider and IPC health check.

---

# Phase 01 Completion Checklist

## Epic 1.1 — APIMProvider

- ✅ `VITE_APIM_ENDPOINT` and `VITE_APIM_SUBSCRIPTION_KEY` read from env vars
- ✅ `frontend/.env.example` created with variable names (no values)
- ✅ `LLM_CONFIG` auto-selects `"apim"` when env vars present, `"mock"` when absent
- ✅ `APIMProvider.streamResponse` SSE parser implemented
- ✅ `APIMProvider.generateResponse` non-streaming path implemented
- ✅ `Ocp-Apim-Subscription-Key` header wired from config
- ✅ Exponential backoff retry for 429 and 503
- ✅ Request timeout via `AbortSignal.timeout()`
- ✅ APIM error envelope parsed; `apim-request-id` extracted
- ✅ Multi-turn conversation history passed to APIM
- ✅ SSE parser unit tests (17 tests, all passing)
- ✅ Error mapping unit tests
- ✅ Glass Prompt streams real responses end-to-end (confirmed working)

## Epic 1.2 — IPC Bridge

- ✅ `fastapi` and `uvicorn` added to `backend/pyproject.toml`
- ✅ FastAPI app with `GET /health` created
- ✅ `python -m enterprise_ai_companion` starts the server
- ✅ Python sidecar spawned from Tauri on app launch (std::process::Command)
- ✅ Sidecar starts and stops with Tauri application lifecycle
- ✅ `IPCClient.ts` created with typed `invoke` wrapper
- ✅ `health_check` IPC command operational (Tauri → reqwest → FastAPI)
- ✅ `waitForSidecar()` utility listens for `sidecar-ready` event
- ✅ `IPCClient` unit tests (4 tests)
- ✅ Backend health endpoint unit tests (3 tests)
- ☐ IPC health check end-to-end integration test (requires running Tauri dev build)

## Epic 1.3 — BGE-M3 Embeddings

- ✅ `fastembed` added to `backend/pyproject.toml` (ONNX runtime; no PyTorch required)
- ✅ `EmbeddingService.generate()` implemented (1024-dim BGE-M3, lazy singleton)
- ✅ `EmbeddingService.generate_batch()` implemented
- ✅ `POST /embeddings` FastAPI endpoint (Pydantic validation, 422 on empty text)
- ✅ `generate_embedding` Tauri IPC command (Rust → reqwest → Python)
- ✅ `IPCClient.generateEmbedding()` TypeScript wrapper
- ✅ `useEmbedding` hook created (manages loading/error state; stub consumer for Phase 02)
- ✅ `EmbeddingService` endpoint tests — 7 tests passing (model mocked for CI speed)
- ✅ `IPCClient.generateEmbedding` unit tests — 2 tests passing
- ✅ `useEmbedding` unit tests — 6 tests passing
- ☐ `EmbeddingService` integration tests with real model (run manually; model ~500 MB)

## Epic 1.4 — Context Engine

- ☐ `WorkspaceContextEngine` created
- ☐ `activeProjectFolder` derived from active file path
- ☐ `recentDocuments` tracks last 5 paths (FIFO, session-only)
- ☐ `WorkspaceContextEngine` wired into `ConversationServiceProvider`
- ☐ Context injected as system message in `buildRequestBody()`
- ☐ `WorkspaceContextEngine` unit tests

## Epic 1.5 — Conversation Persistence

- ☐ `database/schemas/conversations.sql` created
- ☐ `aiosqlite` added to `backend/pyproject.toml`
- ☐ `database.py` connection management
- ☐ `ConversationRepository` CRUD implemented
- ☐ `POST /conversations`, `POST /conversations/{id}/messages`, `GET /conversations/{id}` endpoints
- ☐ `save_message` and `load_conversation` IPC commands
- ☐ `IPCClient.saveMessage()` and `IPCClient.loadConversation()` implemented
- ☐ `useConversation` persists messages via IPC after each turn
- ☐ `ConversationServiceProvider` hydrates store from SQLite on mount
- ☐ `ConversationRepository` unit tests (in-memory SQLite)
- ☐ `useConversation` persistence unit tests

---

# Completion Criteria

This phase is complete when:

- The Glass Prompt streams real AI responses from Azure APIM with no mock fallback required.
- The Python backend starts automatically with the Tauri application.
- The IPC health check command succeeds end-to-end.
- BGE-M3 embeddings are generated locally and returned over IPC.
- Workspace context is enriched with real signals and injected into each request.
- Conversations persist to SQLite and are restored on application restart.
- All unit tests pass.
- `LLM_CONFIG.provider = "mock"` still produces working mock responses (no regressions).

---

# Next Phase

Proceed to:

**Phase 02 — Knowledge & Search**

The next phase establishes the data layer: SQLite structured storage, Qdrant vector indexing, Neo4j knowledge graph, and the hybrid search engine. The local file indexing pipeline is also built in this phase, feeding documents into the vector and graph stores so the retrieval broker can return real results.
