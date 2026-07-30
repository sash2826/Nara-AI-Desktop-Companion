# Phase 02: Knowledge & Search

**Phase:** 02

**Status:** In Progress

**Estimated Duration:** 3-5 Days

---

# Purpose

Phase 02 establishes the data persistence layer and hybrid search architecture for the Enterprise AI Companion.

The two objectives of this phase are closely coupled: persistent storage makes indexing possible, and indexing makes intelligent search possible. They are implemented sequentially within this phase.

At the completion of this phase, the application should provide reliable data services across three storage technologies and support fast, accurate, context-aware retrieval across all indexed content.

---

# Objectives

Upon completion of this phase, the application should provide:

* SQLite integration
* Neo4j integration
* Qdrant integration
* Repository abstraction layer
* Database migration framework
* Connection and transaction management
* Document indexing
* Keyword search
* Semantic vector search
* Metadata filtering
* Hybrid ranking
* Search orchestration
* Search analytics

Business capabilities should remain unaware of database-specific and search-provider-specific implementation details.

---

# Prerequisites

Before beginning this phase:

* Phase 00 must be completed.
* Phase 01 must be completed.
* Configuration services should be operational.
* Logging infrastructure should be available.
* Background task manager should be functioning.

---

# Dependencies

Requires:

* Phase 00
* Phase 01

Provides the persistence and retrieval foundation for:

* Phase 03
* Phase 04
* Phase 05
* Phase 06
* Phase 07

---

# Related Documentation

* `docs/architecture/technology-stack.md`
* `docs/architecture/application-layers.md`
* `docs/architecture/capability-model.md`
* `docs/decisions/ADR-002-Data-Storage-Strategy.md`
* `docs/decisions/ADR-008-Search-Architecture.md`
* `docs/decisions/ADR-010-Logging-and-Observability.md`
* `docs/decisions/ADR-011-Background-Task-Processing.md`
* `docs/decisions/ADR-012-Error-Handling-Strategy.md`

---

# Part A — Data Layer

## Purpose

Implement a unified data access architecture that supports relational data, graph relationships, vector embeddings, and local file storage while hiding implementation details from business capabilities.

## Data Architecture

The persistence layer should follow a provider-based architecture.

```text
database/
│
├── migrations/
├── sqlite/
├── neo4j/
├── qdrant/
├── repositories/
├── providers/
├── models/
└── backups/
```

## Storage Responsibilities

### SQLite

Responsible for:

* Application settings
* Workspace metadata
* User preferences
* Document metadata
* Processing history
* Task history

SQLite stores structured application data.

---

### Neo4j

Responsible for:

* Knowledge graph
* Entity relationships
* Semantic links
* Document relationships
* Graph traversal

Neo4j manages connected information.

---

### Qdrant

Responsible for:

* Embedding storage
* Semantic search vectors
* Similarity lookup
* AI retrieval

Qdrant should only manage vector representations.

---

### Local File Storage

Responsible for:

* Original documents
* Attachments
* Cached resources
* Generated exports
* Temporary files

Large binary assets should not be stored inside relational databases.

## Repository Layer

Business capabilities should communicate only through repositories.

Responsibilities include:

* CRUD operations
* Query abstraction
* Validation support
* Transaction coordination
* Provider selection

Repositories should not expose database-specific APIs.

## Database Providers

Each storage engine should implement a provider responsible for:

* Connection management
* Initialization
* Health reporting
* Shutdown
* Error translation
* Performance monitoring

Providers should remain interchangeable wherever practical.

## Connection Management

The data layer should provide:

* Connection pooling
* Automatic reconnection
* Graceful shutdown
* Timeout handling
* Connection validation

Application services should never create database connections directly.

## Migration Framework

Provide support for:

* Schema creation
* Version tracking
* Incremental migrations
* Rollback support
* Migration validation

Database schema evolution should be predictable and repeatable.

## Transaction Management

Where supported, transactions should provide:

* Atomic operations
* Rollback on failure
* Consistency
* Isolation
* Durability

Cross-database coordination should be minimized and handled explicitly.

## Backup Strategy

The data layer should prepare for future backup support including:

* SQLite snapshots
* Export of graph data
* Vector collection backups
* Configuration backups
* Metadata restoration

Backup implementation may be expanded in later phases.

## Data Layer Deliverables

* SQLite provider
* Neo4j provider
* Qdrant provider
* Repository abstraction layer
* Migration framework
* Connection management
* Transaction support
* Health reporting
* Backup foundation

