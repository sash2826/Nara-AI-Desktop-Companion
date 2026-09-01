# Document-Management-RAG-Graph-Agent

An AI-powered desktop platform for the Volvo Group that helps users understand, organise, retrieve, and interact with their digital knowledge. Built with Tauri, React, and a Python backend — runs entirely on-device with no cloud dependency except the Volvo GenAI Hub for LLM inference.

---

## What it does

- **Living Orb** — an always-on-top desktop widget that floats above every window. Single click opens a compact AI query overlay. Double click opens the full application.
- **File Intelligence** — watches your Downloads folder. When a new file arrives it indexes it, scores placement against your existing folders, and suggests where to move it via the orb.
- **Organise** — on-demand audit of your existing indexed folders with reorganisation recommendations.
- **Semantic Search** — hybrid keyword + vector search across all indexed documents.
- **AI Chat** — conversational interface grounded in your document library.

> **Note — Intelligent Folder Discovery (Clustering):** The backend pipeline for automatic folder discovery is fully implemented (Phase 10 Scenario 3). It uses agglomerative clustering over document embeddings and knowledge-graph entity overlap to propose new folders for unorganised floating files. The feature is **hidden in the UI** pending final folder-naming quality validation. To re-enable it set `CLUSTER_UI_ENABLED = true` in [OrganiseTab.tsx](frontend/src/components/workspace/OrganiseTab.tsx). The REST API endpoints remain active at `POST /organisation/clusters/discover` and `GET /organisation/clusters/proposals`.

---

## Architecture

```
┌─────────────────────────────────────┐
│  Tauri Desktop Shell (Rust)         │
│  ┌───────────────┐  ┌─────────────┐ │
│  │  Main Window  │  │  Orb Window │ │
│  │  React + TS   │  │  React + TS │ │
│  └──────┬────────┘  └──────┬──────┘ │
│         │  IPC (HTTP)      │        │
└─────────┼──────────────────┼────────┘
          │                  │
┌─────────▼──────────────────▼────────┐
│  Python Backend (FastAPI/uvicorn)   │
│  ├── File indexing + OCR            │
│  ├── Embedding generation (BGE-M3)  │
│  ├── Semantic search (Qdrant)       │
│  ├── Knowledge graph (SQLite/Neo4j) │
│  └── LLM integration (GenAI Hub)    │
└─────────────────────────────────────┘
```

