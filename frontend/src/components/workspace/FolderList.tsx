import { Loader2, FolderOpen } from "lucide-react";
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
        <WatcherStatusBadge status={watcherStatus} />
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