## Data Layer Completion Criteria

* All databases initialize successfully.
* Migrations execute without errors.
* Repository abstractions function correctly.
* Connections are managed automatically.
* Health checks report accurate status.
* Transactions behave consistently.
* Logging captures database events.
* Graceful shutdown closes all database connections.

---

# Part B — Search Engine

## Purpose

Implement the hybrid search architecture combining keyword search, semantic vector search, metadata filtering, and knowledge graph traversal behind a unified search interface.

## Search Architecture

The search subsystem should follow a provider-based architecture.

```text
search/
│
├── indexers/
├── providers/
├── ranking/
├── pipelines/
├── preprocessors/
├── filters/
├── models/
├── analytics/
└── services/
```

## Search Pipeline

Search requests should follow a consistent processing pipeline.

```text
User Query
      │
      ▼
Query Preprocessing
      │
      ▼
Search Orchestrator
      │
      ├─────────────┐
      ▼             ▼
Keyword Search   Semantic Search
      │             │
      └──────┬──────┘
             ▼
Metadata Filtering
             ▼
Ranking Engine
             ▼
Unified Results
```

Each stage should remain independently replaceable.

## Query Preprocessing

Responsible for:

* Query normalization
* Tokenization
* Stop-word removal where appropriate
* Typo tolerance preparation
* Query expansion
* Intent preparation

Preprocessing should improve retrieval quality without altering user intent.

## Keyword Search

Provide:

* Full-text search
* Exact phrase matching
* Prefix matching
* Boolean operators
* Field-specific queries

Keyword search should prioritize precision.

## Semantic Search

Provide:

* Embedding lookup
* Similarity search
* Context-aware retrieval
* Embedding ranking
* Vector filtering

Semantic search should prioritize contextual relevance.

## Metadata Filtering

Support filtering by:

* File type
* Tags
* Author
* Creation date
* Modification date
* Workspace
* Custom metadata

Filtering should operate independently of the retrieval mechanism.

## Hybrid Ranking

The ranking engine should combine:

* Keyword relevance
* Semantic similarity
* Metadata relevance
* Document quality
* Freshness where appropriate

Ranking should produce a single ordered result set regardless of the retrieval source.

## Search Indexing

The indexing system should support:

* Incremental indexing
* Full re-indexing
* Change detection
* Batch indexing
* Background indexing
* Index validation

Indexing operations should execute through the background task manager.

## Search Analytics

Collect operational metrics including:

* Query latency
* Result count
* Index size
* Search frequency
* Failed queries
* Index health

Analytics should support future optimization without affecting retrieval behavior.

## Search Engine Deliverables

* Search orchestrator
* Keyword search provider
* Semantic search provider
* Query preprocessing pipeline
* Metadata filtering
* Hybrid ranking engine
* Index management
* Search analytics
* Unified search service

## Search Engine Completion Criteria

* Documents can be indexed successfully.
* Keyword search returns accurate results.
* Semantic search retrieves contextually relevant documents.
* Metadata filtering functions correctly.
* Hybrid ranking produces unified results.
* Index updates occur reliably.
* Search metrics are collected.
* Background indexing completes without blocking the user interface.

---

# Phase 02 Completion Checklist

## Epic 2.1 — Infrastructure & Providers ✅

- ✅ SQL migration runner (`schema_migrations` table, ordered `.sql` files)
- ✅ Qdrant local file-mode provider (`qdrant_provider.py`) with auto-collection creation
- ✅ `database.py` expanded with connection management and `open_db` / `close_db`
- ✅ `qdrant-client>=1.9` dependency added

## Epic 2.2 — Repository Abstraction ✅

- ✅ `DocumentRepository` — SQLite upsert, SHA-256 hash-based change detection, list by workspace
- ✅ `ChunkRepository` — dual write to SQLite + Qdrant, FTS5 mirror, batch ops, delete by document

## Epic 2.3 — SQLite Schema Expansion ✅

- ✅ Migration `001_conversations.sql` — conversations and messages schema
- ✅ Migration `002_knowledge_schema.sql` — documents, chunks, `chunks_fts` FTS5 virtual table with Porter stemming

## Epic 2.4 — File Indexing Pipeline ✅

- ✅ `TextChunker` — sentence-boundary chunking with configurable overlap (chunk_size=1500, overlap=200)
- ✅ `FileIndexer` — recursive .txt/.md discovery, SHA-256 dedup, background re-index on change, graph build wired
- ✅ `POST /indexing/start` (202 accepted) and `GET /indexing/status/{task_id}` API endpoints
- ✅ `index_workspace` and `get_indexing_status` IPC commands (Rust + TypeScript)

