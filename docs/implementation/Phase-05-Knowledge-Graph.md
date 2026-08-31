# Phase 05: Knowledge Graph

**Phase:** 05

**Status:** Complete (implemented 2026-08-05)

**Estimated Duration:** 3-5 Days (actual: ~5 days across two parallel sessions)

---

# Purpose

This phase implements the knowledge graph capabilities of the Document-Management-RAG-Graph-Agent.

The objective is to transform isolated documents into an interconnected network of entities, relationships, concepts, and contextual knowledge that enhances retrieval, reasoning, and AI-assisted workflows.

At the completion of this phase, the application should automatically discover relationships within user data and expose graph-based reasoning capabilities to higher-level services.

---

# Objectives

Upon completion of this phase, the application should provide:

* Entity extraction.
* Relationship extraction.
* Graph construction.
* Knowledge enrichment.
* Graph traversal.
* Context discovery.
* Semantic linking.
* Graph querying.
* Graph visualization support.
* Incremental graph updates.

Business capabilities should interact with knowledge through the centralized graph service rather than directly accessing the graph database.

---

# Prerequisites

Before beginning this phase:

* Phase 00 through Phase 04 must be completed.
* AI services should be operational.
* Search engine should be available.
* `ContextAssembler` from Phase 04 should be stable.
* Background task processing should be functioning.

> **Note:** Neo4j is no longer required as a prerequisite. The knowledge graph now runs on SQLite by default — no additional infrastructure setup is needed.

---

# Knowledge Graph Architecture

The knowledge graph subsystem should follow a modular architecture.

```text
knowledge/
│
├── extraction/
├── entities/
├── relationships/
├── graph/
├── enrichment/
├── traversal/
├── queries/
├── visualization/
├── models/
└── services/
```

Each module should maintain a clearly defined responsibility.

---

# Entity Extraction

Responsible for identifying meaningful entities within indexed content.

Examples include:

* People.
* Organizations.
* Projects.
* Documents.
* Technologies.
* Locations.
* Products.
* Events.
* Custom entity types.

Extraction should remain configurable to support future domain-specific models.

---

# Relationship Extraction

Responsible for discovering relationships between entities.

Examples include:

* References.
* Ownership.
* Membership.
* Dependencies.
* Citations.
* Similarity.
* Chronological relationships.
* Semantic associations.

Relationship generation should operate independently of graph storage.

---

# Graph Construction

The graph builder should:

* Create nodes.
* Create relationships.
* Merge duplicates.
* Validate graph integrity.
* Maintain consistency.
* Update existing structures.

Graph construction should execute through the background task manager.

---

# Knowledge Enrichment

Provide support for:

* Entity normalization.
* Alias resolution.
* Duplicate detection.
* Metadata enrichment.
* Confidence scoring.
* Relationship refinement.

Enrichment should improve graph quality over time without requiring manual intervention.

---

# Graph Traversal

Support traversal operations including:

* Neighbor discovery.
* Multi-hop traversal.
* Path finding.
* Connected component analysis.
* Relationship expansion.
* Context exploration.

Traversal logic should remain independent of user interface concerns.

---

# Graph Query Service

Provide a unified interface for:

* Entity lookup.
* Relationship queries.
* Context expansion.
* Neighborhood retrieval.
* Graph analytics.
* AI-assisted graph exploration.

Consumers should not require knowledge of graph query syntax (Cypher or SQL).

---

# AI Integration

The knowledge graph should enhance AI workflows by providing:

* Context expansion.
* Entity relationships.
* Related concepts.
* Supporting documents.
* Semantic neighborhoods.
* Evidence chains.

AI services should consume graph information through standardized interfaces.

---

# Incremental Updates

Support:

* New document ingestion.
* Entity updates.
* Relationship updates.
* Graph cleanup.
* Consistency validation.

Graph rebuilding should not be required after every document modification.

---

# Visualization Support

Provide graph structures suitable for visualization including:

* Nodes.
* Edges.
* Clusters.
* Categories.
* Layout metadata.

Rendering remains the responsibility of the frontend.

---

# Implementation Summary

Phase 05 was implemented across two parallel sessions (Session A: core graph pipeline; Session B: graph UI and visualization).

## Graph Backend: SQLiteGraphProvider (default)

