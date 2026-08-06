-- Migration 008: SQLite-backed knowledge graph storage.
--
-- Replaces the Neo4j dependency with two relational tables that cover every
-- operation previously performed via Cypher.  Multi-hop traversal is handled
-- with recursive CTEs at query time.
--
-- graph_entities: one row per entity node.
--   id                  — stable UUID (uuid5 of document_id + name)
--   name                — original extracted name
--   entity_type         — EntityType enum value (Person, Organization, …)
--   source_document_id  — FK → documents(id); CASCADE-deleted with the doc
--   confidence          — [0.0, 1.0] from LLM extraction
--   canonical           — lowercase normalised name for deduplication
--
-- graph_relationships: one row per directed edge.
--   source_id / target_id  — FK → graph_entities(id)
--   relationship_type       — RelationshipType enum value
--   confidence              — [0.0, 1.0]

CREATE TABLE IF NOT EXISTS graph_entities (
    id                  TEXT NOT NULL PRIMARY KEY,
    name                TEXT NOT NULL,
    entity_type         TEXT NOT NULL,
    source_document_id  TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    confidence          REAL NOT NULL DEFAULT 1.0,
    canonical           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_graph_entities_document
    ON graph_entities(source_document_id);

CREATE INDEX IF NOT EXISTS idx_graph_entities_canonical
    ON graph_entities(canonical, entity_type);

CREATE INDEX IF NOT EXISTS idx_graph_entities_name
    ON graph_entities(name);

CREATE TABLE IF NOT EXISTS graph_relationships (
    id                  TEXT NOT NULL PRIMARY KEY,
    source_id           TEXT NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    target_id           TEXT NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    relationship_type   TEXT NOT NULL,
    confidence          REAL NOT NULL DEFAULT 1.0,
    UNIQUE (source_id, target_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_graph_relationships_source
    ON graph_relationships(source_id);

CREATE INDEX IF NOT EXISTS idx_graph_relationships_target
    ON graph_relationships(target_id);
