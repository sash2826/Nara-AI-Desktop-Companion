# Phase 03: Workspace Features

**Phase:** 03

**Status:** Planned

**Estimated Duration:** 3-5 Days

---

# Purpose

Phase 03 implements the workspace-specific user interface and frontend capabilities of the Enterprise AI Companion.

The objective is to surface the data, search, and knowledge capabilities introduced in Phase 02 through a coherent, usable workspace experience that keeps the assistant at the centre of the interface.

At the completion of this phase, users should be able to create and manage workspaces, browse indexed documents, perform searches, and see results within the application.

---

# Objectives

Upon completion of this phase, the application should provide:

* Workspace creation and management
* Document browser
* Search interface
* Search results view
* File metadata display
* Workspace settings
* Indexing status and progress
* Document preview

No AI-generated content is required during this phase.

---

# Prerequisites

Before beginning this phase:

* Phase 00 must be completed.
* Phase 01 must be completed.
* Phase 02 must be completed.
* Search engine should be operational.
* Database providers should be available.

---

# Epic 3.0 — Background Indexing Service ✅

**Status:** Complete

This epic extends the Phase 02 indexing pipeline with automatic background indexing, persisted watched folder management, and support for additional file types. It is a prerequisite for the workspace management UI in Epic 3.1+.

## Deliverables

### Watched Folders (SQLite migration 003)

A new `watched_folders` table persists user-configured indexing paths across restarts:

```sql
CREATE TABLE IF NOT EXISTS watched_folders (
    id TEXT PRIMARY KEY, path TEXT NOT NULL UNIQUE,
    auto_index INTEGER NOT NULL DEFAULT 1, added_at TEXT NOT NULL
);
```

### WatcherService (`capabilities/indexing/file_watcher.py`)

- `WatcherService` — manages a `watchdog.Observer` that monitors registered folders in a background OS thread
- `DebounceHandler` — collapses rapid filesystem events (editor save pattern) into a single index call after a 2-second quiet window
- `EXCLUDED_DIRS` — skips system/hidden directories (`Windows`, `AppData`, `.git`, `node_modules`, etc.)
- Thread boundary bridged via `asyncio.run_coroutine_threadsafe` so the async `FileIndexer` can be called safely from the watchdog thread
- Folder operations (`add_folder`, `remove_folder`, `list_folders`) persist to SQLite and register/unregister live watches immediately

### Extended File Type Support

`FileIndexer._extract_text()` dispatcher added — supports:

| Extension | Extraction method |
|---|---|
| `.txt`, `.md` | `Path.read_text()` |
| `.pdf` | `pypdf.PdfReader` — extracts all page text |
| `.docx` | `python-docx Document` — joins all paragraph text |

### API Endpoints (`api/routers/watcher.py`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/watcher/folders` | Register folder; triggers immediate initial index |
| `DELETE` | `/watcher/folders/{id}` | Unregister folder |
| `GET` | `/watcher/folders` | List all watched folders |
| `GET` | `/watcher/status` | Running state, watched count, folder paths |

### IPC Commands (Tauri + TypeScript)

Four new Rust commands registered in `invoke_handler` and matching TypeScript functions in `IPCClient.ts`:
`addWatchedFolder`, `removeWatchedFolder`, `listWatchedFolders`, `getWatcherStatus`

### Dependencies Added

```
watchdog>=4.0   # filesystem event monitoring
pypdf>=4.0      # PDF text extraction
python-docx>=1.0  # DOCX text extraction
```

## Tests

- `tests/test_file_watcher.py` — 20 tests: `_is_excluded`, `DebounceHandler`, `WatcherService` lifecycle + CRUD
- `tests/test_watcher_api.py` — 8 endpoint tests via `TestClient`
- `tests/test_file_indexer.py` — extended with 6 PDF/DOCX extraction tests (total: 248 passing)

---

# Epic 3.2 (Track 2) — Search Interface ✅

**Status:** Complete

## Deliverables

### Store — `src/store/searchStore.ts`

Zustand store holding `query`, `mode` (`"semantic" | "keyword"`), `filters` (`topK`, `workspacePath`), `results`, `isSearching`, `error`, `hasSearched`. Full set/clear actions.

### Service — `src/services/search/SearchService.ts`

`SearchService.search()` delegates to `IPCClient.searchSemantic` or `IPCClient.searchKeyword` based on mode. Returns `SearchResponse` with results, mode, and `durationMs` measured via `performance.now()`.

### Hook — `src/hooks/useSearch.ts`

`useSearch()` wires the store and service. Cancels in-flight requests via `AbortController` on each new search. Exposes `search()`, `clear()`, and all store state as a flat API for components.

### Components — `src/components/search/`

| File | Description |
|---|---|
| `SearchInput.tsx` | Controlled input with animated search/spinner icon, clear button, Enter-to-search, Escape-to-clear |
| `SearchModeSelector.tsx` | Segmented control (Semantic / Keyword) with icon + ARIA tab role |
| `SearchFilters.tsx` | Result count selector (5/10/20/50) + workspace path text filter |
| `SearchResultCard.tsx` | Ranked result card — filename, score %, content excerpt with query term highlighting, truncated path, chunk index |
| `EmptySearchState.tsx` | Two states: pre-search prompt and no-results message |

