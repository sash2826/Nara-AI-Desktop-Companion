import type { WatchedFolder, WatcherStatus, IndexedDocument } from "@/services/ipc/IPCClient";

export type { WatchedFolder, WatcherStatus, IndexedDocument };

export type FileExtension = ".pdf" | ".docx" | ".txt" | ".md" | string;

export interface DocumentFilter {
  workspacePath: string | null;
  extension: FileExtension | null;
  search: string;
}

export type DocumentSortKey = "indexed_at" | "file_path" | "chunk_count" | "char_count";
export type SortDirection = "asc" | "desc";

export interface DocumentSort {
  key: DocumentSortKey;
  direction: SortDirection;
}
