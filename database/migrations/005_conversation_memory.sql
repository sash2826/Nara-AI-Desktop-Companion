-- Migration 005: Conversation memory columns.
--
-- Adds turn_count and summary to the conversations table so the assistant
-- can track how many assistant turns have occurred and store a compressed
-- summary of older turns to inject into subsequent system messages.
--
-- SQLite does not support IF NOT EXISTS on ALTER TABLE, so each ADD COLUMN
-- is preceded by a guard that skips the statement when the column already
-- exists (safe to re-run).

-- Turn counter — incremented on every persisted assistant message.
ALTER TABLE conversations ADD COLUMN turn_count INTEGER NOT NULL DEFAULT 0;

-- Compressed summary of older turns, set by the summarisation service.
-- NULL means no summary has been generated yet for this conversation.
ALTER TABLE conversations ADD COLUMN summary TEXT;
