# Phase 10: File Organisation — Existing Files

**Phase:** 10

**Status:** Complete

**Completed:** 2026-08-18

---

> **Clustering UI note:** Scenario 3 (Intelligent Folder Discovery) is fully implemented in the backend — the clustering pipeline, proposal repository, REST endpoints, and scoring are all production-ready. The UI surface (Discover Folders button and Folder Proposals list in the Organise tab) is **hidden** pending final folder-naming quality validation. Set `CLUSTER_UI_ENABLED = true` in `frontend/src/components/workspace/OrganiseTab.tsx` to re-enable it.

---

# Purpose

Phase 09 handles files as they arrive. Phase 10 handles everything already indexed.

This phase introduces two complementary mechanisms: an on-demand audit that analyses all indexed files and produces a batch of reorganisation suggestions, and a passive background layer that surfaces new suggestions over time as the knowledge graph matures and relationships between documents become clearer.

---

# Objectives

Upon completion of this phase the application should provide:

* An "Organise" button in the main Document-Management-RAG-Graph-Agent application that triggers a full indexed-file audit.
* Batch placement recommendations produced for files whose current location scores poorly against better-matching folders.
* Passive background suggestions that surface gradually as the knowledge graph evolves.
* All suggestions delivered through the same orb notification channel and Suggestions inbox established in Phase 09.
* The same 70/30 graph/rerank confidence formula used for new-file recommendations.
* No file is ever moved without explicit user consent.

---

# Prerequisites

Before beginning this phase:

* Phase 09 (File Organisation — New Files) must be complete.
* The `PlacementScorer`, `RecommendationService`, `FileMover`, and `file_placement_recommendations` table must all be operational.

---

# Design Decisions

All decisions below were settled during the Phase 08/09/10 grilling session (2026-08-11).

## On-Demand Audit

The user triggers the audit from a prominent "Organise my files" button in the main Document-Management-RAG-Graph-Agent app (location TBD during UI design). The audit:

1. Iterates every `IndexedDocument` in SQLite.
2. Skips files that already have a pending or recently accepted recommendation.
3. For each file, runs `PlacementScorer` against all candidate folders except the file's current folder.
4. If the top candidate scores materially higher than the file's current folder (`score_delta > 0.20`), a recommendation is created with status `pending`.
5. Results are batched — the user sees a summary ("23 files could be better organised") and can step through them in the Suggestions inbox.

The audit runs as a background task so it does not block the UI. Progress is reported via the existing `progress_cb` pattern.

## Passive Background Suggestions

Each time `FileIndexer` completes indexing a file (new or modified), the `RecommendationService` re-evaluates a small random sample of already-indexed files from the same community cluster. If a materially better folder emerges for any sampled file, a suggestion is added to pending.

This is deliberately low-frequency — sampling prevents the background layer from hammering the scoring pipeline. The goal is that over weeks of normal use, Document-Management-RAG-Graph-Agent gradually surfaces reorganisation opportunities the user did not know to ask for.

## Deduplication

A file cannot have more than one `pending` recommendation at a time. If a new score would replace an existing pending recommendation for the same file, the higher-scoring one wins and the older record is superseded.

## Suggestion Threshold

Only recommendations with a top-candidate score ≥ 0.55 and a score delta ≥ 0.20 above the file's current folder are surfaced. This prevents noise from low-confidence suggestions cluttering the inbox.

## User Experience

The Suggestions inbox (introduced in Phase 09) handles both new-file and existing-file recommendations in a unified list, sorted by confidence descending. Each item shows:

* File name and current location
* Suggested destination with confidence label
* Accept / Skip / Open file buttons

Bulk actions ("Accept all Strong matches") are deferred to a later enhancement.

## Real-Time Overlay Refresh

The orb notification overlay polls `list_pending_recommendations` every 5 seconds while it is open. When files are deleted from Downloads (or recommendations are dismissed externally), the overlay list updates automatically without requiring the user to close and reopen it. The pending count in the orb badge is also updated on each poll, so the amber glow clears within 5 seconds of all recommendations being resolved.

---

# Architecture

## New Backend Modules

```
backend/src/enterprise_ai_companion/capabilities/organisation/
    audit_service.py            — Iterates all IndexedDocuments, runs PlacementScorer, creates batch recommendations
    passive_suggester.py        — Hooks into post-index callback, samples cluster peers, scores
```

## Modified Files

```
backend/.../capabilities/indexing/file_indexer.py   — Call passive_suggester.on_file_indexed() in progress_cb
backend/.../api/routers/organisation.py             — Add POST /organisation/audit endpoint
backend/.../api/app.py                              — Register AuditService on app.state
frontend/src/...                                    — "Organise" button wired to /organisation/audit
```

---

# Deliverables

* AuditService with configurable score delta threshold.
* PassiveSuggester integrated into the post-index callback.
* "Organise" button in the main Document-Management-RAG-Graph-Agent app triggering the audit as a background task.
* Progress reporting during audit via existing IPC progress mechanism.
* Deduplication logic preventing duplicate pending recommendations per file.
* Unified Suggestions inbox showing both new-file and existing-file recommendations.

---

# Completion Criteria

* Clicking "Organise" starts a background audit and shows progress.
* Audit produces recommendations only for files with score delta ≥ 0.20.
* Passive suggester adds recommendations without blocking the post-index flow.
* No duplicate pending recommendations exist for the same file.
* Suggestions inbox shows combined list from Phase 09 and Phase 10 sources.
* Accepting a recommendation from the audit moves the file and updates records identically to Phase 09.
* No file is ever moved without user action.

---

# Dependencies

Requires:
* Phase 09 (File Organisation — New Files)

Provides context for:
* Phase 07 (Automation Engine) — passive suggestions are a lightweight precursor to rule-based automation

---

# Related Documentation

* `docs/implementation/Phase-09-File-Organisation-New-Files.md`
* `docs/implementation/Phase-07-Automation.md`
* `docs/decisions/ADR-008-Search-Architecture.md`

---

# Next Phase

After completing this phase, review Phase 07 (Automation Engine) and proceed when approved.
