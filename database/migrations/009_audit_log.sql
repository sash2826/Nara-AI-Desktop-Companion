-- Migration 009: Audit log for security-relevant application events.
--
-- audit_events records operations that an enterprise administrator or the user
-- themselves may want to review: indexing jobs, backup creation, and credential
-- changes.  The table is append-only by convention — rows are never updated or
-- deleted by application code.
--
-- event_type  — dot-namespaced verb, e.g. "indexing.started", "backup.created"
-- actor       — always "system" in the current single-user model; reserved for
--               future multi-user or SSO scenarios
-- details     — JSON object with context; credential values are explicitly
--               excluded before insertion by AuditLogger.log()
-- created_at  — ISO-8601 UTC timestamp

CREATE TABLE IF NOT EXISTS audit_events (
    id          TEXT PRIMARY KEY,
    event_type  TEXT NOT NULL,
    actor       TEXT NOT NULL DEFAULT 'system',
    details     TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_created_at
    ON audit_events (created_at);

CREATE INDEX IF NOT EXISTS idx_audit_events_type
    ON audit_events (event_type);
