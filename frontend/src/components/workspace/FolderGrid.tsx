import { cn } from "@/lib/utils";
import type { FolderTreeNode } from "./folderTree";

/**
 * Gradient definitions for the folder glyph. Rendered once per grid so the
 * repeated tiles can share them instead of duplicating ids.
 */
function FolderIconDefs() {
  return (
    <svg width="0" height="0" aria-hidden="true" style={{ position: "absolute" }}>
      <defs>
        <linearGradient id="nara-folder-back" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4CAFEE" />
          <stop offset="100%" stopColor="#2B93DD" />
        </linearGradient>
        <linearGradient id="nara-folder-front" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#84D2FB" />
          <stop offset="100%" stopColor="#51B8F3" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function FolderGlyph({ size = 100 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size * 0.79}
      viewBox="0 0 96 76"
      aria-hidden="true"
      style={{ display: "block", filter: "drop-shadow(0 2px 3px hsl(0 0% 0% / 0.25))" }}
    >
      <path
        d="M4 14a8 8 0 0 1 8-8h21.4a4 4 0 0 1 2.83 1.17L44 15h40a8 8 0 0 1 8 8v45a8 8 0 0 1-8 8H12a8 8 0 0 1-8-8z"
        fill="url(#nara-folder-back)"
      />
      <path
        d="M4 24a6 6 0 0 1 6-6h76a6 6 0 0 1 6 6v44a8 8 0 0 1-8 8H12a8 8 0 0 1-8-8z"
        fill="url(#nara-folder-front)"
      />
    </svg>
  );
}

interface FolderTileProps {
  node: FolderTreeNode;
  /** Includes suggestions targeting this folder's subfolders. */
  badgeCount: number;
  selected: boolean;
  onSelect: () => void;
  onOpen: () => void;
}

function FolderTile({ node, badgeCount, selected, onSelect, onOpen }: FolderTileProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      onDoubleClick={onOpen}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          onOpen();
        }
      }}
      title={node.path}
      aria-label={`${node.name}, ${node.documentCount} files${
        badgeCount > 0 ? `, ${badgeCount} suggestions` : ""
      }`}
      className={cn(
        "flex w-[140px] flex-col items-center gap-1.5 rounded-lg px-2 py-3 transition-colors",
        selected ? "bg-accent" : "hover:bg-accent/50"
      )}
    >
      <span className="relative">
        <FolderGlyph />
        {badgeCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-6 min-w-6 items-center justify-center rounded-full border-2 border-background bg-warning px-1.5 text-xs font-bold tabular-nums text-warning-foreground">
            {badgeCount > 99 ? "99+" : badgeCount}
          </span>
        )}
      </span>
      <span className="w-full truncate text-center text-sm font-medium text-foreground">
        {node.name}
      </span>
      <span className="text-2xs text-muted-foreground">
        {node.documentCount} file{node.documentCount !== 1 ? "s" : ""}
      </span>
    </button>
  );
}
interface FolderGridProps {
  nodes: FolderTreeNode[];
  badgeCounts: Map<string, number>;
  selectedPath: string | null;
  onSelect: (path: string) => void;
  onOpen: (path: string) => void;
  emptyMessage: string;
}

/** Finder-style folder grid — single click selects, double click opens. */
export function FolderGrid({
  nodes,
  badgeCounts,
  selectedPath,
  onSelect,
  onOpen,
  emptyMessage,
}: FolderGridProps) {
  if (nodes.length === 0) {
    return <p className="text-xs text-muted-foreground">{emptyMessage}</p>;
  }

  return (
    <>
      <FolderIconDefs />
      <div className="flex flex-wrap gap-2">
        {nodes.map((node) => (
          <FolderTile
            key={node.path}
            node={node}
            badgeCount={badgeCounts.get(node.path) ?? 0}
            selected={selectedPath === node.path}
            onSelect={() => onSelect(node.path)}
            onOpen={() => onOpen(node.path)}
          />
        ))}
      </div>
    </>
  );
}
