import { useState } from "react";
import { Trash2, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { FileTypeIcon } from "@/components/common/FileTypeIcon";
import type { IndexedDocument } from "@/types/workspace";

function getFileName(filePath: string): string {
  return filePath.replace(/\\/g, "/").split("/").pop() ?? filePath;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatSize(chars: number): string {
  if (chars >= 1_000_000) return `${(chars / 1_000_000).toFixed(1)}M chars`;
  if (chars >= 1_000) return `${(chars / 1_000).toFixed(0)}k chars`;
  return `${chars} chars`;
}

interface DocumentRowProps {
  document: IndexedDocument;
  /** Called when the user confirms single-document deletion. Parent handles optimistic removal + undo. */
  onDeleteRequested: (documentId: string) => void;
  isSelected: boolean;
  onToggleSelect: (documentId: string) => void;
  className?: string;
}

export function DocumentRow({
  document,
  onDeleteRequested,
  isSelected,
  onToggleSelect,
  className,
}: DocumentRowProps) {
  const fileName = getFileName(document.file_path);

  const [confirming, setConfirming] = useState(false);

  return (
    <div
      className={cn(
        "group flex items-center gap-3 rounded-lg border border-border bg-card px-3 py-2.5",
        "transition-colors hover:bg-accent/50",
        isSelected && "border-primary/40 bg-primary/5",
        confirming && "border-destructive/40 bg-destructive/5",
        className
      )}
    >
      {/* Checkbox */}
      <button
        onClick={() => onToggleSelect(document.id)}
        aria-label={isSelected ? `Deselect ${fileName}` : `Select ${fileName}`}
        className={cn(
          "flex h-4 w-4 flex-shrink-0 items-center justify-center rounded border transition-colors",
          isSelected
            ? "border-primary bg-primary text-primary-foreground"
            : "border-border bg-background opacity-0 group-hover:opacity-100 focus-visible:opacity-100",
          isSelected && "opacity-100"
        )}
      >
        {isSelected && <Check size={10} strokeWidth={3} />}
      </button>

      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-muted">
        <FileTypeIcon path={document.file_path} size={20} />
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-foreground" title={document.file_path}>
          {fileName}
        </p>
        <p className="truncate text-xs text-muted-foreground" title={document.file_path}>
          {document.file_path}
        </p>
      </div>

      {/* Metadata — hidden during confirmation */}
      {!confirming && (
        <div className="flex flex-shrink-0 flex-col items-end gap-0.5">
          <span className="text-xs text-muted-foreground">
            {document.chunk_count} chunk{document.chunk_count !== 1 ? "s" : ""}
          </span>
          <span className="text-2xs text-muted-foreground">
            {formatSize(document.char_count)} · {formatDate(document.indexed_at)}
          </span>
        </div>
      )}

      {/* Confirmation row */}
      {confirming && (
        <div className="flex flex-shrink-0 items-center gap-2">
          <span className="text-xs text-destructive">Remove from index?</span>
          <button
            onClick={() => {
              setConfirming(false);
              onDeleteRequested(document.id);
            }}
            className="rounded-md bg-destructive px-2 py-0.5 text-2xs font-medium text-destructive-foreground hover:bg-destructive/90"
          >
            Delete
          </button>
          <button
            onClick={() => setConfirming(false)}
            className="rounded-md border border-border px-2 py-0.5 text-2xs font-medium text-muted-foreground hover:bg-accent"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Delete button — visible on hover when idle and not selected */}
      {!confirming && !isSelected && (
        <button
          onClick={() => setConfirming(true)}
          title="Remove from index"
          aria-label={`Delete ${fileName} from index`}
          className={cn(
            "ml-1 flex-shrink-0 rounded-md p-1 transition-colors",
            "text-muted-foreground opacity-0 group-hover:opacity-100",
            "hover:bg-destructive/10 hover:text-destructive",
            "focus-visible:opacity-100"
          )}
        >
          <Trash2 size={13} strokeWidth={1.5} />
        </button>
      )}
    </div>
  );
}