### Page — `src/pages/SearchPage.tsx`

Replaces placeholder. Layout: search bar + mode selector row → filters row → optional error banner → scrollable results list or empty state. Zero layout shift between states.

## No Backend Changes

All IPC commands (`searchSemantic`, `searchKeyword`) were already implemented in Phase 02.

---

# Epic 3.3 (Track 3) — Settings Page ✅

**Status:** Complete

## Deliverables

### Store — `src/store/settingsStore.ts`

Zustand store holding `AppSettings` (theme, sidebarCollapsed, aiProvider, indexing). Hydrates from `eac-settings` localStorage key on first load with deep-merge against defaults. `saveSettings()` persists; `resetToDefaults()` wipes back to defaults. `isDirty` flag enables the Save button only when there are unsaved changes.

### Service — `src/services/settings/SettingsService.ts`

Thin wrapper around `IPCClient.createBackup` / `IPCClient.listBackups`. Pure preference persistence is handled by the store directly.

### Hook — `src/hooks/useSettings.ts`

`useSettings()` bridges the store with `ThemeProvider` so theme changes in the Settings panel are applied immediately to the document. Exposes `save()`, `reset()`, and typed `update*` helpers.

### Components — `src/components/settings/`

| File | Description |
|---|---|
| `GeneralSettings.tsx` | Three-option theme picker (Light / Dark / System) with icon tiles |
| `AIProviderSettings.tsx` | Endpoint URL, masked subscription key (show/hide toggle), model ID, timeout, max retries. Shows env var hint. |
| `IndexingSettings.tsx` | Chunk size, chunk overlap, max file size, auto-index on startup checkbox |
| `BackupSettings.tsx` | Create Backup button, Refresh, scrollable backup list with status badges and file sizes. Live feedback on success/error. |

### Page — `src/pages/SettingsPage.tsx`

Replaces placeholder. Left sidebar tab navigation (General / AI Provider / Indexing / Backup) with Save and Reset buttons anchored at the bottom. Vertical divider separates nav from the active panel. Unsaved changes disable the Save button until `isDirty` is true.

## No New Backend Work

Backup IPC commands (`createBackup`, `listBackups`) were already implemented in Phase 02 Epic 2.10.

---

# Workspace Architecture

Workspace features should follow the frontend feature-oriented architecture established in Phase 00.

```text
src/
│
├── pages/
│   ├── workspace/
│   ├── search/
│   ├── documents/
│   └── settings/
│
├── components/
│   ├── workspace/
│   ├── search/
│   └── documents/
```

Each feature area should remain independently navigable.

---

# Workspace Management

Provide support for:

* Workspace creation
* Workspace selection
* Workspace settings
* Folder mapping
* Workspace deletion
* Workspace status

A workspace represents a user-defined scope of indexed content.

---

# Document Browser

The document browser should support:

* Folder navigation
* File listing
* File type filtering
* Sorting
* Metadata display
* Indexing status per file
* Bulk selection
* Document actions (open, re-index, exclude)

The browser should communicate with backend services through the IPC layer.

---

# Search Interface

Provide a search page containing:

* Search input
* Filter controls (file type, date, workspace, tags)
* Result list
* Result cards with metadata
* Highlighted matches
* Pagination or virtual scrolling
* Empty states
* Error states

Search should feel fast and responsive regardless of result count.

---

# Indexing Status

Surface indexing progress through:

* Global indexing indicator
* Per-workspace status
* Per-file indexing state
* Background task progress
* Error reporting for failed files
* Re-index triggers

Users should always understand the current state of their indexed content.

---

# Document Preview

Provide basic document preview support for:

* Plain text
* Markdown
* PDF page preview (where available)
* Metadata summary

Full document rendering is not required during this phase.

---

# User Experience Principles

* Workspace navigation should feel natural and predictable.
* Search results should appear without perceptible delay.
* Indexing should never block the user interface.
* Empty workspace states should guide the user toward adding content.

---

# Deliverables

Completion of this phase should produce:

* Workspace management pages
* Document browser
* Search interface
* Search results view
* Indexing status indicators
* Document preview

---

# Completion Criteria

This phase is complete when:

* Workspaces can be created and selected.
* Documents are listed and browsable.
* Search returns results from the backend.
* Filters narrow results correctly.
* Indexing progress is visible.
* Document preview displays basic content.
* All views remain responsive during backend operations.

---

# Dependencies

Requires:

* Phase 00
* Phase 01
* Phase 02

Provides workspace UI for:

* Phase 04
* Phase 05
* Phase 06
* Phase 07
* Phase 08

---

# Related Documentation

* `docs/architecture/application-layers.md`
* `docs/decisions/ADR-007-IPC-Communication.md`
* `docs/decisions/ADR-008-Search-Architecture.md`

---

# Next Phase

After completing this phase, proceed to:

**Phase 04 – Intelligence Layer**

The next phase implements the knowledge graph, enabling entity extraction, relationship discovery, semantic linking, graph traversal, and contextual reasoning across the indexed workspace.
