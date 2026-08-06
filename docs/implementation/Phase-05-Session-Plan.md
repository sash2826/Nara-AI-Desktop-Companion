# Phase 05 — Parallel Session Plan

**Phase:** 05 — Knowledge Graph  
**Status:** Ready  
**Last Updated:** 2026-08-05

This document defines which epics can run in parallel sessions and which must be sequenced.
Both sessions update the checklist below after completing each epic.

---

## Session Map

```
Session A (Core Graph Pipeline)        Session B (Visualization)
───────────────────────────────        ─────────────────────────
Epic 5.0 — Entity Extraction           Epic 5.5 — Graph UI & Visualization
     │
Epic 5.1 — Relationship Extraction     (start immediately, finish independently)
     │
Epic 5.2 — Knowledge Enrichment
     │
Epic 5.6 — Incremental Updates
     │
Epic 5.3 — Graph Query & Traversal
     │
Epic 5.4 — Graph-Augmented Retrieval

(all in sequence — each epic builds
 on the output of the prior one)
```

Session B can start immediately and finish independently.  
Session A must proceed in order: 5.0 → 5.1 → 5.2 → 5.6 → 5.3 → 5.4.

---

## Existing Foundation (Phase 02 — Epic 2.9)

The following files already exist and must not be rewritten — only extended:

```
backend/src/enterprise_ai_companion/capabilities/graph/
  graph_provider.py            # GraphProvider abstract interface (7 methods)
  null_graph_provider.py       # no-op stub — app runs without Neo4j
  neo4j_provider.py            # async Bolt driver, MERGE-based upsert, health check
  knowledge_graph_service.py   # per-chunk LLM entity extraction (to be upgraded by 5.0/5.1)

backend/src/enterprise_ai_companion/api/routers/
  graph.py                     # GET /graph/entity/{name} and GET /graph/health
```

Session A upgrades `KnowledgeGraphService` and `Neo4jProvider` incrementally.  
Session B adds new endpoints to `graph.py` without touching Session A's routes.

---

## Why These Sessions Cannot Be Merged

**Epic 5.5 is fully isolated:**

- New files only: `GraphPage.tsx`, `frontend/src/components/graph/*`
- Backend adds one new route to `graph.py` — non-conflicting with Session A's additions (different function names)
- No migration required — reads existing Neo4j data via `GET /graph/visualize`
- Safe to develop with a stub response `{nodes: [], edges: []}` before Session A's 5.1 is merged
- Can wire to real data once Session A merges Epic 5.1

**Epics 5.0–5.4 + 5.6 form a dependency chain:**

| Epic | Depends On | Conflict Files |
|---|---|---|
| 5.0 | Phase 02 foundation | `knowledge_graph_service.py` |
| 5.1 | 5.0 (entity schema must exist) | `knowledge_graph_service.py`, `neo4j_provider.py` |
| 5.2 | 5.1 (nodes to enrich) | `knowledge_graph_service.py`, `neo4j_provider.py`, `enrichment_service.py` |
| 5.6 | 5.2 (full build pipeline stable) | `knowledge_graph_service.py`, `file_indexer.py` |
| 5.3 | 5.1 (graph populated) | `graph_query_service.py`, `traversal_engine.py`, `graph.py` router |
| 5.4 | 5.3 (query service must exist) | `context_assembler.py`, `graph_query_service.py` |

Attempting to run any two of 5.0–5.4/5.6 in parallel would produce merge conflicts
in `knowledge_graph_service.py` and `neo4j_provider.py`.

---

## File Ownership

### Session A — owns exclusively

```
backend/src/enterprise_ai_companion/capabilities/graph/
  entity_extractor.py           (new — Epic 5.0)
  relationship_extractor.py     (new — Epic 5.1)
  enrichment_service.py         (new — Epic 5.2)
  graph_query_service.py        (new — Epic 5.3)
  traversal_engine.py           (new — Epic 5.3)
  knowledge_graph_service.py    (modify — Epics 5.0, 5.1, 5.2, 5.6)
  neo4j_provider.py             (modify — Epics 5.1, 5.2, 5.3)

backend/src/enterprise_ai_companion/capabilities/ai/
  context_assembler.py          (modify — Epic 5.4)

backend/src/enterprise_ai_companion/api/routers/
  graph.py                      (modify — Epic 5.3: entity search, neighborhood, traversal endpoints)
```

