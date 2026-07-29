# Repository Layout

**Version:** 1.1.0
**Status:** Active
**Last Updated:** 2026-07-29

---

# 1. Purpose

This document defines the physical organization of the Enterprise AI Companion repository.

The repository structure is designed to promote maintainability, scalability, modularity, and clear separation of responsibilities.

Each directory has a single primary purpose, allowing the project to grow without introducing unnecessary complexity or tightly coupled components.

This document establishes the repository organization that all contributors and implementation guides must follow.

---

# 2. Design Objectives

The repository layout is designed to achieve the following goals:

* Clear separation of responsibilities.
* Scalable project organization.
* Reusable shared components.
* Independent application development.
* Consistent engineering practices.
* Simplified onboarding for new contributors.
* Minimal coupling between modules.
* Long-term maintainability.

The repository organization should remain stable throughout the lifetime of the project.

---

# 3. Repository Structure

```text
Enterprise-AI-Companion/
│
├── .claude/
│   ├── CLAUDE.md
│   └── commands/
│
├── frontend/                  ← Tauri + React desktop application
│   ├── src/                   ← React + TypeScript source
│   ├── src-tauri/             ← Rust Tauri shell
│   └── package.json
│
├── backend/                   ← Python FastAPI backend service
│   ├── src/
│   │   └── enterprise_ai_companion/
│   ├── tests/
│   └── pyproject.toml
│
├── database/
│   ├── migrations/
│   ├── schemas/
│   └── seeds/
│
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── implementation/
│   └── research/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│
├── assets/
│
├── README.md
├── CHANGELOG.md
└── .gitignore
```

> **Note:** The original specification used `apps/desktop/` and `apps/backend/`
> with a `packages/` monorepo layer. The flat `frontend/` / `backend/` layout
> was adopted during Phase 00 implementation and formally accepted in
> ADR-013. The `packages/` layer will be introduced when a shared library is
> extracted that is consumed by both applications.

The repository is organized into applications, reusable packages, documentation, testing, database resources, automation scripts, and project assets.

Each top-level directory has a clearly defined responsibility.

---

# 4. Directory Responsibilities

## .claude/

Contains permanent engineering guidance for AI-assisted development.

This directory includes:

* Repository engineering standards.
* Claude Code configuration.
* Reusable development commands.
* AI workflow documentation.

This directory does not contain application source code.

---

## apps/

Contains executable applications.

Applications are independently deployable and represent the primary entry points of the system.

Current applications include:

### desktop/

Contains the desktop application, user interface, and desktop-specific functionality.

### backend/

Contains backend services, business logic, orchestration, AI integration, indexing workflows, and application services.

Applications may depend on reusable packages.

Applications must not directly depend on one another unless explicitly documented by an Architecture Decision Record (ADR).

---

## packages/

Contains reusable libraries shared across applications.

Examples include:

* Shared models.
* Data Transfer Objects (DTOs).
* Common utilities.
* Validation logic.
* Shared configuration.
* Common type definitions.

Packages should remain application-independent.

Packages must not contain application-specific business logic.

---

## database/

Contains database-related resources.

Examples include:

* Schema definitions.
* Database migrations.
* Seed data.
* Initialization scripts.

Business logic should never be implemented inside this directory.

---

## docs/

Contains all engineering documentation.

Documentation is organized into the following categories:

### architecture/

High-level architectural documentation describing the overall system design.

### decisions/

Architecture Decision Records (ADRs) documenting significant engineering decisions and their rationale.

### implementation/

Implementation guides, development phases, and engineering procedures.

### research/

Research notes, evaluations, technology investigations, and supporting documentation.

Documentation should evolve alongside the software and remain synchronized with the implementation.

---

## tests/

Contains automated testing resources.

Testing is organized into:

### unit/

Tests for individual functions, classes, and isolated components.

### integration/

Tests covering interactions between multiple components.

### e2e/

End-to-end tests validating complete user workflows.

Production source code must never be placed inside the tests directory.

---

## scripts/

Contains developer automation and maintenance utilities.

Examples include:

* Build scripts.
* Development helpers.
* Setup scripts.
* Maintenance tools.
* Automation utilities.

Scripts should improve developer productivity while remaining independent of business logic.

---

## assets/

Contains static project resources.

Examples include:

* Images.
* Icons.
* Application branding.
* Static media.
* Design resources.

Application logic should not reside within this directory.

---

# 5. Dependency Rules

Repository dependencies must follow a clear and predictable hierarchy.

```text
Applications
        │
        ▼
Reusable Packages
        │
        ▼
Shared Libraries
```

The following rules apply:

* Applications may depend on reusable packages.
* Packages must never depend on applications.
* Packages should minimize dependencies on other packages.
* Circular dependencies are prohibited.
* Shared functionality should be implemented once and reused.
* Business logic should not be duplicated across applications.

Dependency direction must remain consistent throughout the repository.

---

# 6. Repository Growth Strategy

The repository is expected to grow over time.

Future additions should follow these principles:

New applications should be created under the `apps/` directory.

New reusable libraries should be added under `packages/`.

New architectural documentation should be placed under `docs/architecture/`.

New Architecture Decision Records should be added to `docs/decisions/`.

Implementation guides should be added under `docs/implementation/`.

Repository restructuring should occur only when supported by an accepted Architecture Decision Record.

Large-scale structural changes should preserve existing architectural boundaries whenever practical.

---

# 7. Repository Standards

The repository should remain organized and maintainable throughout its lifetime.

Contributors should:

* Keep related functionality together.
* Avoid duplicate implementations.
* Reuse existing abstractions where appropriate.
* Follow established naming conventions.
* Maintain consistent directory organization.
* Remove obsolete code and documentation.
* Preserve clear ownership of modules.

Every addition to the repository should improve or preserve overall maintainability.

---

# 8. Relationship to Other Documents

This document defines the physical organization of the repository.

Additional architectural details are documented separately.

* **System Overview** defines the overall architecture of the Enterprise AI Companion.
* **Application Layers** defines the logical layering of the system.
* **Capability Model** defines the functional organization of the application.
* **Technology Stack** defines the responsibilities of each technology.
* **Architecture Decision Records (ADRs)** document significant engineering decisions.
* **Implementation Guides** describe how architectural decisions should be implemented.

All future repository changes should remain consistent with the principles established in this document.
