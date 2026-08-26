import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { FolderInput, PackageSearch, Loader2, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { RecommendationRow } from "./RecommendationRow";
import { FolderContentsList } from "./FolderContentsList";
import { OrganiseDashboard } from "./OrganiseDashboard";
import { FolderGrid } from "./FolderGrid";
import {
  buildFolderTree,
  flattenFolderTree,
  findDeepestMatch,
  findNodeByPath,
  aggregateCounts,
  isDirectChildFile,
} from "./folderTree";
import { useWorkspace } from "@/hooks/useWorkspace";
import { IPCClient, PendingRecommendation, AuditStatus } from "@/services/ipc/IPCClient";

const SKIP_ALL_KEY = "__all__";

/**
 * Finder-style organisation review: browse folders as tiles, double-click to
 * open one, and act on the suggestions that target that exact folder.
 */
export function OrganiseTab() {
  const { folders, documents } = useWorkspace();

  const [recommendations, setRecommendations] = useState<PendingRecommendation[]>([]);
  const [busy, setBusy] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Map<string, string>>(new Map());
  const [conflicts, setConflicts] = useState<Map<string, string>>(new Map()); // id → target folder
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditStatus, setAuditStatus] = useState<AuditStatus | null>(null);
  const [bulk, setBulk] = useState<{ key: string; done: number; total: number } | null>(null);
  const [confirmSkipAll, setConfirmSkipAll] = useState(false);
  // Folder currently opened for review; null shows the top-level grid.
  const [openPath, setOpenPath] = useState<string | null>(null);
  const [selectedTilePath, setSelectedTilePath] = useState<string | null>(null);
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

  // Bulk actions run sequentially and never interrupt mid-batch — anything that
  // conflicts or errors stays in the list as residue once the batch finishes.
  const handleAcceptMany = useCallback(
    async (key: string, recs: PendingRecommendation[], folder: string) => {
      setBulk({ key, done: 0, total: recs.length });
      for (let i = 0; i < recs.length; i++) {
        await _doAccept(recs[i], folder);
        setBulk({ key, done: i + 1, total: recs.length });
      }
      setBulk(null);
    },
    [_doAccept]
  );

  const handleDismissMany = useCallback(async (key: string, ids: string[]) => {
    setBulk({ key, done: 0, total: ids.length });
    for (let i = 0; i < ids.length; i++) {
      try {
        await IPCClient.dismissRecommendation(ids[i]);
        setRecommendations((prev) => prev.filter((r) => r.id !== ids[i]));
      } catch {
        // A failed skip shouldn't halt the rest of the batch.
      }
      setBulk({ key, done: i + 1, total: ids.length });
    }
    setBulk(null);
  }, []);

  // Group suggestions by the most specific folder (root or subfolder) that their
  // top candidate falls under, so each suggestion belongs to exactly one node in the rail.
  const folderTree = useMemo(() => buildFolderTree(folders, documents), [folders, documents]);
  const flatNodes = useMemo(() => flattenFolderTree(folderTree), [folderTree]);

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

  // Badges roll subfolder suggestions up into their parent folder.
  const badgeCounts = useMemo(() => {
    const own = new Map<string, number>();
    for (const [path, list] of recommendationsByFolderPath) own.set(path, list.length);
    return aggregateCounts(folderTree, own);
  }, [recommendationsByFolderPath, folderTree]);

  const openNode = openPath ? findNodeByPath(flatNodes, openPath) : null;
  const openFolderRecs = openPath ? (recommendationsByFolderPath.get(openPath) ?? []) : [];
  // Subfolder files are reachable by opening that subfolder, so only loose files show here.
  const openFolderDocs = openNode
    ? documents.filter((d) => isDirectChildFile(openNode.path, d.file_path))
    : [];

  // Breadcrumb trail from the watched root down to the open folder.
  const trail = useMemo(() => {
    if (!openNode) return [];
    return flatNodes
      .filter((n) => openNode.path === n.path || openNode.path.startsWith(n.path))
      .sort((a, b) => a.path.length - b.path.length);
  }, [flatNodes, openNode]);

  const statusLabel =
    auditStatus && auditStatus.total > 0
      ? `Analysed ${auditStatus.analysed} / ${auditStatus.total}`
      : auditRunning
        ? "Starting…"
        : null;

  const isBulkBusy = bulk !== null;

  const handleOpenFolder = useCallback((path: string) => {
    setOpenPath(path);
    setSelectedTilePath(null);
  }, []);

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

          {recommendations.length > 1 && (
            <div className="ml-auto flex items-center gap-2">
              {confirmSkipAll ? (
                <>
                  <span className="text-xs text-foreground">
                    Skip all {recommendations.length}?
                  </span>
                  <button
                    onClick={() => {
                      setConfirmSkipAll(false);
                      void handleDismissMany(
                        SKIP_ALL_KEY,
                        recommendations.map((r) => r.id)
                      );
                    }}
                    disabled={isBulkBusy}
                    className="rounded-md border border-destructive/50 bg-destructive/10 px-2.5 py-1 text-xs font-semibold text-destructive transition-colors hover:bg-destructive/20 disabled:opacity-50"
                  >
                    Skip all
                  </button>
                  <button
                    onClick={() => setConfirmSkipAll(false)}
                    className="rounded-md border border-border px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent/50"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setConfirmSkipAll(true)}
                  disabled={isBulkBusy}
                  className="text-xs text-muted-foreground transition-colors hover:text-foreground disabled:opacity-50"
                >
                  {bulk?.key === SKIP_ALL_KEY
                    ? `Skipping ${bulk.done}/${bulk.total}…`
                    : `Skip all ${recommendations.length}`}
                </button>
              )}
            </div>
          )}
        </div>

        {openNode ? (
          <div className="flex flex-col gap-5">
            {/* Breadcrumb */}
            <div className="flex flex-wrap items-center gap-1 text-xs">
              <button
                onClick={() => setOpenPath(null)}
                className="rounded px-1.5 py-0.5 text-muted-foreground transition-colors hover:bg-accent/50 hover:text-foreground"
              >
                All folders
              </button>
              {trail.map((node, i) => (
                <span key={node.path} className="flex items-center gap-1">
                  <ChevronRight size={12} className="text-muted-foreground" />
                  {i === trail.length - 1 ? (
                    <span className="px-1 font-semibold text-foreground">{node.name}</span>
                  ) : (
                    <button
                      onClick={() => handleOpenFolder(node.path)}
                      className="rounded px-1.5 py-0.5 text-muted-foreground transition-colors hover:bg-accent/50 hover:text-foreground"
                    >
                      {node.name}
                    </button>
                  )}
                </span>
              ))}
              <span className="ml-1 text-muted-foreground">
                {openFolderDocs.length} file{openFolderDocs.length !== 1 ? "s" : ""} ·{" "}
                {openFolderRecs.length} suggestion{openFolderRecs.length !== 1 ? "s" : ""} here
              </span>
            </div>

            {openNode.children.length > 0 && (
              <FolderGrid
                nodes={openNode.children}
                badgeCounts={badgeCounts}
                selectedPath={selectedTilePath}
                onSelect={setSelectedTilePath}
                onOpen={handleOpenFolder}
                emptyMessage="No subfolders."
              />
            )}

            {openFolderRecs.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
                  <FolderInput size={13} strokeWidth={1.5} />
                  Suggested for this folder
                </p>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() =>
                      void handleAcceptMany(openNode.path, openFolderRecs, openNode.path)
                    }
                    disabled={isBulkBusy}
                    title={openNode.path}
                    className="rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                  >
                    {bulk?.key === openNode.path
                      ? `Moving ${bulk.done}/${bulk.total}…`
                      : `Move all ${openFolderRecs.length} to ${openNode.name}`}
                  </button>
                  <button
                    onClick={() =>
                      void handleDismissMany(
                        openNode.path,
                        openFolderRecs.map((r) => r.id)
                      )
                    }
                    disabled={isBulkBusy}
                    className="rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-accent/50 disabled:opacity-50"
                  >
                    Skip this folder
                  </button>
                </div>

                {openFolderRecs.map(renderRec)}
              </div>
            )}

            <div>
              <p className="mb-2 text-xs font-semibold text-foreground">
                Contents ({openFolderDocs.length})
              </p>
              <FolderContentsList documents={openFolderDocs} />
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-5">
            {recommendations.length === 0 && !auditRunning ? (
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
              <OrganiseDashboard recommendations={recommendations} />
            )}

            <div className="flex flex-col gap-2">
              <p className="text-xs font-semibold text-foreground">Folders ({folderTree.length})</p>
              <FolderGrid
                nodes={folderTree}
                badgeCounts={badgeCounts}
                selectedPath={selectedTilePath}
                onSelect={setSelectedTilePath}
                onOpen={handleOpenFolder}
                emptyMessage="No watched folders yet."
              />
              <p className="text-2xs text-muted-foreground">
                Double-click a folder to review its suggestions.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
