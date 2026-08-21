import { useMemo, useState } from "react";
import { Files, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { FolderTreeRow } from "./FolderTreeRow";
import { buildFolderTree } from "./folderTree";
import { AddFolderInput } from "./AddFolderInput";
import { WatcherStatusBadge } from "./WatcherStatusBadge";
import { useWorkspace } from "@/hooks/useWorkspace";

/**
 * File-explorer-style left rail: watched folders (and their subfolders,
 * derived from indexed document paths) with live document counts.
 * Selecting a folder scopes DocumentBrowser's list to that folder's files.
 */
interface WorkspaceFolderRailProps {
  /** Optional folder-path -> pending-suggestion-count map, shown as an amber badge (used by Organise). */
  recommendationCounts?: Map<string, number>;
}

export function WorkspaceFolderRail({ recommendationCounts }: WorkspaceFolderRailProps = {}) {
  const {
    folders,
    documents,
    watcherStatus,
    selectedFolderPath,
    setSelectedFolder,
    addFolder,
    removeFolder,
    indexFolder,
  } = useWorkspace();

  const [isAdding, setIsAdding] = useState(false);

  const tree = useMemo(() => buildFolderTree(folders, documents), [folders, documents]);

  return (
    <div className="flex h-full w-56 flex-shrink-0 flex-col border-r border-border">
      <div className="flex items-center justify-between gap-2 px-3 pb-2 pt-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Watched
        </h3>
        <div className="flex flex-shrink-0 items-center gap-1.5">
          <WatcherStatusBadge status={watcherStatus} className="text-2xs" />
          <button
            type="button"
            onClick={() => setIsAdding((v) => !v)}
            aria-label={isAdding ? "Cancel adding folder" : "Add folder"}
            title={isAdding ? "Cancel" : "Add folder"}
            className={cn(
              "flex h-5 w-5 flex-shrink-0 items-center justify-center rounded transition-colors",
              isAdding
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <Plus
              size={13}
              strokeWidth={1.75}
              className={cn("transition-transform duration-fast", isAdding && "rotate-45")}
            />
          </button>
        </div>
      </div>

      {isAdding && (
        <div className="px-2 pb-2">
          <AddFolderInput
            onAdd={async (path) => {
              const result = await addFolder(path);
              setIsAdding(false);
              return result;
            }}
          />
        </div>
      )}

      <div className="min-h-0 flex-1 space-y-0.5 overflow-y-auto px-2">
        <button
          type="button"
          onClick={() => setSelectedFolder(null)}
          className={cn(
            "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors",
            selectedFolderPath === null
              ? "bg-accent text-accent-foreground"
              : "text-foreground hover:bg-accent/50"
          )}
        >
          <Files size={14} className="flex-shrink-0 text-muted-foreground" strokeWidth={1.5} />
          <span className="min-w-0 flex-1 truncate">All files</span>
          <span className="flex-shrink-0 text-2xs text-muted-foreground">{documents.length}</span>
        </button>

        {tree.map((root) => (
          <FolderTreeRow
            key={root.path}
            node={root}
            depth={0}
            selectedFolderPath={selectedFolderPath}
            onSelect={(path) => setSelectedFolder(selectedFolderPath === path ? null : path)}
            onRemove={removeFolder}
            onReindex={indexFolder}
            recommendationCounts={recommendationCounts}
          />
        ))}
      </div>
    </div>
  );
}
