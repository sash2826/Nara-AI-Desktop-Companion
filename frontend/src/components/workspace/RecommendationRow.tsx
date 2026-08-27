import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { FileTypeIcon } from "@/components/common/FileTypeIcon";
import type { PendingRecommendation } from "@/services/ipc/IPCClient";

interface RecommendationRowProps {
  rec: PendingRecommendation;
  isLoading: boolean;
  errorMsg?: string;
  conflictFolder?: string;
  onAccept: (rec: PendingRecommendation) => void;
  onChooseFolder: (rec: PendingRecommendation) => void;
  onDismiss: (id: string) => void;
  onConflictReplace: (rec: PendingRecommendation) => void;
  onConflictKeepBoth: (rec: PendingRecommendation) => void;
  onConflictCancel: (id: string) => void;
}

/** A single pending file-placement suggestion, with its move/skip/conflict controls. */
export function RecommendationRow({
  rec,
  isLoading,
  errorMsg,
  conflictFolder,
  onAccept,
  onChooseFolder,
  onDismiss,
  onConflictReplace,
  onConflictKeepBoth,
  onConflictCancel,
}: RecommendationRowProps) {
  const fileName = rec.source_path.split(/[\\/]/).pop() ?? rec.source_path;
  const top = rec.candidates[0];
  const folderName = top ? (top.folder.split(/[\\/]/).pop() ?? top.folder) : null;
  const conflictFolderName = conflictFolder
    ? (conflictFolder.split(/[\\/]/).pop() ?? conflictFolder)
    : null;

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 rounded-md border bg-background px-3 py-2 text-xs",
        conflictFolder ? "border-orange-500/30" : "border-amber-500/20"
      )}
    >
      <div className="min-w-0 flex flex-1 gap-2">
        <FileTypeIcon path={rec.source_path} size={19} className="mt-0.5 flex-shrink-0" />
        <div className="min-w-0 flex-1">
          <span className="block truncate font-medium text-foreground">{fileName}</span>
          {conflictFolder ? (
            <span className="text-orange-500 dark:text-orange-400">
              A file named <span className="font-semibold">{fileName}</span> already exists in{" "}
              <span className="font-semibold">{conflictFolderName}</span>.
            </span>
          ) : (
            <>
              {top && folderName && (
                <span className="text-muted-foreground">
                  → {folderName}
                  <span
                    className={cn(
                      "ml-1.5 rounded px-1 py-0.5 text-2xs font-semibold",
                      top.label === "Strong" &&
                        "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
                      top.label === "Good" && "bg-blue-500/15 text-blue-600 dark:text-blue-400",
                      top.label === "Possible" && "bg-muted text-muted-foreground"
                    )}
                  >
                    {top.label}
                  </span>
                  <span className="ml-1 text-2xs tabular-nums text-muted-foreground">
                    {Math.round(top.score * 100)}%
                  </span>
                </span>
              )}
              {errorMsg && (
                <span className="mt-0.5 block text-2xs text-destructive">{errorMsg}</span>
              )}
            </>
          )}
        </div>
      </div>
      <div className="flex flex-shrink-0 items-center gap-1.5">
        {conflictFolder ? (
          <>
            <button
              onClick={() => onConflictReplace(rec)}
              disabled={isLoading}
              className="rounded border border-orange-500/30 bg-orange-500/10 px-2 py-1 text-2xs font-medium text-orange-600 dark:text-orange-400 transition-colors hover:bg-orange-500/20 disabled:opacity-50"
            >
              Replace
            </button>
            <button
              onClick={() => onConflictKeepBoth(rec)}
              disabled={isLoading}
              className="rounded border border-primary/30 bg-primary/10 px-2 py-1 text-2xs font-medium text-primary transition-colors hover:bg-primary/20 disabled:opacity-50"
            >
              Keep both
            </button>
            <button
              onClick={() => onConflictCancel(rec.id)}
              disabled={isLoading}
              aria-label="Cancel"
              className="rounded p-1 text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
            >
              <X size={12} />
            </button>
          </>
        ) : (
          <>
            {top && (
              <button
                onClick={() => onAccept(rec)}
                disabled={isLoading}
                className="rounded border border-primary/30 bg-primary/10 px-2 py-1 text-2xs font-medium text-primary transition-colors hover:bg-primary/20 disabled:opacity-50"
              >
                Move here
              </button>
            )}
            <button
              onClick={() => onChooseFolder(rec)}
              disabled={isLoading}
              className="rounded border border-border px-2 py-1 text-2xs font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
            >
              Choose folder…
            </button>
            <button
              onClick={() => onDismiss(rec.id)}
              disabled={isLoading}
              aria-label="Dismiss suggestion"
              className="rounded p-1 text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
            >
              <X size={12} />
            </button>
          </>
        )}
      </div>
    </div>
  );
}
