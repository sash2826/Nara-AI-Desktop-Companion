import { useState } from "react";
import { ChevronRight, Folder, RefreshCw, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FolderTreeNode } from "./folderTree";

interface FolderTreeRowProps {
  node: FolderTreeNode;
  depth: number;
  selectedFolderPath: string | null;
  onSelect: (path: string) => void;
  onRemove: (id: string) => Promise<unknown>;
  onReindex: (path: string) => Promise<unknown>;
  /** Optional pending-suggestion count for this exact path, shown as an amber badge. */
  recommendationCounts?: Map<string, number>;
}

/** A single row in the folder tree, recursively rendering its children when expanded. */
export function FolderTreeRow({
  node,
  depth,
  selectedFolderPath,
  onSelect,
  onRemove,
  onReindex,
  recommendationCounts,
}: FolderTreeRowProps) {
  const [expanded, setExpanded] = useState(depth === 0);
  const [removing, setRemoving] = useState(false);
  const [reindexing, setReindexing] = useState(false);

  const hasChildren = node.children.length > 0;
  const isRoot = !!node.watchedFolder;
  const isSelected = selectedFolderPath === node.path;
  const recommendationCount = recommendationCounts?.get(node.path);

  const handleRemove = async () => {
    if (!node.watchedFolder) return;
    setRemoving(true);
    try {
      await onRemove(node.watchedFolder.id);
    } finally {
      setRemoving(false);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      await onReindex(node.path);
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => onSelect(node.path)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onSelect(node.path);
          }
        }}
        title={node.path}
        style={{ paddingLeft: 8 + depth * 14 }}
        className={cn(
          "group flex w-full items-center gap-1 rounded-md py-1.5 pr-2 text-left text-sm transition-colors",
          isSelected ? "bg-accent text-accent-foreground" : "text-foreground hover:bg-accent/50"
        )}
      >
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded((v) => !v);
          }}
          className={cn(
            "flex h-4 w-4 flex-shrink-0 items-center justify-center rounded text-muted-foreground transition-transform",
            !hasChildren && "invisible",
            expanded && "rotate-90"
          )}
          aria-label={expanded ? "Collapse" : "Expand"}
          tabIndex={-1}
        >
          <ChevronRight size={12} strokeWidth={2} />
        </button>

        <Folder size={14} className="flex-shrink-0 text-muted-foreground" strokeWidth={1.5} />
        <span className="min-w-0 flex-1 truncate">{node.name}</span>

        {!!recommendationCount && (
          <span className="flex-shrink-0 rounded-full bg-warning/15 px-1.5 py-0.5 text-2xs font-semibold text-warning">
            {recommendationCount}
          </span>
        )}
        <span className="flex-shrink-0 text-2xs text-muted-foreground">{node.documentCount}</span>

        {isRoot && (
          <span className="flex flex-shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
            <button
              onClick={(e) => {
                e.stopPropagation();
                void handleReindex();
              }}
              disabled={reindexing}
              title="Re-index folder"
              className={cn(
                "rounded p-0.5 text-muted-foreground transition-colors hover:bg-background hover:text-foreground",
                reindexing && "animate-spin text-primary"
              )}
              aria-label="Re-index folder"
            >
              <RefreshCw size={11} strokeWidth={1.5} />
            </button>
            {!node.watchedFolder?.is_protected && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  void handleRemove();
                }}
                disabled={removing}
                title="Remove folder"
                className="rounded p-0.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                aria-label="Remove folder"
              >
                <Trash2 size={11} strokeWidth={1.5} />
              </button>
            )}
          </span>
        )}
      </div>

      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <FolderTreeRow
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedFolderPath={selectedFolderPath}
              onSelect={onSelect}
              onRemove={onRemove}
              onReindex={onReindex}
              recommendationCounts={recommendationCounts}
            />
          ))}
        </div>
      )}
    </div>
  );
}
