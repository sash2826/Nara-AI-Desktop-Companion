# Technology Stack

**Version:** 1.0.0
**Status:** Active
**Last Updated:** 2026-07-23

---

# 1. Purpose

This document defines the technologies used by the Document-Management-RAG-Graph-Agent and the architectural responsibilities assigned to each.

The technology stack exists to support the system architecture defined in the System Overview. Technologies are implementation choices, not architectural boundaries.

Each technology is selected because it fulfills a specific responsibility within the system. If a technology is replaced in the future, its architectural responsibility should remain unchanged.

---

# 2. Technology Selection Principles

Technology choices should follow these principles:

* Select technologies based on architectural requirements rather than popularity.
* Prefer mature, actively maintained solutions.
* Favor modular and replaceable components.
* Minimize unnecessary dependencies.
* Keep business logic independent of implementation technologies.
* Avoid vendor lock-in whenever practical.
* Prioritize long-term maintainability over short-term convenience.

Technology decisions should support the architecture rather than define it.

---

# 3. Technology Overview

| Category           | Technology        | Primary Responsibility                       |
| ------------------ | ----------------- | -------------------------------------------- |
| Desktop Framework  | Tauri             | Native desktop application shell             |
| Frontend Framework | React             | User interface                               |
| Frontend Language  | TypeScript        | Frontend application logic                   |
| Backend Language   | Python            | Business logic and AI orchestration          |
| Local Database     | SQLite            | Structured application data                  |
| Graph Database     | SQLite (embedded) | Knowledge graph and relationships (default)  |
| Vector Database    | Qdrant            | Semantic search and embeddings               |
| OCR Engine         | PaddleOCR         | Text extraction from images and documents    |
| AI Provider        | OpenAI GPT Models | Natural language understanding and reasoning |

Each technology serves a distinct responsibility within the overall architecture.

---

# 4. Desktop Framework

## Technology

Tauri

## Responsibility

Provides the native desktop application shell.

Primary responsibilities include:

* Native application packaging.
* Window management.
* Secure communication between frontend and backend.
* Operating system integration.
* Application lifecycle management.

Business logic should not be implemented within the desktop framework.

---

# 5. Frontend Framework

## Technology

React

## Responsibility

Provides the presentation layer.

Primary responsibilities include:

* Rendering user interfaces.
* Managing user interaction.
* Displaying application state.
* Component composition.
* Client-side navigation.

React should remain focused on presentation rather than business logic.

---

# 6. Frontend Language

## Technology

TypeScript

## Responsibility

Provides type-safe frontend development.

Primary responsibilities include:

* UI logic.
* State management.
* Client-side validation.
* Interface definitions.
* API communication.

Type safety should improve maintainability and reduce runtime errors.

---

# 7. Backend Language

## Technology

Python

## Responsibility

Provides application services and business logic.

Primary responsibilities include:

* Workflow orchestration.
* AI integration.
* File processing.
* Search coordination.
* Data processing.
* Background tasks.

Business rules should remain centralized within the backend.

---

# 8. Structured Database

## Technology

SQLite

## Responsibility

Stores structured application data.

Examples include:

* User preferences.
* Metadata.
* Configuration.
* Index information.
* Application state.

SQLite stores structured data and, by default, the knowledge graph (via the `SQLiteGraphProvider`). It should not be responsible for semantic (vector) search — that remains Qdrant's responsibility.

---

# 9. Knowledge Graph

## Technology

SQLite (default) · Neo4j (optional, future scale-out)

## Responsibility

Stores relationships between entities extracted from indexed documents.

Examples include:

* Document relationships.
* Entity connections.
* Concept graphs.
* Context generation.
* Knowledge navigation.

Graph storage should remain focused on relationship data.

## Default: SQLite

The knowledge graph runs on SQLite by default using recursive CTEs for multi-hop traversal. No additional infrastructure is required. The `EAC_GRAPH_PROVIDER` environment variable controls provider selection at startup (`sqlite`, `neo4j`, or `null`).

## Future Scope: Neo4j

Neo4j is supported as an optional opt-in backend for large-scale deployments, advanced graph analytics (PageRank, community detection, graph ML), and multi-instance scenarios. Business logic is identical across both providers — only the storage implementation changes. See `docs/implementation/Phase-05-Knowledge-Graph.md` for migration guidance.

---

# 10. Vector Database

## Technology

Qdrant

## Responsibility

Provides semantic similarity search.

Primary responsibilities include:

* Vector storage.
* Embedding indexing.
* Similarity search.
* Semantic retrieval.
* Nearest-neighbor queries.

Qdrant should remain dedicated to vector operations.

---

# 11. OCR Engine

## Technology

PaddleOCR

## Responsibility

Extracts text from image-based content.

Examples include:

* Images.
* Scanned documents.
* Screenshots.
* PDFs without selectable text.

OCR should produce structured text for downstream processing.

---

# 12. AI Provider

## Technology

OpenAI GPT Models

## Responsibility

Provides AI-powered reasoning and language understanding.

Primary responsibilities include:

* Question answering.
* Summarization.
* Classification.
* Natural language understanding.
* Text generation.
* Embedding generation.

AI providers should always be accessed through an abstraction layer rather than directly.

---

# 13. Technology Interaction

The technologies collaborate according to the following architecture.

```text id="m7jpd8"
             User
               │
               ▼
        React (TypeScript)
               │
               ▼
             Tauri
               │
               ▼
             Python
               │
      ┌────────┼────────────┐
      ▼        ▼            ▼
   SQLite  SQLite/Neo4j  Qdrant
  (data)   (graph)      (vectors)
      │                     │
      └────────┬────────────┘
               ▼
         AI Services
               │
               ▼
       OpenAI GPT Models
```

Each technology fulfills a specific role within the overall architecture.

Responsibilities should not overlap unnecessarily.

---

# 14. Technology Independence

Business logic should remain independent of specific technologies.

Examples include:

* AI providers may be replaced without changing business logic.
* Database engines may evolve while preserving storage interfaces.
* OCR engines may be substituted if requirements change.
* Frontend libraries may evolve while preserving application behavior.

Implementation details should remain isolated behind clearly defined interfaces.

---

# 15. Technology Replacement Guidelines

Technology replacement should follow these principles:

* Preserve architectural responsibilities.
* Maintain interface compatibility whenever practical.
* Minimize impact on unrelated components.
* Document significant technology changes through an Architecture Decision Record (ADR).
* Avoid introducing unnecessary coupling during migration.

Replacing a technology should require minimal changes outside its assigned responsibility.

---

# 16. Future Technology Evolution

The technology stack is expected to evolve over time.

Potential future additions include:

* Additional AI providers.
* Alternative vector databases.
* Cloud storage services.
* Enterprise authentication providers.
* Plugin frameworks.
* Mobile technologies.
* Distributed processing services.

Future technologies should integrate into the existing architecture without altering established architectural boundaries.

---

# 17. Relationship to Other Documents

This document defines the implementation technologies supporting the Document-Management-RAG-Graph-Agent.

Related documentation includes:

* **System Overview** for the overall architecture.
* **Repository Layout** for repository organization.
* **Application Layers** for logical architecture.
* **Capability Model** for functional organization.
* **Architecture Decision Records (ADRs)** for technology selection rationale.

Technology choices should remain consistent with the architectural principles established throughout the documentation.