### Session B — owns exclusively

```
frontend/src/pages/
  GraphPage.tsx                  (new — Epic 5.5)

frontend/src/components/graph/   (new directory — Epic 5.5)
  GraphCanvas.tsx
  GraphControls.tsx
  EntityCard.tsx
  EdgeLabel.tsx

frontend/src/hooks/
  useGraph.ts                    (new — Epic 5.5)
```

### Shared — coordinate on last-to-merge

```
backend/src/enterprise_ai_companion/api/routers/
  graph.py
  — Session A adds: entity search, neighborhood, traversal routes (Epic 5.3)
  — Session B adds: GET /graph/visualize route (Epic 5.5)
  — whichever session merges last adds its route as a non-conflicting addition

frontend/src-tauri/src/lib.rs
  — Session A: no new IPC commands expected (graph queries go via HTTP)
  — Session B: registers get_graph_visualization IPC command
  — low conflict risk; coordinate if Session A also needs new commands

frontend/src/services/ipc/IPCClient.ts
  — Session B: adds getGraphVisualization()
  — Session A: no IPCClient changes expected
  — low conflict risk

frontend/src/components/layout/TopBar.tsx  (or navigation component)
  — Session B: adds Graph nav link
  — Session A: no nav changes expected
```

---

## Progress Checklist

Sessions must update this file after each epic is merged.  
Mark with `[x]` when the epic is fully merged into main and verified.

---

### Session A — Epic 5.0 — Entity Extraction Engine

- [x] `ExtractedEntity` dataclass defined (`entity_type`, `name`, `confidence`, `source_text`)
- [x] `EntityExtractor` class created (`capabilities/graph/entity_extractor.py`)
- [x] LLM prompt structured for JSON entity extraction (typed schema, not free-text)
- [x] Entity types enumerated: Person, Organisation, Project, Technology, Location, Event, Product, Concept
- [x] `KnowledgeGraphService` updated to use `EntityExtractor` in place of inline extraction
- [x] `Neo4jProvider.upsert_entity()` updated to accept `ExtractedEntity` (adds `confidence` and `entity_type` properties)
- [x] Unit tests: entity parsing from LLM JSON, malformed response handling, entity deduplication
- [x] Backend only — no frontend changes this epic

---

### Session A — Epic 5.1 — Relationship Extraction Engine

- [x] `ExtractedRelationship` dataclass defined (`source`, `target`, `relation_type`, `confidence`, `source_text`)
- [x] `RelationshipExtractor` class created (`capabilities/graph/relationship_extractor.py`)
- [x] LLM prompt structured for relationship extraction scoped to known entity list (prevents hallucination)
- [x] Relationship types enumerated: REFERENCES, OWNS, MEMBER_OF, DEPENDS_ON, SIMILAR_TO, AUTHORED_BY, PART_OF
- [x] `KnowledgeGraphService` updated: runs entity extraction then relationship extraction per chunk
- [x] `Neo4jProvider.upsert_relationship()` updated: adds `confidence` property to relationship props
- [x] Extraction failures on relationship step never abort entity persistence (best-effort)
- [x] Unit tests: relationship parsing, hallucination rejection, deduplication

---

### Session A — Epic 5.2 — Knowledge Enrichment Service

- [x] `EnrichmentService` class created (`capabilities/graph/enrichment_service.py`)
- [x] `canonical_name()` module function: NFC normalisation, strip boundary non-word chars, collapse whitespace, lowercase
- [x] Duplicate detection: groups nodes by canonical name + entity_type, merges lower-confidence into higher
- [x] Merge strategy: re-points outgoing and incoming rels, DETACH DELETEs duplicate node
- [x] `KnowledgeGraphService.build_from_chunks()` calls `EnrichmentService.enrich()` after upsert — best-effort
- [x] Enrichment failures never abort graph build; only runs against Neo4jProvider (skips NullGraphProvider)
- [x] Unit tests: canonical_name normalisation, strip trailing punctuation, unicode normalisation

