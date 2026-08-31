# Phase 09: File Organisation — New Files

**Phase:** 09

**Status:** Planned

**Estimated Duration:** 4–6 Days

---

# Purpose

This phase implements intelligent placement recommendations for files that arrive in the OS Downloads folder.

When a new file lands in Downloads, Document-Management-RAG-Graph-Agent indexes it automatically, scores every known folder against the file's content using a combined knowledge graph and rerank signal, and presents the top three placement suggestions via the orb notification overlay. If the user accepts a suggestion, Document-Management-RAG-Graph-Agent physically moves the file to the target folder and updates all internal records without re-indexing.

---

# Objectives

Upon completion of this phase the application should provide:

* Automatic watch of the OS Downloads folder on first launch (no user setup required).
* Post-index placement recommendation pipeline triggered by any new file in Downloads.
* Top 3 folder recommendations with confidence labels (Strong match / Possible / Alternative).
* Orb notification prompt delivered via the Phase 08 orb overlay.
* Physical file move to the accepted folder, with SQLite path and Qdrant record updated in place.
* Pending recommendations persisted — file stays in Downloads until the user decides.
* Pending recommendations accessible from the orb notification overlay and from a dedicated inbox inside the main Document-Management-RAG-Graph-Agent app.
* No file is ever moved without explicit user consent.

---

# Prerequisites

Before beginning this phase:

* Phase 08 (Orb Native Shell) must be complete — the orb overlay is the notification surface.
* Pre-08 SQLite graph correctness fixes must be applied — unbounded CTE and case-sensitivity bugs corrupt recommendation scores.

---

# Design Decisions

All decisions below were settled during the Phase 08/09 grilling session (2026-08-11).

## Downloads Watch

Document-Management-RAG-Graph-Agent registers the OS Downloads folder (`%USERPROFILE%\Downloads`) as a watched folder automatically on first launch. It is treated identically to any other watched folder for indexing purposes, with one addition: new files arriving here enter the placement recommendation pipeline instead of being silently indexed.

Existing watched folders do not trigger placement recommendations. Files already in Downloads at the time Document-Management-RAG-Graph-Agent first watches it do not trigger recommendations (they are handled by Phase 10's on-demand audit).

## Confidence Scoring Formula

Placement recommendations are scored using a weighted combination of two signals:

```
score = 0.70 × graph_score + 0.30 × rerank_score
```

**graph_score**: Community overlap between the new file's extracted entities and the entities associated with documents already in the candidate folder. Uses the fixed 2-hop traversal from the Pre-08 graph correctness fix.

**rerank_score**: Cross-encoder rerank similarity between the new file's text chunks and the existing document chunks in the candidate folder, using the existing `RerankService`.

Only folders that are already watched and indexed by Document-Management-RAG-Graph-Agent are considered as candidates.

## Recommendation Presentation

The orb transitions to the Notification Pending state (amber glow) as soon as scoring completes. Clicking the orb opens the notification overlay showing:

```
📄 quarterly-report.pdf arrived in Downloads

Where should this go?

1. Reports/Q3/Finance        ████████░░  Strong match  (0.87)
2. Projects/Volvo-2026       █████░░░░░  Possible      (0.61)
3. Archive/2025              ███░░░░░░░  Alternative   (0.44)

[Move to #1]  [Choose folder…]  [Keep in Downloads]
```

"Move to #1" accepts the top recommendation. "Choose folder…" opens a native folder picker. "Keep in Downloads" dismisses and marks the recommendation as deferred.

## File Move and Record Update

On acceptance:
1. File is physically moved on disk using `shutil.move()`.
2. The existing `IndexedDocument` SQLite record is updated in place — same `id`, new `file_path`.
3. Qdrant vector metadata is updated via `client.set_payload()` — same point IDs, new path field.
4. No re-embedding or re-extraction is performed (content has not changed).
5. A `FileOrganisationEvent` is written to the audit log.

## Pending Recommendations

If the user dismisses or ignores a recommendation, it is persisted in a new `file_placement_recommendations` SQLite table with status `pending`. The orb continues to glow amber while any pending recommendations exist. The main Document-Management-RAG-Graph-Agent app exposes a "Suggestions" inbox listing all pending items.

---

# Architecture

## New Backend Modules

```
backend/src/enterprise_ai_companion/capabilities/organisation/
    __init__.py
    placement_scorer.py         — Combines graph_score + rerank_score for each candidate folder
    recommendation_service.py   — Orchestrates scoring, persists results, triggers orb notification
    file_mover.py               — shutil.move wrapper + SQLite + Qdrant record update
    recommendation_repository.py — CRUD for file_placement_recommendations table

backend/src/enterprise_ai_companion/api/routers/
    organisation.py             — REST endpoints for recommendations inbox
```

## New Database Migration

```
database/migrations/011_file_placement_recommendations.sql

CREATE TABLE IF NOT EXISTS file_placement_recommendations (
    id              TEXT PRIMARY KEY,
    source_path     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending | accepted | dismissed
    recommendations TEXT NOT NULL,                    -- JSON array [{folder, score, label}]
    accepted_folder TEXT,
    created_at      TEXT NOT NULL,
    resolved_at     TEXT
);
```

## Modified Files

```
backend/.../capabilities/indexing/file_watcher.py   — Hook Downloads new-file events into RecommendationService
backend/.../capabilities/indexing/file_indexer.py   — Pass progress_cb result to RecommendationService for Downloads files
backend/.../api/app.py                              — Register organisation router; place RecommendationService on app.state
frontend/src/windows/orb/OrbNotificationOverlay.tsx — Render recommendation list fetched from /organisation/recommendations
frontend/src/pages/SettingsPage.tsx or new page     — "Suggestions" inbox in main Document-Management-RAG-Graph-Agent app
```

## New Tauri IPC Commands

```
accept_recommendation(recommendation_id, folder_path)
dismiss_recommendation(recommendation_id)
list_pending_recommendations()
```

---

# Deliverables

* Downloads folder auto-watched on first launch.
* PlacementScorer combining 70/30 graph/rerank formula.
* RecommendationService triggered post-index for Downloads files.
* Top-3 recommendations with confidence labels surfaced via orb overlay.
* Physical file move with in-place SQLite and Qdrant record update.
* Pending recommendations persisted and accessible from orb and main app.
* Migration 011 applied cleanly.
* Audit log entry for every accepted move.

---

# Completion Criteria

* A file dropped into Downloads triggers indexing within 2 seconds (debounce).
* Orb transitions to amber Notification Pending state after scoring completes.
* Clicking orb shows top-3 recommendations with correct scores.
* Accepting a recommendation physically moves the file and updates all records.
* No re-indexing occurs after the move.
* Dismissing a recommendation leaves the file in Downloads and persists the pending record.
* Pending count badge in main Document-Management-RAG-Graph-Agent app reflects unresolved recommendations.
* No file is ever moved without user action.

---

# Dependencies

Requires:
* Phase 08 (Orb Native Shell)
* Pre-08 graph correctness fixes

Provides the foundation for:
* Phase 10 (File Organisation — Existing Files)

---

# Related Documentation

* `docs/implementation/Phase-08-Orb-Native-Shell.md`
* `docs/implementation/Phase-10-File-Organisation-Existing-Files.md`
* `docs/decisions/ADR-002-Data-Storage-Strategy.md`
* `docs/decisions/ADR-008-Search-Architecture.md`

---

# Next Phase

After completing this phase, proceed to:

**Phase 10: File Organisation — Existing Files**
