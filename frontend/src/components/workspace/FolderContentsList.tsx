import { FileTypeIcon } from "@/components/common/FileTypeIcon";
import type { IndexedDocument } from "@/types/workspace";

function fileName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
}

interface FolderContentsListProps {
  documents: IndexedDocument[];
}

/** Read-only preview of a folder's already-indexed files, for context during organisation review. */
export function FolderContentsList({ documents }: FolderContentsListProps) {
  if (documents.length === 0) {
    return <p className="text-xs text-muted-foreground">No indexed files in this folder yet.</p>;
  }

  return (
    <div className="space-y-1">
      {documents.map((doc) => (
        <div key={doc.id} className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs">
          <FileTypeIcon path={doc.file_path} size={17} className="flex-shrink-0" />
          <span className="min-w-0 flex-1 truncate text-foreground" title={doc.file_path}>
            {fileName(doc.file_path)}
          </span>
          <span className="flex-shrink-0 text-2xs text-muted-foreground">
            {doc.chunk_count} chunk{doc.chunk_count !== 1 ? "s" : ""}
          </span>
        </div>
      ))}
    </div>
  );
}