## Epic 2.5 — Semantic Search ✅

- ✅ `QdrantSearchProvider` — embed query → Qdrant nearest-neighbour → SQLite hydration
- ✅ `POST /search/semantic` API endpoint (top_k, workspace_path filter)
- ✅ `search_semantic` IPC command (Rust + TypeScript)
- ✅ Top-5 retrieved fragments injected as system context into every LLM call via `retrievedContext` field

## Epic 2.6 — Keyword Search ✅

- ✅ `KeywordSearchProvider` — FTS5 BM25 query with Porter stemming, safe token escaping (no FTS5 injection)
- ✅ BM25 score normalised to [0, 1] using `1 / (1 + |raw|)` for consistent ranking
- ✅ `POST /search/keyword` API endpoint (workspace filter, top_k 1–50)
- ✅ `search_keyword` IPC command (Rust + TypeScript)
- ✅ `KeywordSearchResponse` type exported from `IPCClient.ts`
- ✅ 19 unit tests — helper functions, search behaviour, workspace filtering, stemming (all passing)

## Epic 2.7 — Query Preprocessing ❌ Not started

- ❌ Query normalisation service
- ❌ Tokenisation / stop-word handling
- ❌ Query expansion pipeline

## Epic 2.8 — Hybrid Search Orchestrator ❌ Not started

- ❌ `HybridSearchOrchestrator` combining keyword + semantic results
- ❌ Reciprocal Rank Fusion or weighted score merge
- ❌ `POST /search/hybrid` API endpoint and IPC command

## Epic 2.9 — Neo4j Knowledge Graph ✅

- ✅ `GraphProvider` abstract interface (7 methods: initialize, upsert_entity, upsert_relationship, get_context, delete_by_document, health, close)
- ✅ `NullGraphProvider` — no-op stub; app runs fully without Docker or Neo4j
- ✅ `Neo4jProvider` — async Bolt driver, uniqueness constraint + name index, MERGE-based upsert, depth-limited traversal
- ✅ `KnowledgeGraphService` — per-chunk LLM entity extraction (best-effort; failures never abort indexing)
- ✅ `llm_client.py` — httpx async wrapper for Volvo GenAI Hub; credentials from env vars only
- ✅ `FileIndexer` updated: graph build wired after chunk/embed persist; stale nodes deleted on re-index
- ✅ `GET /graph/entity/{name}` and `GET /graph/health` API endpoints
- ✅ `get_graph_entity` and `graph_health` IPC commands (Rust + TypeScript, `urlencoding` dep added)
- ✅ `docker-compose.yml` — `neo4j:5-community` service (Bolt 7687, Browser 7474)
- ✅ App startup: `EAC_GRAPH_PROVIDER=neo4j` opt-in; auto-falls back to Null on connection failure
- ✅ `neo4j>=5.0` dependency added
- ✅ 30+ tests: graph models, NullGraphProvider contract, KnowledgeGraphService (mocked LLM), graph endpoint (107 Python tests total passing)

## Epic 2.10 — Backup Foundation ❌ Not started

- ❌ SQLite snapshot mechanism
- ❌ Qdrant collection export stub
- ❌ Graph data export stub

---

## Phase 02 Summary

| Epic | Title | Status | Commit |
|------|-------|--------|--------|
| 2.1 | Infrastructure & Providers | ✅ Done | c9954af |
| 2.2 | Repository Abstraction | ✅ Done | c9954af |
| 2.3 | SQLite Schema Expansion | ✅ Done | c9954af |
| 2.4 | File Indexing Pipeline | ✅ Done | c9954af |
| 2.5 | Semantic Search | ✅ Done | c9954af |
| 2.6 | Keyword Search | ✅ Done | c9954af |
| 2.7 | Query Preprocessing | ❌ Pending | — |
| 2.8 | Hybrid Search Orchestrator | ❌ Pending | — |
| 2.9 | Neo4j Knowledge Graph | ✅ Done | 21b64c4 |
| 2.10 | Backup Foundation | ❌ Pending | — |

**Implemented:** 7 / 10 epics  
**Pending:** 2.7, 2.8, 2.10

---

# Next Phase

After completing the remaining epics (2.7, 2.8, 2.10), proceed to:

**Phase 03 – Workspace Features**

The next phase introduces workspace-specific frontend capabilities, including document management views, search UI, file browsing, and workspace organization features.
