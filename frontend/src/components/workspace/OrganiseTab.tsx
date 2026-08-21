import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { FolderInput, PackageSearch, Loader2, Folder } from "lucide-react";
import { cn } from "@/lib/utils";
import { WorkspaceFolderRail } from "./WorkspaceFolderRail";
import { RecommendationRow } from "./RecommendationRow";
import { FolderContentsList } from "./FolderContentsList";
import { buildFolderTree, flattenFolderTree, findDeepestMatch } from "./folderTree";
import { useWorkspace } from "@/hooks/useWorkspace";
import { IPCClient, PendingRecommendation, AuditStatus } from "@/services/ipc/IPCClient";

function folderName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
}

/**
 * Folder-scoped organisation review: pick a folder in the rail to see only the
 * suggestions that target it, plus its existing contents for context — instead
 * of a single flat list of every pending suggestion across the workspace.
 */
export function OrganiseTab() {
  const { folders, documents, selectedFolderPath } = useWorkspace();

  const [recommendations, setRecommendations] = useState<PendingRecommendation[]>([]);
  const [busy, setBusy] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Map<string, string>>(new Map());
  const [conflicts, setConflicts] = useState<Map<string, string>>(new Map()); // id → target folder
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

  const _doAccept = useCallback(
    async (
      rec: PendingRecommendation,
      folder: string,
      conflictStrategy: "error" | "replace" | "rename" = "error"
    ) => {
      setBusy((prev) => new Set(prev).add(rec.id));
      setErrors((prev) => {
        const m = new Map(prev);
        m.delete(rec.id);
        return m;
      });
      // Do NOT clear conflicts here — keep the conflict UI visible (disabled) while
      // the request is in-flight so the card never flips to "Move here" mid-request.
      try {
        await IPCClient.acceptRecommendation(rec.id, folder, conflictStrategy);
        // Success: clear conflict then remove the card.
        setConflicts((prev) => {
          const m = new Map(prev);
          m.delete(rec.id);
          return m;
        });
        setRecommendations((prev) => prev.filter((r) => r.id !== rec.id));
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : typeof err === "string" ? err : "Move failed";
        if (msg.includes("already exists")) {
          setConflicts((prev) => new Map(prev).set(rec.id, folder));
        } else {
          // Non-conflict error: clear conflict so the card returns to normal state.
          setConflicts((prev) => {
            const m = new Map(prev);
            m.delete(rec.id);
            return m;
          });
          setErrors((prev) => new Map(prev).set(rec.id, msg));
        }
      } finally {
        setBusy((prev) => {
          const next = new Set(prev);
          next.delete(rec.id);
          return next;
        });
      }
    },
    []
  );

  const handleAccept = useCallback(
    (rec: PendingRecommendation) => {
      const top = rec.candidates[0];
      if (!top) return;
      void _doAccept(rec, top.folder);
    },
    [_doAccept]
  );

  const handleChooseFolder = useCallback(
    async (rec: PendingRecommendation) => {
      const selected = await openDialog({ directory: true, multiple: false });
      if (!selected) return;
      void _doAccept(rec, selected as string);
    },
    [_doAccept]
  );

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

  const handleConflictReplace = useCallback(
    (rec: PendingRecommendation) => {
      const folder = conflicts.get(rec.id);
      if (!folder) return;
      void _doAccept(rec, folder, "replace");
    },
    [_doAccept, conflicts]
  );

  const handleConflictKeepBoth = useCallback(
    (rec: PendingRecommendation) => {
      const folder = conflicts.get(rec.id);
      if (!folder) return;
      void _doAccept(rec, folder, "rename");
    },
    [_doAccept, conflicts]
  );

  const handleConflictCancel = useCallback((id: string) => {
    setConflicts((prev) => {
      const m = new Map(prev);
      m.delete(id);
      return m;
    });
  }, []);

  // Group suggestions by the most specific folder (root or subfolder) that their
  // top candidate falls under, so each suggestion belongs to exactly one node in the rail.
  const flatNodes = useMemo(
    () => flattenFolderTree(buildFolderTree(folders, documents)),
    [folders, documents]
  );

  const recommendationsByFolderPath = useMemo(() => {
    const map = new Map<string, PendingRecommendation[]>();
    for (const rec of recommendations) {
      const top = rec.candidates[0];
      if (!top) continue;
      const owner = findDeepestMatch(flatNodes, top.folder);
      if (!owner) continue;
      const list = map.get(owner.path) ?? [];
      list.push(rec);
      map.set(owner.path, list);
    }
    return map;
  }, [recommendations, flatNodes]);

  const recommendationCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const [path, list] of recommendationsByFolderPath) counts.set(path, list.length);
    return counts;
  }, [recommendationsByFolderPath]);

  const selectedFolderRecs = selectedFolderPath
    ? (recommendationsByFolderPath.get(selectedFolderPath) ?? [])
    : [];
  const selectedFolderDocs = selectedFolderPath
    ? documents.filter((d) => d.file_path.startsWith(selectedFolderPath))
    : [];

  const statusLabel =
    auditStatus && auditStatus.total > 0
      ? `Analysed ${auditStatus.analysed} / ${auditStatus.total}`
      : auditRunning
        ? "Starting…"
        : null;

  const renderRec = (rec: PendingRecommendation) => (
    <RecommendationRow
      key={rec.id}
      rec={rec}
      isLoading={busy.has(rec.id)}
      errorMsg={errors.get(rec.id)}
      conflictFolder={conflicts.get(rec.id)}
      onAccept={handleAccept}
      onChooseFolder={(r) => void handleChooseFolder(r)}
      onDismiss={(id) => void handleDismiss(id)}
      onConflictReplace={handleConflictReplace}
      onConflictKeepBoth={handleConflictKeepBoth}
      onConflictCancel={handleConflictCancel}
    />
  );

  return (
    <div className="flex h-full min-h-0">
      <WorkspaceFolderRail recommendationCounts={recommendationCounts} />

      <div className="min-w-0 flex-1 overflow-y-auto px-4 py-4">
        {/* Action bar */}
        <div className="mb-4 flex items-center gap-3">
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

        {selectedFolderPath ? (
          <div className="flex flex-col gap-5">
            <div className="flex items-center gap-2">
              <Folder size={16} className="flex-shrink-0 text-muted-foreground" strokeWidth={1.5} />
              <h3 className="text-sm font-semibold text-foreground">
                {folderName(selectedFolderPath)}
              </h3>
              <span className="text-xs text-muted-foreground">
                {selectedFolderDocs.length} file{selectedFolderDocs.length !== 1 ? "s" : ""} ·{" "}
                {selectedFolderRecs.length} suggestion
                {selectedFolderRecs.length !== 1 ? "s" : ""} to review
              </span>
            </div>

            {selectedFolderRecs.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
                  <FolderInput size={13} strokeWidth={1.5} />
                  Suggested for this folder
                </p>
                {selectedFolderRecs.map(renderRec)}
              </div>
            )}

            <div>
              <p className="mb-2 text-xs font-semibold text-foreground">
                Contents ({selectedFolderDocs.length})
              </p>
              <FolderContentsList documents={selectedFolderDocs} />
            </div>
          </div>
        ) : recommendations.length === 0 && !auditRunning ? (
          /* Overview / empty state */
          <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-10 text-center">
            <PackageSearch size={32} strokeWidth={1} className="text-muted-foreground/50" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">No suggestions yet</p>
              <p className="text-xs text-muted-foreground">
                Run an audit to find files that may be better organised elsewhere.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border py-10 text-center">
            <p className="text-sm font-medium text-foreground">
              {recommendations.length} suggestion{recommendations.length !== 1 ? "s" : ""} ready to
              review
            </p>
            <p className="text-xs text-muted-foreground">
              Pick a folder on the left to review its suggestions one at a time.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