The frontend never touches the database or AI providers directly. All business logic lives in the Python backend, exposed to Tauri over a local HTTP IPC channel.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| [Rust](https://rustup.rs/) | stable | Required for Tauri |
| [Node.js](https://nodejs.org/) | 20+ | |
| [pnpm](https://pnpm.io/) | 9+ | `npm i -g pnpm` |
| [Python](https://python.org/) | 3.11+ | Backend |
| [Tauri CLI](https://tauri.app/start/prerequisites/) | v2 | Installed via `pnpm tauri` |

> **Windows only:** The desktop application targets Windows. The Tauri build uses the MSVC toolchain. See [docs/](docs/) for the `~/.cargo/config.toml` xwin setup if you don't have Visual Studio installed.

---

## Setup

### 1. Clone

```bash
git clone <repo-url>
cd Document-Management-RAG-Graph-Agent
```

### 2. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

# Install with dev dependencies
pip install -e ".[dev]"
```

Create `backend/.env` with your configuration:

```env
# Required
EAC_APIM_ENDPOINT=https://api.volvogenaihubqa.volvogroup.net

# Optional — subscription key stored in Windows Credential Manager by the app
# Set here only for headless / CLI use
EAC_APIM_SUBSCRIPTION_KEY=your_subscription_key_here

# Model deployment ID — verify the active deployment in the GenAI Hub portal
EAC_LLM_MODEL_ID=gpt-41-mini_gb_2025-04-14

# Graph backend: "sqlite" (default, no extra setup) or "neo4j"
EAC_GRAPH_PROVIDER=sqlite

# Storage paths — defaults to %APPDATA%\Document-Management-RAG-Graph-Agent\ if unset
# EAC_DB_PATH=C:\path\to\eac.db
# EAC_QDRANT_PATH=C:\path\to\qdrant-data
```

> **API key:** In normal use the app stores and loads the subscription key from Windows Credential Manager (Settings → Security). You only need `EAC_APIM_SUBSCRIPTION_KEY` in `.env` for headless scripts or CI.

### 3. Frontend

```bash
cd frontend
pnpm install
```

---

## Running in development

Open two terminals.

**Terminal 1 — Backend:**
```bash
cd backend
.venv\Scripts\activate
python -m enterprise_ai_companion
```

The backend starts on a free port and writes it to a sidecar port file that Tauri reads automatically.

**Terminal 2 — Tauri dev:**
```bash
cd frontend
pnpm tauri dev
```

This launches the main window and the floating orb window. Hot-reload is active for the React frontend. Rust changes require a full rebuild.

---

## Building for production

```bash
cd frontend
pnpm tauri build
```

The installer is written to `frontend/src-tauri/target/release/bundle/nsis/`.

The Python backend is compiled into a standalone sidecar executable via PyInstaller and bundled inside the installer automatically.

---

## Testing

**Backend:**
```bash
cd backend
.venv\Scripts\activate
pytest
```

**Frontend:**
```bash
cd frontend
pnpm test          # run once
pnpm test:watch    # watch mode
pnpm test:ui       # browser UI
```

**Linting / formatting:**
```bash
cd frontend
pnpm lint          # ESLint
pnpm format        # Prettier
```

---

## Environment variables reference

All backend configuration is read from environment variables (or `backend/.env`). None of these are required except `EAC_APIM_ENDPOINT`.

| Variable | Required | Default | Description |
|---|---|---|---|
| `EAC_APIM_ENDPOINT` | Yes | — | Volvo GenAI Hub base URL |
| `EAC_APIM_SUBSCRIPTION_KEY` | No | keychain | APIM subscription key (loaded from Windows Credential Manager at runtime) |
| `EAC_LLM_MODEL_ID` | No | `gpt-41-mini_gb_2025-04-14` | Active model deployment ID |
| `EAC_GRAPH_PROVIDER` | No | `sqlite` | `sqlite` or `neo4j` |
| `EAC_DB_PATH` | No | `%APPDATA%\...\eac.db` | SQLite database path |
| `EAC_QDRANT_PATH` | No | `%APPDATA%\...\qdrant` | Qdrant vector store path |
| `EAC_MIGRATIONS_DIR` | No | auto-detected | Path to SQL migration files |
| `EAC_IPC_SECRET` | No | auto-generated | Shared secret for Tauri ↔ backend IPC |
| `EAC_SYSTEM_INDEX_PATHS` | No | `""` | Comma-separated paths hidden from the document browser |

---

## Volvo GenAI Hub — key integration notes

The backend calls the Volvo internal APIM rather than the public Azure OpenAI or OpenAI APIs. Three things differ from standard documentation:

1. **Auth header:** use `api-key: <subscription-key>` — not `Ocp-Apim-Subscription-Key`
2. **Endpoint path:** `/azure-openai/v1/chat/completions?api-version=preview`
3. **Model in body:** pass `"model": "<deployment-id>"` in the request body, not in the URL

If you get HTTP 500, the deployment ID is likely decommissioned — check the GenAI Hub portal for the current active deployment and update `EAC_LLM_MODEL_ID`.

See [docs/genaihub-developer-feedback.md](docs/genaihub-developer-feedback.md) for the full integration notes including a cost-tracking proxy for local development.

---

## Project structure

```
.
├── frontend/                   # Tauri + React desktop application
│   ├── src/                    # React/TypeScript source
│   │   ├── components/         # UI components
│   │   ├── pages/              # Top-level page views
│   │   ├── services/           # IPC client, AI provider, search
│   │   ├── store/              # Zustand state stores
│   │   ├── providers/          # React context providers
│   │   └── windows/orb/        # Living Orb window components
│   └── src-tauri/              # Rust Tauri shell
│       ├── src/lib.rs          # IPC command handlers
│       └── tauri.conf.json     # Window and bundle config
│
├── backend/                    # Python FastAPI backend
│   └── src/enterprise_ai_companion/
│       ├── api/                # HTTP endpoints (routers + app)
│       ├── capabilities/
│       │   ├── indexing/       # File watcher, indexer, OCR
│       │   ├── retrieval/      # Hybrid search, keyword, semantic
│       │   ├── graph/          # Knowledge graph operations
│       │   ├── ai/             # LLM client
│       │   └── organisation/   # File placement scoring
│       └── infrastructure/     # DB, Qdrant, config, keychain
│
├── database/                   # SQLite schema and migrations
├── docs/                       # Architecture docs and ADRs
└── scripts/                    # Benchmark and utility scripts
```

---

## Documentation

| Document | Description |
|---|---|
| [docs/architecture/](docs/architecture/) | System design, capability model, technology choices |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records (ADRs) |
| [docs/implementation/](docs/implementation/) | Phase-by-phase implementation notes |
| [docs/genaihub-developer-feedback.md](docs/genaihub-developer-feedback.md) | GenAI Hub integration notes and cost-tracking proxy |
| [docs/genaihub-intern-onboarding.md](docs/genaihub-intern-onboarding.md) | Step-by-step setup guide for new team members |
| [.claude/CLAUDE.md](.claude/CLAUDE.md) | Engineering standards for AI-assisted development |
