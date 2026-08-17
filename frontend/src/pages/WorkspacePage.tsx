import { useState, useEffect, useCallback, useRef } from "react";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import {
  Folders,
  Files,
  Activity,
  AlertTriangle,
  FolderInput,
  X,
  PackageSearch,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { FolderList } from "@/components/workspace/FolderList";
import { DocumentBrowser } from "@/components/workspace/DocumentBrowser";
import { IndexingStatusPanel } from "@/components/workspace/IndexingStatusPanel";
import { IndexingErrorsTab } from "@/components/workspace/IndexingErrorsTab";
import { useWorkspace } from "@/hooks/useWorkspace";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { IPCClient, PendingRecommendation, AuditStatus } from "@/services/ipc/IPCClient";

// ── Organise Tab ──────────────────────────────────────────────────────────────

function OrganiseTab() {
  const [recommendations, setRecommendations] = useState<PendingRecommendation[]>([]);
  const [busy, setBusy] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Map<string, string>>(new Map());
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditStatus, setAuditStatus] = useState<AuditStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchRecommendations = useCallback(() => {
    IPCClient.listPendingRecommendations()
      .then((recs) => setRecommendations(recs))
      .catch(() => {
        /* backend not ready */
      });
  }, []);

  // 5s rec polling
  useEffect(() => {
    fetchRecommendations();
    const interval = setInterval(fetchRecommendations, 5_000);
    return () => clearInterval(interval);
  }, [fetchRecommendations]);

  // 2s audit status polling while running
  const startAuditPoll = useCallback(() => {
    if (pollRef.current) return;
    pollRef.current = setInterval(async () => {
      try {
        const status = await IPCClient.getAuditStatus();
        setAuditStatus(status);
        if (!status.running) {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setAuditRunning(false);
          // Refresh suggestions once audit completes
          fetchRecommendations();
        }
      } catch {
        // ignore transient errors
      }
    }, 2_000);
  }, [fetchRecommendations]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // On mount, check if an audit was already running before this tab was visited
  // (e.g. user started audit then switched tabs). Resume polling so the spinner
  // and progress counter remain accurate regardless of navigation.
  useEffect(() => {
    IPCClient.getAuditStatus()
      .then((status) => {
        if (status.running) {
          setAuditRunning(true);
          setAuditStatus(status);
          startAuditPoll();
        }
      })
      .catch(() => {});
  }, [startAuditPoll]);

  const handleOrganise = useCallback(async () => {
    if (auditRunning) return;
    setAuditRunning(true);
    setAuditStatus({ running: true, analysed: 0, total: 0, found: 0 });
    try {
      await IPCClient.runOrganisationAudit();
      startAuditPoll();
    } catch {
      setAuditRunning(false);
      setAuditStatus(null);
    }
  }, [auditRunning, startAuditPoll]);

  const handleAccept = useCallback(async (rec: PendingRecommendation) => {
    const top = rec.candidates[0];
    if (!top) return;
    setBusy((prev) => new Set(prev).add(rec.id));
    setErrors((prev) => {
      const m = new Map(prev);
      m.delete(rec.id);
      return m;
    });
    try {
      await IPCClient.acceptRecommendation(rec.id, top.folder);
      setRecommendations((prev) => prev.filter((r) => r.id !== rec.id));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Move failed — file may no longer exist";
      setErrors((prev) => new Map(prev).set(rec.id, msg));
    } finally {
      setBusy((prev) => {
        const next = new Set(prev);
        next.delete(rec.id);
        return next;
      });
    }
  }, []);

  const handleChooseFolder = useCallback(async (rec: PendingRecommendation) => {
    const selected = await openDialog({ directory: true, multiple: false });
    if (!selected) return;
    setBusy((prev) => new Set(prev).add(rec.id));
    setErrors((prev) => {
      const m = new Map(prev);
      m.delete(rec.id);
      return m;
    });
    try {
      await IPCClient.acceptRecommendation(rec.id, selected as string);
      setRecommendations((prev) => prev.filter((r) => r.id !== rec.id));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Move failed";
      setErrors((prev) => new Map(prev).set(rec.id, msg));
    } finally {
      setBusy((prev) => {
        const next = new Set(prev);
        next.delete(rec.id);
        return next;
      });
    }
  }, []);

  const handleDismiss = useCallback(async (id: string) => {
    setBusy((prev) => new Set(prev).add(id));
    try {
      await IPCClient.dismissRecommendation(id);
      setRecommendations((prev) => prev.filter((r) => r.id !== id));
    } catch {
      // leave in list on failure
    } finally {
      setBusy((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }, []);

  const statusLabel =
    auditStatus && auditStatus.total > 0
      ? `Analysed ${auditStatus.analysed} / ${auditStatus.total}`
      : auditRunning
        ? "Starting…"
        : null;

  return (
    <div className="flex flex-col gap-4">
      {/* Action bar */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => void handleOrganise()}
          disabled={auditRunning}
          className={cn(
            "inline-flex items-center gap-2 rounded-md px-4 py-2 text-xs font-semibold transition-colors",
            auditRunning
              ? "bg-primary/20 text-primary cursor-not-allowed"
              : "bg-primary text-primary-foreground hover:bg-primary/90"
          )}
        >
          {auditRunning ? (
            <Loader2 size={13} className="animate-spin" strokeWidth={2} />
          ) : (
            <PackageSearch size={13} strokeWidth={1.5} />
          )}
          Organise
        </button>
        {statusLabel && <span className="text-xs text-muted-foreground">{statusLabel}</span>}
        {auditStatus && !auditRunning && auditStatus.found > 0 && (
          <span className="text-xs text-muted-foreground">
            Found {auditStatus.found} suggestion{auditStatus.found !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Suggestions list */}
      {recommendations.length > 0 ? (
        <div className="flex flex-col gap-2">
          <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
            <FolderInput size={13} strokeWidth={1.5} />
            File Suggestions
          </p>
          {recommendations.map((rec) => {
            const fileName = rec.source_path.split(/[\\/]/).pop() ?? rec.source_path;
            const top = rec.candidates[0];
            const folderName = top ? (top.folder.split(/[\\/]/).pop() ?? top.folder) : null;
            const isLoading = busy.has(rec.id);
            const errorMsg = errors.get(rec.id);

            return (
              <div
                key={rec.id}
                className="flex items-center justify-between gap-3 rounded-md border border-amber-500/20 bg-background px-3 py-2 text-xs"
              >
                <div className="min-w-0 flex-1">
                  <span className="block truncate font-medium text-foreground">{fileName}</span>
                  {top && folderName && (
                    <span className="text-muted-foreground">
                      → {folderName}
                      <span
                        className={cn(
                          "ml-1.5 rounded px-1 py-0.5 text-2xs font-semibold",
                          top.label === "Most Likely" &&
                            "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
                          top.label === "Likely" &&
                            "bg-blue-500/15 text-blue-600 dark:text-blue-400",
                          top.label === "Possible" && "bg-muted text-muted-foreground"
                        )}
                      >
                        {top.label}
                      </span>
                    </span>
                  )}
                  {errorMsg && (
                    <span className="mt-0.5 block text-2xs text-destructive">{errorMsg}</span>
                  )}
                </div>
                <div className="flex flex-shrink-0 items-center gap-1.5">
                  {top && (
                    <button
                      onClick={() => void handleAccept(rec)}
                      disabled={isLoading}
                      className="rounded border border-primary/30 bg-primary/10 px-2 py-1 text-2xs font-medium text-primary transition-colors hover:bg-primary/20 disabled:opacity-50"
                    >
                      Move here
                    </button>
                  )}
                  <button
                    onClick={() => void handleChooseFolder(rec)}
                    disabled={isLoading}
                    className="rounded border border-border px-2 py-1 text-2xs font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
                  >
                    Choose folder…
                  </button>
                  <button
                    onClick={() => void handleDismiss(rec.id)}
                    disabled={isLoading}
                    aria-label="Dismiss suggestion"
                    className="rounded p-1 text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
                  >
                    <X size={12} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : !auditRunning ? (
        /* Empty state */
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-10 text-center">
          <PackageSearch size={32} strokeWidth={1} className="text-muted-foreground/50" />
          <div className="space-y-1">
            <p className="text-sm font-medium text-foreground">No suggestions yet</p>
            <p className="text-xs text-muted-foreground">
              Run an audit to find files that may be better organised elsewhere.
            </p>
          </div>
          <button
            onClick={() => void handleOrganise()}
            className="mt-1 rounded-md bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Organise
          </button>
        </div>
      ) : null}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const STATIC_TABS = [
  { id: "folders" as const, label: "Folders", icon: Folders },
  { id: "documents" as const, label: "Documents", icon: Files },
  { id: "indexing" as const, label: "Indexing", icon: Activity },
  { id: "organise" as const, label: "Organise", icon: PackageSearch },
];

export function WorkspacePage() {
  const { activeTab, setActiveTab } = useWorkspace();
  const errorCount = useWorkspaceStore((s) => s.errorCount);

  return (
    <div className="flex h-full flex-col">
      {/* Tab bar */}
      <div className="flex flex-shrink-0 items-center gap-1 border-b border-border px-4 pt-4">
        {STATIC_TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-t-md border-b-2 px-3 pb-2.5 pt-1 text-xs font-medium transition-colors",
              activeTab === id
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon size={13} strokeWidth={1.5} />
            {label}
          </button>
        ))}

        {/* Errors tab — rendered separately so we can attach the badge */}
        <button
          onClick={() => setActiveTab("errors")}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-t-md border-b-2 px-3 pb-2.5 pt-1 text-xs font-medium transition-colors",
            activeTab === "errors"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          <AlertTriangle size={13} strokeWidth={1.5} />
          Errors
          {errorCount > 0 && (
            <span
              className={cn(
                "ml-0.5 flex h-4 min-w-4 items-center justify-center rounded-full px-1",
                "bg-destructive text-2xs font-semibold text-destructive-foreground"
              )}
            >
              {errorCount > 99 ? "99+" : errorCount}
            </span>
          )}
        </button>
      </div>

      {/* Tab content */}
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        {activeTab === "folders" && <FolderList />}
        {activeTab === "documents" && <DocumentBrowser />}
        {activeTab === "indexing" && <IndexingStatusPanel />}
        {activeTab === "organise" && <OrganiseTab />}
        {activeTab === "errors" && <IndexingErrorsTab />}
      </div>
    </div>
  );
}
