-- Migration 002: Document indexing and chunk storage schema.
-- All timestamps are stored as ISO-8601 UTC strings.

CREATE TABLE IF NOT EXISTS documents (
    id             TEXT PRIMARY KEY,
    workspace_path TEXT NOT NULL,
    file_path      TEXT NOT NULL UNIQUE,
    file_hash      TEXT NOT NULL,
    char_count     INTEGER NOT NULL DEFAULT 0,
    chunk_count    INTEGER NOT NULL DEFAULT 0,
    indexed_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    char_start  INTEGER NOT NULL,
    char_end    INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

-- FTS5 virtual table for keyword search over chunk content.
-- chunk_id is stored unindexed as a foreign key back to the chunks table.
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
    USING fts5(content, chunk_id UNINDEXED, tokenize='porter ascii');