The knowledge graph runs on SQLite by default, requiring **zero additional infrastructure**. The backend uses recursive CTEs (`WITH RECURSIVE`) for multi-hop traversal, BFS-based path-finding, and connected document discovery — all capabilities previously associated only with Neo4j.

Key implementation decisions:

* **`SQLiteGraphProvider`** (`capabilities/graph/sqlite_graph_provider.py`) — full `GraphProvider` implementation with upsert-on-conflict, FK cascade deletes, depth-limited recursive traversal, substring entity search, and focal-entity visualization subgraphs.
* **`EAC_GRAPH_PROVIDER` environment variable** controls provider selection at startup: `sqlite` (default), `neo4j` (opt-in), or `null` (graph features disabled).
* **Migration `008_sqlite_graph.sql`** adds `graph_entities` and `graph_relationships` tables to the existing SQLite database — the same database already used for documents, chunks, and application state.
* **`GraphProvider` abstract interface** extended with `search_entities()` and `get_connected_documents()` as required methods on all providers, eliminating `AttributeError` fallbacks.
* **`EnrichmentService`** and **`TraversalEngine`** detect provider capability via `hasattr` rather than `isinstance`, keeping them decoupled from concrete provider classes.
* **Graph-augmented retrieval** (`ContextAssembler._expand_via_graph()`) supplements vector search by looking up graph-connected documents for query tokens, appending extra chunks to the context payload without exceeding budget limits.
* **Incremental updates** (`GraphStateRepository` + file hash comparison) prevent re-running LLM extraction on unchanged files.

## Graph UI

A force-directed SVG graph visualization was implemented without external graph libraries. The `KnowledgeGraphPage` renders an interactive canvas with drag support, entity type colour coding, confidence arc overlays, and a click-to-open `EntityCard` side panel.

---

# Neo4j: Future Scope

Neo4j remains fully supported as an optional backend and is the recommended choice for large-scale or enterprise deployments that require:

* **Very large graphs** — tens of millions of nodes and relationships where SQLite write performance or query planning becomes a bottleneck.
* **Advanced graph analytics** — algorithms such as PageRank, betweenness centrality, Louvain community detection, and native graph ML (via Neo4j GDS).
* **Multi-instance deployments** — scenarios where multiple backend instances must share a single graph store (Neo4j supports clustering; SQLite is single-file per host).
* **Cypher tooling** — teams already familiar with Neo4j Browser, Bloom, or other Cypher-based inspection tools.

To enable Neo4j, set the environment variable:

```
EAC_GRAPH_PROVIDER=neo4j
```

The backend will connect to a Neo4j instance using the credentials in `EAC_NEO4J_URI`, `EAC_NEO4J_USER`, and `EAC_NEO4J_PASSWORD`. All business logic is identical — only the storage layer changes.

An Architecture Decision Record should be filed before migrating a production instance from SQLite to Neo4j.

---

# Deliverables

Completion of this phase should produce:

* Entity extraction engine.
* Relationship extraction engine.
* Graph builder.
* Knowledge enrichment service.
* Graph query service.
* Traversal engine.
* Incremental update framework.
* Visualization data provider.

---

# Completion Criteria

This phase is complete when:

* Entities are extracted reliably.
* Relationships are created accurately.
* Graph updates execute incrementally.
* Graph traversal returns valid results.
* AI services can retrieve graph context.
* Graph queries execute efficiently.
* Background graph processing functions correctly.
* Logging captures graph operations consistently.

---

# Dependencies

Requires:

* Phase 00
* Phase 01
* Phase 02
* Phase 03
* Phase 04

Provides the knowledge foundation for:

* Phase 06
* Phase 07
* Phase 08

---

# Related Documentation

* `docs/architecture/capability-model.md`
* `docs/architecture/technology-stack.md`
* `docs/decisions/ADR-002-Data-Storage-Strategy.md`
* `docs/decisions/ADR-003-AI-Provider-Abstraction.md`
* `docs/decisions/ADR-008-Search-Architecture.md`
* `docs/decisions/ADR-011-Background-Task-Processing.md`

---

# Next Phase

After completing this phase, proceed to:

**Phase 06: Enterprise Features**

The next phase introduces authentication, authorisation, credential storage, encryption, audit logging, and data privacy controls. This hardens the platform for enterprise deployment before productivity automation is added in Phase 07.
