# Backlog

Items deferred from completed phases. Each entry records what was deferred, why, and the recommended follow-up.

---

## Connectors & Data Sources

### OneDriveConnector — full OAuth 2.0 flow
**Deferred from:** Phase 0 / indexing capability bootstrap  
**Why:** OAuth device-flow or PKCE requires a Tauri deep-link or redirect handler that was out of scope for the initial indexing milestone.  
**Recommended:** Implement as a dedicated connector in Phase 08 (Connectors). Requires `tauri-plugin-deep-link` or an embedded OAuth redirect server, plus a `connectors/onedrive/` capability module following the same `FileConnector` interface pattern.

### LocalFileConnector — full implementation
**Deferred from:** Phase 0  
**Why:** The indexing MVP reads files directly via `FileIndexer.index_workspace()`. A formal `LocalFileConnector` class implementing a `FileConnector` interface was planned but not required for Phase 0 functionality.  
**Recommended:** Extract direct file access from `FileIndexer` into a `LocalFileConnector` class during the Phase 08 connector work, so all data sources share the same interface.

### ProjectKnowledgeRepository — live implementation
**Deferred from:** Phase 0  
**Why:** The initial system design included a `ProjectKnowledgeRepository` as an abstraction over structured project data. The current codebase handles this through raw SQLite queries in the router layer.  
**Recommended:** Introduce when a second project-data consumer is added to avoid duplicating query logic.

---

## Notifications

### Notification service delivery (email / push / webhook)
**Deferred from:** Phase 0 notification scaffold  
**Why:** The notification infrastructure was scaffolded (event types defined) but delivery adapters (email, OS push, webhook) were deferred pending a concrete use case.  
**Recommended:** Implement alongside Phase 07 automation triggers, where rules that fire need to notify the user.

---

## Knowledge Graph

### NullGraphProvider — stub completeness
**Deferred from:** Phase 05 knowledge graph  
**Why:** `NullGraphProvider.search_entities()` and `get_connected_documents()` return empty lists. This is correct for the null-object pattern but means graph-dependent search paths silently return nothing when Neo4j is unavailable.  
**Recommended:** Leave as-is unless the application starts showing degraded-mode UI. The `SQLiteGraphProvider` is the default and covers all production paths.

### Full Neo4j wiring
**Deferred from:** Phase 05  
**Why:** `Neo4jProvider` implements the `GraphProvider` interface but the full indexing path (entity extraction → Neo4j write) was not wired end-to-end. All production paths use `SQLiteGraphProvider`.  
**Recommended:** Complete when there is a requirement for a hosted Neo4j instance (e.g. team-shared graph). Requires updating `_build_graph_provider()` in `app.py` and validating schema compatibility.

---

## Plugin System

### SearchEnricherPlugin — wiring into search pipeline
**Deferred from:** Phase 06B (plugin foundation)  
**Why:** The `SearchEnricherPlugin` ABC is defined in `plugin_interfaces.py` and plugin authors can implement it, but the search pipeline in `routers/search.py` does not yet call enrichers. Wiring it requires a clean search-result model shared between the search router and the enricher interface.  
**Recommended:** Wire during Phase 07 when the search pipeline is refactored for automation hooks. The enricher call site is the post-RRF merge step in `SearchService.hybrid_search()`.

---

## Infrastructure

### Sidecar production bundling
**Deferred from:** Phase 08 (production packaging)  
**Why:** The Python sidecar runs as a subprocess launched from the Tauri binary. For production distribution the sidecar must be bundled as a PyInstaller or Nuitka executable inside the Tauri bundle. Development currently requires a Python environment to be present.  
**Recommended:** Tackle during Phase 08 (Production & Distribution). Reference: Tauri `externalBin` config.

### IPC token in WebView memory — acknowledged limitation
**Deferred from:** Phase 06 (security hardening)  
**Why:** The `EAC_IPC_SECRET` token is generated per-session and held in Rust `AppState`. It never touches the filesystem or logs. However, the Tauri WebView process runs in the same OS session and in theory could read process memory. This is an accepted architectural limitation of the Tauri IPC model.  
**Recommended:** No action needed unless the threat model changes to include a compromised WebView (e.g. arbitrary JS execution via content injection). If that becomes a concern, migrate to Tauri's capability-based IPC permissions model (Tauri v2 permissions).

---

## Testing

### End-to-end test suite
**Deferred from:** every phase  
**Why:** Unit and integration tests exist for backend modules. No automated E2E tests cover the full Tauri + React + Python sidecar stack.  
**Recommended:** Add E2E tests using Tauri's WebDriver integration (or a mock sidecar) in a dedicated `tests/e2e/` pass. Target the golden path: launch → index folder → search → graph context.

---

---

## Graph Correctness (Pre-08 blocker)

### get_connected_documents — unbounded recursive CTE
**Deferred from:** Phase 06 audit  
**Why:** The recursive CTE in `SQLiteGraphProvider.get_connected_documents()` has no depth limit. For large graphs this causes excessive traversal and corrupts placement recommendation scores in Phase 09.  
**Recommended:** Apply before Phase 08. Cap traversal at 2 hops, mirroring `_reachable_ids_from_id(depth=2)`. Also fix `get_context` case-sensitive name match (`WHERE name = ?` → `WHERE lower(name) = lower(?)`).

---

## File Organisation

### Bulk accept for suggestions inbox
**Deferred from:** Phase 09/10 design  
**Why:** "Accept all Strong matches" was noted as a useful UX enhancement but scoped out to keep Phase 09 focused on the core recommendation and move flow.  
**Recommended:** Add in a future UX polish pass after Phase 10.

### SearchEnricherPlugin wiring
**Deferred from:** Phase 06B  
**Why:** The `SearchEnricherPlugin` ABC exists but the search pipeline does not call enrichers. The clean wiring point is the post-RRF merge step in `SearchService.hybrid_search()`. Reassess when Phase 07 (Automation) is scheduled — the refactor belongs there.

---

## Orb / UI

### Volvo/Scandinavian main app design
**Deferred from:** Phase 08 design session (2026-08-11)  
**Why:** The user will decide the Volvo/Scandinavian visual direction separately. The main EAC window retains its current dark theme until that decision is made.  
**Recommended:** Treat as a dedicated design + implementation phase once direction is confirmed.

---

*Last updated: 2026-08-11*
