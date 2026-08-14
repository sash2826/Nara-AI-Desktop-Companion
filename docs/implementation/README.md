# Implementation Documentation

**Version:** 2.0.0
**Status:** Active
**Last Updated:** 2026-08-14

---

# Overview

This directory contains the implementation documentation for the Enterprise AI Companion.

The implementation guides describe how the architecture defined in the Architecture Documentation should be realized.

These documents are intended for developers implementing the system and should be followed sequentially unless otherwise specified.

Implementation guides define the order of development, expected outcomes, dependencies between phases, and implementation objectives.

---

# Purpose

The implementation documentation exists to:

* Provide a structured development roadmap.
* Define implementation phases.
* Reduce architectural drift during development.
* Maintain consistency across contributors.
* Enable incremental delivery of functionality.
* Ensure implementation remains aligned with the documented architecture.

Implementation guides describe engineering execution rather than architectural design.

---

# Relationship to Other Documentation

The implementation documentation builds upon the architectural documentation.

```text
Architecture
       │
       ▼
Architecture Decision Records
       │
       ▼
Implementation Guides
       │
       ▼
Source Code
```

Implementation guides should never contradict the architecture or accepted Architecture Decision Records (ADRs).

---

# Implementation Phases

Development is organized into the following phases.

| Phase       | Name                              | Status    | Objective                                                              |
| ----------- | --------------------------------- | --------- | ---------------------------------------------------------------------- |
| Phase 00    | Assistant Experience              | Complete  | Desktop application, Character Widget, conversation architecture       |
| Phase 01    | AI Integration                    | Complete  | APIM provider, RAG pipeline, embeddings, streaming responses           |
| Phase 02    | Knowledge & Search                | Complete  | Data layer (SQLite, Neo4j, Qdrant) and hybrid search engine            |
| Phase 03    | Workspace Features                | Complete  | Workspace management, document browser, search UI                      |
| Phase 04    | AI Context & Intelligence         | Complete  | Context assembly, conversation memory, reranking, source citation      |
| Phase 05    | Knowledge Graph                   | Complete  | Graph-augmented retrieval, entity/relationship extraction               |
| Phase 06    | Enterprise Features               | Complete  | Plugin system, security, authentication, audit logging                 |
| Pre-08      | Graph Correctness Fixes           | Complete  | SQLite graph CTE depth cap and case-insensitive name lookup            |
| Phase 08    | Orb Native Shell                  | Complete  | Always-on-top orb window, Liquid Glass UI, 5 animation states          |
| Phase 09    | File Organisation — New Files     | Complete  | Downloads auto-watch, graph+rerank placement scorer (87%), move        |
| Phase 09b   | Adaptive Placement Learning       | Planned   | Feedback capture, entity affinity weights, threshold recalibration     |
| Phase 10    | File Organisation — Existing Files| Planned   | On-demand audit + passive background reorganisation suggestions        |
| Phase 07    | Automation Engine                 | Deferred  | Workflow engine, task scheduling, event-driven processing (under review)|
| Phase 11    | Polish & Release                  | Planned   | Testing, quality assurance, packaging, and production release          |

Each phase should be completed before progressing to the next unless dependencies explicitly allow parallel development.

---

# Implementation Principles

Development should follow these principles:

* Preserve architectural boundaries.
* Follow accepted ADRs.
* Deliver incremental functionality.
* Prefer reusable components.
* Minimize technical debt.
* Maintain comprehensive testing.
* Keep documentation synchronized with implementation.

Implementation should never compromise the architectural principles established by the project.

---

# Document Structure

Each implementation phase includes:

* Purpose
* Objectives
* Prerequisites
* Deliverables
* Implementation Tasks
* Completion Criteria
* Dependencies
* Related Documentation

Maintaining a consistent structure simplifies project planning and progress tracking.

---

# Scope

Implementation guides define:

* Development order.
* Engineering tasks.
* Milestones.
* Expected deliverables.
* Dependencies between implementation phases.

They do not redefine the architecture or replace Architecture Decision Records.

---

# Related Documentation

Implementation guides depend on:

* `docs/architecture/`
* `docs/decisions/`
* `.claude/CLAUDE.md`

Developers should become familiar with these documents before beginning implementation.
