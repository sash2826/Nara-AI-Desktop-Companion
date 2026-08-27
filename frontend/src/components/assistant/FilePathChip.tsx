import { useState, useCallback } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { IPCClient } from "@/services/ipc/IPCClient";
import { cn } from "@/lib/utils";
import { FileTypeIcon } from "@/components/common/FileTypeIcon";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

interface FilePathChipProps {
  path: string;
}

export function FilePathChip({ path }: FilePathChipProps) {
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState(false);

  // Strip trailing sentence punctuation swept up by the regex
  const cleanPath = path.replace(/[.,;:!?)]+$/, "");
  const trailingPunct = path.slice(cleanPath.length);

  const filename = cleanPath.replace(/\\/g, "/").split("/").at(-1) ?? cleanPath;

  const handleOpen = useCallback(async () => {
    if (!IS_TAURI) return;
    setOpening(true);
    setError(false);
    try {
      await IPCClient.openFile(cleanPath);
    } catch {
      setError(true);
    } finally {
      setOpening(false);
    }
  }, [cleanPath]);

  return (
    <>
      <button
        onClick={handleOpen}
        disabled={opening || !IS_TAURI}
        title={cleanPath}
        className={cn(
          "inline-flex max-w-[280px] items-center gap-1 rounded-md border px-1.5 py-0.5",
          "font-mono text-xs transition-colors",
          error
            ? "border-destructive/40 bg-destructive/10 text-destructive"
            : "border-border bg-muted text-foreground hover:border-primary/40 hover:bg-primary/5 hover:text-primary",
          "disabled:pointer-events-none disabled:opacity-60"
        )}
        aria-label={`Open ${filename}`}
      >
        {opening ? (
          <Loader2 size={11} className="flex-shrink-0 animate-spin" />
        ) : error ? (
          <AlertCircle size={11} className="flex-shrink-0" />
        ) : (
          <FileTypeIcon path={cleanPath} size={14} className="flex-shrink-0" />
        )}
        <span className="truncate">{filename}</span>
      </button>
      {trailingPunct}
    </>
  );
}
