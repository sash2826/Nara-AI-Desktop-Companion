-- Incremental organisation audit: tracks when each document was last scored.
-- audited_at is compared against documents.indexed_at on subsequent runs so
-- only new or re-indexed documents are re-scored, not the entire corpus.
CREATE TABLE IF NOT EXISTS doc_audit_log (
    doc_id     TEXT PRIMARY KEY,
    audited_at TEXT NOT NULL
);
