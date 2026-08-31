-- Migration 017: Create cluster_proposals table.
--
-- Migration 016 was applied under an earlier filename (016_cluster_recommendations.sql)
-- which created the now-unused cluster_recommendations table. This migration creates
-- the cluster_proposals table that the backend actually uses.

CREATE TABLE IF NOT EXISTS cluster_proposals (
    id                   TEXT PRIMARY KEY,
    status               TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'accepted' | 'dismissed'
    proposed_folder_name TEXT NOT NULL,
    document_ids         TEXT NOT NULL,  -- JSON array of document IDs
    file_paths           TEXT NOT NULL,  -- JSON array of absolute file paths
    accepted_folder      TEXT,           -- full path of the folder created on accept
    created_at           TEXT NOT NULL,
    resolved_at          TEXT
);

CREATE INDEX IF NOT EXISTS idx_cp_status ON cluster_proposals (status);
