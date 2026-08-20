import { AlertCircle, Loader2, Puzzle, ToggleLeft, ToggleRight } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { IPCClient, type PluginRecord } from "@/services/ipc/IPCClient";
import { cn } from "@/lib/utils";

const PERMISSION_LABELS: Record<string, string> = {
  "indexing.file_processing": "File processing",
  "indexing.text_processing": "Text processing",
  "search.enrichment": "Search enrichment",
};

function PermissionBadge({ permission }: { permission: string }) {
  return (
    <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
      {PERMISSION_LABELS[permission] ?? permission}
    </span>
  );
}

export function PluginSettings() {
  const [plugins, setPlugins] = useState<PluginRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toggling, setToggling] = useState<Set<string>>(new Set());

  const loadPlugins = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const list = await IPCClient.listPlugins();
      setPlugins(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadPlugins();
  }, [loadPlugins]);

  async function handleToggle(plugin: PluginRecord) {
    setToggling((prev) => new Set(prev).add(plugin.id));
    try {
      const updated = plugin.enabled
        ? await IPCClient.disablePlugin(plugin.id)
        : await IPCClient.enablePlugin(plugin.id);
      setPlugins((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setToggling((prev) => {
        const next = new Set(prev);
        next.delete(plugin.id);
        return next;
      });
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-foreground">Plugins</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Installed plugins extend indexing, text processing, and search. Drop a plugin folder into{" "}
          <code className="font-mono">%APPDATA%\Nara\plugins\</code> and restart the application to
          register it.
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
          <AlertCircle size={13} className="mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 size={13} className="animate-spin" />
          Loading plugins…
        </div>
      ) : plugins.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-10 text-center">
          <Puzzle size={28} strokeWidth={1.25} className="text-muted-foreground/50" />
          <div>
            <p className="text-sm font-medium text-foreground">No plugins installed</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Drop a plugin folder into <code className="font-mono">%APPDATA%\Nara\plugins\</code>{" "}
              and restart.
            </p>
          </div>
        </div>
      ) : (
        <ul className="space-y-3">
          {plugins.map((plugin) => (
            <li
              key={plugin.id}
              className={cn(
                "flex items-start justify-between gap-4 rounded-lg border border-border p-3",
                !plugin.enabled && "opacity-60"
              )}
            >
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <p className="truncate text-sm font-medium text-foreground">
                    {plugin.display_name}
                  </p>
                  <span className="flex-shrink-0 text-xs text-muted-foreground">
                    v{plugin.version}
                  </span>
                </div>
                {plugin.description && (
                  <p className="text-xs text-muted-foreground">{plugin.description}</p>
                )}
                {plugin.author && (
                  <p className="text-xs text-muted-foreground/70">by {plugin.author}</p>
                )}
                {plugin.permissions.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {plugin.permissions.map((p) => (
                      <PermissionBadge key={p} permission={p} />
                    ))}
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={() => void handleToggle(plugin)}
                disabled={toggling.has(plugin.id)}
                aria-label={
                  plugin.enabled
                    ? `Disable ${plugin.display_name}`
                    : `Enable ${plugin.display_name}`
                }
                className="flex-shrink-0 text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
              >
                {toggling.has(plugin.id) ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : plugin.enabled ? (
                  <ToggleRight size={20} className="text-primary" />
                ) : (
                  <ToggleLeft size={20} />
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
