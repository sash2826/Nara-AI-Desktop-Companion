CREATE TABLE IF NOT EXISTS indexing_errors (
    id             TEXT PRIMARY KEY,
    workspace_path TEXT NOT NULL,
    file_path      TEXT NOT NULL,
    error_message  TEXT NOT NULL,
    failed_at      TEXT NOT NULL
);
