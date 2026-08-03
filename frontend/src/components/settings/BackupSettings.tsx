import { useState, useEffect, useCallback } from "react";
import { HardDrive, Plus, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { settingsService } from "@/services/settings/SettingsService";
import type { BackupSummary } from "@/services/ipc/IPCClient";
import { cn } from "@/lib/utils";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function BackupSettings() {
  const [backups, setBackups] = useState<BackupSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastCreated, setLastCreated] = useState<string | null>(null);

  const loadBackups = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const list = await settingsService.listBackups();
      setBackups(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load backups.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadBackups();
  }, [loadBackups]);

  const handleCreateBackup = async () => {
    setIsCreating(true);
    setError(null);
    setLastCreated(null);
    try {
      const result = await settingsService.createBackup("Created from Settings");
      setLastCreated(result.backup_id);
      await loadBackups();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backup failed.");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Backup</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Create a consistent snapshot of the SQLite database and Qdrant collection metadata.
          Backups are saved to the <code className="font-mono">backups/</code> directory.
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button size="sm" onClick={handleCreateBackup} disabled={isCreating} className="gap-1.5">
          {isCreating ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
          {isCreating ? "Creating…" : "Create Backup"}
        </Button>

        <Button variant="outline" size="sm" onClick={loadBackups} disabled={isLoading}>
          Refresh
        </Button>
      </div>

      {/* Success / error feedback */}
      {lastCreated && !error && (
        <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
          <CheckCircle2 size={13} className="text-success flex-shrink-0" />
          Backup <code className="font-mono">{lastCreated}</code> created successfully.
        </div>
      )}

      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive"
        >
          <AlertCircle size={13} className="flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Backup list */}
      <div>
        <p className="mb-2 text-xs font-medium text-foreground">
          Existing Backups
          {backups.length > 0 && (
            <span className="ml-1.5 text-muted-foreground">({backups.length})</span>
          )}
        </p>

        {isLoading ? (
          <div className="flex items-center gap-2 py-4 text-xs text-muted-foreground">
            <Loader2 size={13} className="animate-spin" />
            Loading…
          </div>
        ) : backups.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border py-8 text-center">
            <HardDrive size={20} className="text-muted-foreground" strokeWidth={1.5} />
            <p className="text-xs text-muted-foreground">No backups yet.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {backups.map((backup) => (
              <div
                key={backup.backup_id}
                className={cn(
                  "flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-3 py-2.5",
                  lastCreated === backup.backup_id && "border-ring/50 bg-accent/30"
                )}
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate font-mono text-xs text-foreground">{backup.backup_id}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(backup.created_at)}</p>
                </div>
                <div className="flex flex-shrink-0 items-center gap-3">
                  <span className="text-xs text-muted-foreground">
                    {formatBytes(backup.sqlite_size_bytes)}
                  </span>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-2xs font-medium",
                      backup.status === "complete"
                        ? "bg-success/15 text-success"
                        : "bg-warning/15 text-warning"
                    )}
                  >
                    {backup.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
