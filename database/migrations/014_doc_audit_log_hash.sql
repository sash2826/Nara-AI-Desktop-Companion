-- Add file_hash to doc_audit_log so the incremental audit can skip documents
-- whose content has not changed since they were last scored, regardless of
-- whether indexed_at was bumped by a workspace re-index with identical content.
ALTER TABLE doc_audit_log ADD COLUMN file_hash TEXT;
