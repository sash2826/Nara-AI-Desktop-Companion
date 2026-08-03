import { useState } from "react";
import { Folder, Trash2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import type { WatchedFolder } from "@/types/workspace";

interface FolderRowProps {
  folder: WatchedFolder;
  onRemove: (id: string) => Promise<unknown>;
  onReindex: (path: string) => Promise<unknown>;
}

export function FolderRow({ folder, onRemove, onReindex }: FolderRowProps) {
  const [removing, setRemoving] = useState(false);
  const [reindexing, setReindexing] = useState(false);

  const handleRemove = async () => {
    setRemoving(true);
    try {
      await onRemove(folder.id);
    } finally {
      setRemoving(false);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      await onReindex(folder.path);
    } finally {
      setReindexing(false);
    }
  };

  const displayPath = folder.path.length > 60 ? `…${folder.path.slice(-57)}` : folder.path;

  return (
    <div className="group flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5 transition-colors hover:bg-accent/50">
      <Folder size={16} className="flex-shrink-0 text-muted-foreground" strokeWidth={1.5} />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-foreground" title={folder.path}>
          {displayPath}
        </p>
        <p className="text-2xs text-muted-foreground">
          Added {new Date(folder.added_at).toLocaleDateString()}
        </p>
      </div>
      <div className="flex flex-shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          onClick={handleReindex}
          disabled={reindexing}
          title="Re-index folder"
          className={cn(
            "rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
            reindexing && "animate-spin text-primary"
          )}
          aria-label="Re-index folder"
        >
          <RefreshCw size={13} strokeWidth={1.5} />
        </button>
        <button
          onClick={handleRemove}
          disabled={removing}
          title="Remove folder"
          className="rounded p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          aria-label="Remove folder"
        >
          <Trash2 size={13} strokeWidth={1.5} />
        </button>
      </div>
    </div>
  );
}
