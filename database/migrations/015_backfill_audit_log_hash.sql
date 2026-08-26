-- Backfill file_hash in doc_audit_log for rows added before migration 014.
-- Those rows have file_hash = NULL (ALTER TABLE default). Copying the hash
-- from the documents table means the next audit run treats them as already
-- scored and skips them, rather than re-scoring every previously-audited doc.
UPDATE doc_audit_log
SET file_hash = (
    SELECT file_hash
    FROM documents
    WHERE documents.id = doc_audit_log.doc_id
)
WHERE file_hash IS NULL;