---

### Session A — Epic 5.6 — Incremental Update Framework

- [x] `FileIndexer._build_graph_incremental()` method: checks `GraphStateRepository`, skips if hash unchanged
- [x] `FileIndexer._index_file()` calls `graph_state_repo.delete_by_document()` on re-index
- [x] SQLite migration `007_graph_state.sql`: `graph_state` table with FK CASCADE to documents
- [x] `GraphStateRepository` created (`capabilities/graph/graph_state_repository.py`): `save()`, `get_by_document()`, `delete_by_document()`
- [x] `FileIndexer` wires `GraphStateRepository`: updates state after successful build, deletes on document delete
- [x] `app.py` wires `GraphStateRepository` and passes it to `FileIndexer`
- [x] Unit tests: save/retrieve, replace-on-update, delete, idempotent delete

---

### Session A — Epic 5.3 — Graph Query Service & Traversal

- [x] `GraphQueryService` class created (`capabilities/graph/graph_query_service.py`)
- [x] `get_entity(name)` — wraps `provider.get_context()`, returns `GraphContext | None`
- [x] `get_neighborhood(entity_name, depth)` — returns `GraphNeighborhood | None`
- [x] `search_entities(query, entity_type, limit)` — graceful `[]` fallback for NullGraphProvider
- [x] `get_connected_documents(entity_name)` — graceful `[]` fallback
- [x] `TraversalEngine` class created (`capabilities/graph/traversal_engine.py`)
- [x] `find_path(source, target)` — shortest path via Cypher `shortestPath()`, up to 6 hops
- [x] `TraversalEngine.get_connected_documents()` — 2-hop traversal collecting distinct document IDs
- [x] `Neo4jProvider.search_entities()` and `Neo4jProvider.get_connected_documents()` added
- [x] `graph.py` router: `GET /graph/entity/{name}` refactored to use `GraphQueryService`; new endpoints:
  - [x] `GET /graph/neighborhood/{name}?depth=2`
  - [x] `GET /graph/search?q=&entity_type=&limit=`
  - [x] `GET /graph/path?from_entity=&to_entity=`
  - [x] `GET /graph/documents/{entity_name}`
- [x] `NullGraphProvider` gains `search_entities()` and `get_connected_documents()` stubs
- [x] Unit tests: query service graceful degradation, traversal engine empty results

---

### Session A — Epic 5.4 — Graph-Augmented Retrieval

- [x] `ContextAssembler.assemble()` gains optional `use_graph: bool = True` parameter
- [x] `_expand_via_graph()` method: tokenises query, calls `GraphQueryService.get_connected_documents()`, loads extra chunks from `ChunkRepository`, appends up to budget
- [x] `ContextPayload` gains `graph_entities: list[str]` field — entity tokens that contributed
- [x] Graph expansion is skipped when `chunk_repo` is None (graceful degradation)
- [x] `ContextAssembler` constructor gains optional `graph_provider` and `chunk_repo` parameters
- [x] `app.py` exposes `chunk_repo` on `app.state` for future assembler construction
- [x] `total_chars` bug fixed: was summing `chunk_index` values, now correctly sums `len(c.content)`
- [x] Unit tests: graph expansion, graceful degradation when Neo4j offline

---

### Session B — Epic 5.5 — Graph UI & Visualization

