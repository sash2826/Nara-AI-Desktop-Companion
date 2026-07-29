# ADR-013: Repository Root Layout

**Status:** Accepted

**Date:** 2026-07-29

**Decision Makers:** Project Architecture Team

---

# Context

The architecture specification document (`docs/architecture/repository-layout.md`) defines
the canonical repository structure as:

```text
Enterprise-AI-Companion/
├── apps/
│   ├── desktop/      ← Tauri + React desktop application
│   └── backend/      ← Python backend service
└── packages/
    ├── shared/
    ├── types/
    └── config/
```

During Phase 00 implementation the repository was scaffolded using a flatter layout:

```text
Enterprise-AI-Companion/
├── frontend/         ← Tauri + React desktop application
└── backend/          ← Python backend service
```

The `packages/` monorepo layer was omitted entirely because no shared packages
exist yet.

This discrepancy was identified at the end of Phase 00 and flagged as an open item
requiring a formal decision before Phase 01 continued.

---

# Decision

The `frontend/` / `backend/` flat layout is accepted as the canonical layout for
Version 1 of the Enterprise AI Companion.

The `docs/architecture/repository-layout.md` document will be updated to reflect
this layout.

The migration to `apps/desktop/` and `apps/backend/` is deferred until the
`packages/` monorepo layer is genuinely needed (i.e., when a shared library is
extracted that is consumed by both applications).

---

# Rationale

## The monorepo layout adds no value without shared packages

The `apps/` prefix exists to distinguish application code from shared `packages/`.
With no shared packages in scope for Phase 01 through Phase 03, the extra nesting
adds path length and tooling friction (pnpm workspace configuration, Rust workspace
configuration) with no architectural benefit.

## Migration cost is low when the time comes

If shared packages are introduced in Phase 04 or later, the migration from
`frontend/` → `apps/desktop/` and `backend/` → `apps/backend/` is a mechanical
rename with no business logic changes. The risk is low.

## Keeping the codebase consistent is more valuable than conforming to a spec

The current layout is committed to Git, referenced in documentation, recorded in
Tauri configuration paths, and understood by contributors. Migrating mid-phase
introduces churn and integration risk without delivering any new capability.

---

# Alternatives Considered

## Migrate immediately to apps/ layout

Advantages:
- Conforms to the architecture specification.
- Prepares for the packages/ layer.

Disadvantages:
- Pure churn: moves files that are actively being developed.
- Requires updating all paths in tauri.conf.json, Cargo.toml, pyproject.toml,
  CI configuration, and documentation simultaneously.
- No immediate engineering benefit.

This option was rejected.

## Adopt apps/ layout at the start of Phase 02

Advantages:
- Clean break between phases.

Disadvantages:
- Phase 02 begins the data layer (SQLite, Qdrant, Neo4j) — introducing a path
  migration at the same time increases integration risk for no functional gain.

This option was rejected.

---

# Consequences

## Positive

- No disruption to active Phase 01 development.
- All existing paths, build scripts, and documentation remain correct.
- Decision is formally recorded — no ambiguity for future contributors.

## Negative

- `docs/architecture/repository-layout.md` is temporarily inconsistent with
  the actual layout. This document must be updated as part of closing this ADR.

## Follow-up required

- `docs/architecture/repository-layout.md` updated to reflect `frontend/` and
  `backend/` at root.
- Migration to `apps/` layout reconsidered at the start of whichever phase first
  introduces a shared `packages/` library.

---

# Related Documents

- `docs/architecture/repository-layout.md`
- Phase 00 Completion Checklist — open item: "Directory layout decision recorded"
