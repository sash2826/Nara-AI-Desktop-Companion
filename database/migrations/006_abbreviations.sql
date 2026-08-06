-- Migration 006: Abbreviation discovery storage.
--
-- Persists abbreviation–definition pairs extracted from indexed documents.
-- Rows are automatically removed when the parent document is deleted or re-indexed
-- (via ON DELETE CASCADE from the documents table).
--
-- The composite PK (abbreviation, document_id) models the many-to-many
-- relationship: one abbreviation may appear in many documents; one document
-- may define many abbreviations. Using the PK as the upsert target
-- (INSERT OR REPLACE) means re-indexing a document cleanly replaces its rows.

CREATE TABLE IF NOT EXISTS abbreviations (
    abbreviation  TEXT NOT NULL,
    definition    TEXT NOT NULL,
    document_id   TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    discovered_at TEXT NOT NULL,
    PRIMARY KEY (abbreviation, document_id)
);

CREATE INDEX IF NOT EXISTS idx_abbreviations_document_id
    ON abbreviations(document_id);

-- Fast lookup by abbreviation token for query-time expansion.
CREATE INDEX IF NOT EXISTS idx_abbreviations_abbreviation
    ON abbreviations(abbreviation);
