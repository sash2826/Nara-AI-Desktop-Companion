import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, RefreshCw, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { IPCClient } from "@/services/ipc/IPCClient";
import type { IndexingError } from "@/services/ipc/IPCClient";
import { FilePathChip } from "@/components/assistant/FilePathChip";
import { useWorkspaceStore } from "@/store/workspaceStore";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString([], {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function IndexingErrorsTab() {
  const setErrorCount = useWorkspaceStore((s) => s.setErrorCount);
  const [errors, setErrors] = useState<IndexingError[]>([]);
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!IS_TAURI) return;
    setLoading(true);
    setFetchError(null);
    try {
      const data = await IPCClient.listIndexingErrors();
      setErrors(data);
      setErrorCount(data.length);
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : "Failed to load indexing errors");
    } finally {
      setLoading(false);
    }
  }, [setErrorCount]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load().catch(() => {});
  }, [load]);

  const handleClearAll = async () => {
    setClearing(true);
    try {
      await IPCClient.clearIndexingErrors();
      setErrors([]);
      setErrorCount(0);
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : "Failed to clear errors");
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Indexing Errors</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Files that failed during indexing. Errors persist across restarts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => void load()}
            disabled={loading}
            title="Refresh"
            className={cn(
              "inline-flex h-7 w-7 items-center justify-center rounded-md border border-border",
              "bg-background text-muted-foreground transition-colors hover:bg-accent hover:text-foreground",
              "disabled:pointer-events-none disabled:opacity-50"
            )}
          >
            <RefreshCw size={12} className={cn(loading && "animate-spin")} strokeWidth={1.5} />
          </button>

          {errors.length > 0 && (
            <button
              onClick={() => void handleClearAll()}
              disabled={clearing}
              className={cn(
                "inline-flex h-7 items-center gap-1.5 rounded-md border border-destructive/30 px-2.5 text-xs font-medium",
                "bg-destructive/10 text-destructive transition-colors hover:bg-destructive/20",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              <Trash2 size={11} strokeWidth={1.5} />
              {clearing ? "Clearing…" : "Clear all"}
            </button>
          )}
        </div>
      </div>

      {/* Error state */}
      {fetchError && (
        <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {fetchError}
        </p>
      )}

      {/* Empty state */}
      {!loading && !fetchError && errors.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-12 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted">
            <AlertTriangle size={20} className="text-muted-foreground" strokeWidth={1.5} />
          </div>
          <p className="text-sm text-muted-foreground">No indexing errors on record.</p>
        </div>
      )}

      {/* Error table */}
      {errors.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-3 py-2 text-left font-semibold text-muted-foreground">File</th>
                <th className="px-3 py-2 text-left font-semibold text-muted-foreground">Error</th>
                <th className="whitespace-nowrap px-3 py-2 text-left font-semibold text-muted-foreground">
                  Failed at
                </th>
              </tr>
            </thead>
            <tbody>
              {errors.map((error, i) => (
                <tr
                  key={error.id}
                  className={cn(
                    "border-b border-border last:border-0",
                    i % 2 === 0 ? "bg-background" : "bg-muted/20"
                  )}
                >
                  <td className="px-3 py-2 align-top">
                    <FilePathChip path={error.file_path} />
                  </td>
                  <td className="px-3 py-2 align-top">
                    <p className="break-all font-mono text-xs text-warning leading-relaxed">
                      {error.error_message}
                    </p>
                  </td>
                  <td className="whitespace-nowrap px-3 py-2 align-top text-muted-foreground">
                    {formatTimestamp(error.failed_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
