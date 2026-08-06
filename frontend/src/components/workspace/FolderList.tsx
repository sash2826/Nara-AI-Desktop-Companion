import { useState } from "react";
import { Loader2, FolderOpen, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { FolderRow } from "./FolderRow";
import { AddFolderInput } from "./AddFolderInput";
import { WatcherStatusBadge } from "./WatcherStatusBadge";
import { useWorkspace } from "@/hooks/useWorkspace";

export function FolderList() {
  const {
    folders,
    watcherStatus,
    watcherLoading,
    watcherError,
    addFolder,
    removeFolder,
    indexFolder,
  } = useWorkspace();
  const [reindexingAll, setReindexingAll] = useState(false);

  const handleReindexAll = async () => {
    if (folders.length === 0 || reindexingAll) return;
    setReindexingAll(true);
    try {
      await Promise.all(folders.map((f) => indexFolder(f.path)));
    } finally {
      setReindexingAll(false);
    }
  };

  if (watcherLoading) {
    return (
      <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
        <Loader2 size={16} className="animate-spin" />
        <span className="text-sm">Loading folders…</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Watched Folders</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Files in these folders are indexed automatically.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {folders.length > 0 && (
            <button
              onClick={handleReindexAll}
              disabled={reindexingAll}
              title="Re-index all folders"
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
                reindexingAll && "cursor-not-allowed opacity-60"
              )}
            >
              <RefreshCw
                size={12}
                strokeWidth={1.5}
                className={reindexingAll ? "animate-spin" : ""}
              />
              Re-index All
            </button>
          )}
          <WatcherStatusBadge status={watcherStatus} />
        </div>
      </div>

      <AddFolderInput onAdd={addFolder} />

      {watcherError && (
        <p className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {watcherError}
        </p>
      )}

      {folders.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-10 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted">
            <FolderOpen size={20} className="text-muted-foreground" strokeWidth={1.5} />
          </div>
          <p className="text-sm text-muted-foreground">No folders added yet.</p>
          <p className="text-xs text-muted-foreground">
            Add a folder above to start automatic indexing.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {folders.map((folder) => (
            <FolderRow
              key={folder.id}
              folder={folder}
              onRemove={removeFolder}
              onReindex={indexFolder}
            />
          ))}
        </div>
      )}
    </div>
  );
}
