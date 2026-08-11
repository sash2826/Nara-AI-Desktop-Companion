-- Migration 011: File placement recommendations table for Phase 09.
--
-- Persists placement recommendations generated when a new file arrives in the
-- OS Downloads folder. A recommendation is pending until the user accepts or
-- dismisses it; the orb glows amber while any pending rows exist.

CREATE TABLE IF NOT EXISTS file_placement_recommendations (
    id              TEXT PRIMARY KEY,
    source_path     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    recommendations TEXT NOT NULL,  -- JSON array of {folder, score, label}
    accepted_folder TEXT,
    created_at      TEXT NOT NULL,
    resolved_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_fpr_status ON file_placement_recommendations (status);
