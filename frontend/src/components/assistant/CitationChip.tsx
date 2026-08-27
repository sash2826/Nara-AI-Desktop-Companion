import { useState, useCallback } from "react";
import { Loader2, AlertCircle, Cloud } from "lucide-react";
import { IPCClient } from "@/services/ipc/IPCClient";
import { cn } from "@/lib/utils";
import { FileTypeIcon } from "@/components/common/FileTypeIcon";
import type { CitationMeta } from "@/types/conversation";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

interface CitationChipProps {
  citation: CitationMeta;
  index: number;
}

/**
 * Displays a single retrieved source as a clickable chip.
 *
 * Hovering reveals a tooltip with the source location.
 * Clicking opens the file via Tauri's shell opener.
 */
export function CitationChip({ citation, index }: CitationChipProps) {
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState(false);
  const [hovered, setHovered] = useState(false);

  const normalised = citation.documentPath.replace(/\\/g, "/");
  const segments = normalised.split("/").filter(Boolean);
  const filename = segments.at(-1) ?? citation.documentPath;
  const parentFolder = segments.at(-2) ?? null;
  const isOneDrive = /\/OneDrive[^/]*/i.test(normalised);

  const handleOpen = useCallback(async () => {
    if (!IS_TAURI) return;
    setOpening(true);
    setError(false);
    try {
      await IPCClient.openFile(citation.documentPath);
    } catch {
      setError(true);
    } finally {
      setOpening(false);
    }
  }, [citation.documentPath]);

  return (
    <div className="relative inline-flex">
      <button
        onClick={handleOpen}
        disabled={opening || !IS_TAURI}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onFocus={() => setHovered(true)}
        onBlur={() => setHovered(false)}
        className={cn(
          "inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5",
          "text-2xs font-medium transition-colors",
          error
            ? "border-destructive/40 bg-destructive/10 text-destructive"
            : "border-border bg-muted text-muted-foreground hover:border-primary/40 hover:bg-primary/5 hover:text-primary",
          "disabled:pointer-events-none disabled:opacity-60"
        )}
        aria-label={`Source ${index}: ${filename}`}
      >
        {opening ? (
          <Loader2 size={10} className="flex-shrink-0 animate-spin" />
        ) : error ? (
          <AlertCircle size={10} className="flex-shrink-0" />
        ) : (
          <FileTypeIcon path={citation.documentPath} size={13} className="flex-shrink-0" />
        )}
        <span className="max-w-[200px] truncate">{filename}</span>
        {isOneDrive && (
          <Cloud
            size={9}
            className="flex-shrink-0 text-blue-400"
            strokeWidth={1.5}
            aria-label="OneDrive"
          />
        )}
      </button>

      {/* Hover tooltip — pure CSS positioning, no library dependency */}
      {hovered && (
        <div
          className={cn(
            "absolute bottom-full left-0 z-50 mb-1.5 w-64",
            "rounded-lg border border-border bg-popover px-3 py-2 shadow-md",
            "pointer-events-none"
          )}
          role="tooltip"
        >
          <p className="mb-1 break-all font-mono text-2xs text-foreground">
            {parentFolder ? `${parentFolder} / ${filename}` : filename}
          </p>
          <div className="flex items-center text-2xs text-muted-foreground">
            {isOneDrive && (
              <span className="flex items-center gap-1 text-blue-400">
                <Cloud size={9} strokeWidth={1.5} />
                OneDrive
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
