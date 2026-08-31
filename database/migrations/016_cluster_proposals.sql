-- Migration 016: Cluster proposals table for Phase 10 (Intelligent Folder Discovery).
--
-- Persists folder-creation proposals generated when ClusterDiscoveryService
-- detects a group of semantically-related floating files. A proposal stays
-- 'pending' until the user accepts (files are moved and a new folder is created)
-- or dismisses it via the Organise dashboard.

CREATE TABLE IF NOT EXISTS cluster_proposals (
    id                   TEXT PRIMARY KEY,
    status               TEXT NOT NULL DEFAULT 'pending',  -- 'pending' | 'accepted' | 'dismissed'
    proposed_folder_name TEXT NOT NULL,  -- deterministic name from FolderNamingService
    document_ids         TEXT NOT NULL,  -- JSON array of document IDs in the cluster
    file_paths           TEXT NOT NULL,  -- JSON array of absolute file paths (for display)
    accepted_folder      TEXT,           -- full path of the folder actually created on accept
    created_at           TEXT NOT NULL,
    resolved_at          TEXT
);

CREATE INDEX IF NOT EXISTS idx_cp_status ON cluster_proposals (status);
