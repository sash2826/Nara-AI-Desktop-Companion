-- Migration 007: graph_state table
-- Tracks the last successful knowledge graph build per document.
-- Allows FileIndexer to skip the graph build when a document's content
-- has not changed since the last index run, matching the hash-based
-- deduplication already applied to chunks.

CREATE TABLE IF NOT EXISTS graph_state (
    document_id TEXT NOT NULL PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    file_hash   TEXT NOT NULL,
    built_at    TEXT NOT NULL
);
