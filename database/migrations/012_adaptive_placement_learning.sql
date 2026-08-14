-- Migration 012: Adaptive Placement Learning (Phase 09b).
--
-- Adds three capabilities:
--   1. entity_snapshot / corrected_folder columns on the recommendations table
--      so we can replay which entities were present at recommendation time and
--      record user corrections.
--   2. entity_folder_affinity — per-(entity, folder) EMA weights updated from
--      user accept / dismiss / correction signals.
--   3. scorer_config — key-value store for threshold diagnostic output.

ALTER TABLE file_placement_recommendations ADD COLUMN entity_snapshot TEXT;
ALTER TABLE file_placement_recommendations ADD COLUMN corrected_folder TEXT;

CREATE TABLE IF NOT EXISTS entity_folder_affinity (
    entity_name  TEXT    NOT NULL,
    folder_path  TEXT    NOT NULL,
    weight       REAL    NOT NULL DEFAULT 1.0,
    observations INTEGER NOT NULL DEFAULT 0,
    updated_at   TEXT    NOT NULL,
    PRIMARY KEY (entity_name, folder_path)
);

CREATE INDEX IF NOT EXISTS idx_efa_folder ON entity_folder_affinity (folder_path);

CREATE TABLE IF NOT EXISTS scorer_config (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
