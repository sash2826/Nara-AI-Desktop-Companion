-- Migration 010: Plugin registry table.
--
-- Stores metadata about discovered plugins and their enabled/disabled state.
-- The registry is updated on every application startup as the plugin scan
-- directory is walked. Rows are upserted, so re-installing or upgrading a
-- plugin is idempotent.

CREATE TABLE IF NOT EXISTS plugins (
    id            TEXT    PRIMARY KEY,           -- manifest.name (slug)
    display_name  TEXT    NOT NULL,
    version       TEXT    NOT NULL,
    description   TEXT,
    author        TEXT,
    permissions   TEXT    NOT NULL DEFAULT '[]', -- JSON array of permission strings
    enabled       INTEGER NOT NULL DEFAULT 1,    -- 1 = active, 0 = disabled
    manifest_json TEXT    NOT NULL,              -- full manifest for auditing
    installed_at  TEXT    NOT NULL               -- ISO-8601 UTC timestamp
);

CREATE INDEX IF NOT EXISTS idx_plugins_enabled ON plugins (enabled);