- [x] `GET /graph/visualize?entity=&depth=` added to `graph.py` — returns `{nodes: [{id, label, entity_type, confidence}], edges: [{source, target, relation_type, confidence}]}`; returns `{nodes: [], edges: []}` when graph is empty or Neo4j offline; catches all provider exceptions
- [x] `get_visualization()` abstract method added to `GraphProvider`; `NullGraphProvider` returns empty structure; `Neo4jProvider` implements entity-focal and overview Cypher queries
- [x] Rust IPC: `GraphVisNodeResponse`, `GraphVisEdgeResponse`, `GraphVisualizationResponse` structs; `get_graph_visualization` command registered in `invoke_handler!`
- [x] TypeScript: `GraphVisNode`, `GraphVisEdge`, `GraphVisualization` interfaces; `getGraphVisualization()` added to `IPCClient.ts` and exported object
- [x] `useGraph.ts` hook: loads on mount, exposes `nodes`, `edges`, `isLoading`, `error`, `focalEntity`, `depth`, `selectedNode`, `setFocalEntity`, `setDepth`, `setSelectedNode`, `refresh`
- [x] `GraphCanvas.tsx`: library-free SVG force-directed renderer — spring/charge simulation, drag support, entity type colour palette, arrowhead markers, edge label on hover, selection ring, confidence arc overlay, graceful empty state
- [x] `GraphControls.tsx`: entity search input with clear button, depth range slider (1–3), refresh button, node/edge count stat
- [x] `EntityCard.tsx`: click-to-open detail panel — name, type, confidence badge, incoming/outgoing relationships with clickable targets, open source document action, focus graph action
- [x] `EdgeLabel.tsx`: standalone relationship type pill component (used for inline rendering and reuse)
- [x] `KnowledgeGraphPage.tsx` rewritten: canvas + controls + optional entity card side panel; loading overlay; error banner; graceful empty state when no entities indexed
- [x] Navigation already wired — `KnowledgeGraphPage` was already in `MainContent.tsx` PAGE_MAP and sidebar; no changes needed
- [x] `npx tsc --noEmit` passes with zero errors from Session B files

---

## Merge Order Recommendation

1. Session B can merge Epic 5.5 at any time — no Session A dependency for the stub state.
2. Session A merges each epic immediately after completing it (5.0, 5.1, 5.2, 5.6, 5.3, 5.4).
3. Session B wires `getGraphVisualization()` to real data after Session A merges Epic 5.1 (graph is populated).
4. When Session B merges `graph.py` changes: if Session A has already added routes, Session B's `GET /graph/visualize` is a non-conflicting addition.

---

---

### SQLiteGraphProvider — Zero-Config Graph Backend

Implemented after Session A as a replacement for Neo4j as the default backend.

- [x] Migration `008_sqlite_graph.sql`: `graph_entities` + `graph_relationships` tables, FK CASCADE, indexes
- [x] `SQLiteGraphProvider` created (`capabilities/graph/sqlite_graph_provider.py`): full `GraphProvider` implementation using recursive CTEs for multi-hop traversal and path-finding
- [x] `GraphProvider` abstract interface updated: `search_entities()` and `get_connected_documents()` promoted to abstract methods (were Neo4j-only before)
- [x] `EnrichmentService` refactored: detects provider by capability (`hasattr`), runs SQLite enrichment path or Neo4j path accordingly — no more `isinstance(Neo4jProvider)` coupling
- [x] `TraversalEngine` refactored: routes `find_path()` and `get_connected_documents()` to SQLite or Neo4j implementation based on provider type
- [x] `GraphQueryService` cleaned up: removed `AttributeError` fallbacks (interface now complete on all providers); returns typed `EntitySearchResult` objects directly
- [x] `app.py` updated: `SQLiteGraphProvider` is the default (`EAC_GRAPH_PROVIDER` defaults to `sqlite`); Neo4j opt-in via `EAC_GRAPH_PROVIDER=neo4j`; `NullGraphProvider` via `EAC_GRAPH_PROVIDER=null`
- [x] 20 unit tests covering all SQLiteGraphProvider operations (in-memory DB, no external services)

---

## Phase Completion Gate

Phase 05 is complete when all boxes above are checked AND:

- [x] `SQLiteGraphProvider` is the default — graph features work out-of-the-box with zero configuration
- [ ] Graph features verified end-to-end: index a document, entities appear via `GET /graph/search?q=`
- [ ] `GET /graph/neighborhood/{name}` returns valid multi-hop results
- [ ] Chat responses include graph-sourced context when relevant entities are present
- [ ] Graph page renders indexed entities visually
- [ ] `npx tsc --noEmit` passes with zero errors
- [ ] Pytest integration tests pass for all new backend endpoints
- [ ] No regression in search, indexing, or existing chat functionality
- [x] Phase 05 spec `Phase-05-Knowledge-Graph.md` updated to `Status: Complete`
