import { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { useOrbWindowStore } from "./orbWindowStore";

export interface Recommendation {
  id: string;
  source_path: string;
  candidates: Array<{
    folder: string;
    score: number;
    label: "Most Likely" | "Likely" | "Possible";
  }>;
}

export interface BulkProgress {
  /** Group key currently being processed, or "__all__" for skip-all. */
  key: string;
  done: number;
  total: number;
}

export interface UseRecommendationsResult {
  recommendations: Recommendation[];
  loading: boolean;
  errors: Map<string, string>;
  conflicts: Map<string, string>;
  bulk: BulkProgress | null;
  handleAccept: (recId: string, folder: string) => void;
  handleChooseFolder: (recId: string) => Promise<void>;
  handleConflictReplace: (recId: string) => void;
  handleConflictKeepBoth: (recId: string) => void;
  handleConflictCancel: (recId: string) => void;
  handleSkip: (recId: string) => Promise<void>;
  handleAcceptMany: (key: string, recIds: string[], folder: string) => Promise<void>;
  handleSkipMany: (key: string, recIds: string[]) => Promise<void>;
  handleDismiss: () => void;
}

export function useRecommendations(): UseRecommendationsResult {
  const { setOverlayMode, setPendingCount } = useOrbWindowStore();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<Map<string, string>>(new Map());
  const [conflicts, setConflicts] = useState<Map<string, string>>(new Map());
  const [bulk, setBulk] = useState<BulkProgress | null>(null);

  const fetchRecommendations = useCallback(() => {
    invoke<Recommendation[]>("list_pending_recommendations")
      .then((recs) => {
        setRecommendations(recs);
        setPendingCount(recs.length);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [setPendingCount]);

  useEffect(() => {
    fetchRecommendations();
    const interval = setInterval(fetchRecommendations, 5_000);
    return () => clearInterval(interval);
  }, [fetchRecommendations]);

  const handleDismiss = useCallback(() => {
    setOverlayMode("none");
  }, [setOverlayMode]);

  // Uses functional setState to avoid stale closure on the recommendations array.
  const _removeRec = useCallback(
    (recId: string) => {
      setRecommendations((prev) => {
        const updated = prev.filter((r) => r.id !== recId);
        setPendingCount(updated.length);
        if (updated.length === 0) setOverlayMode("none");
        return updated;
      });
    },
    [setPendingCount, setOverlayMode]
  );

  const _doAccept = useCallback(
    async (
      recId: string,
      folder: string,
      conflictStrategy: "error" | "replace" | "rename" = "error"
    ) => {
      setErrors((prev) => {
        const m = new Map(prev);
        m.delete(recId);
        return m;
      });
      // Do NOT clear conflicts before the request completes — keeps the conflict
      // UI visible (disabled) while in-flight so the card never flips mid-request.
      try {
        await invoke("accept_recommendation", {
          recommendationId: recId,
          folder,
          conflictStrategy,
        });
        setConflicts((prev) => {
          const m = new Map(prev);
          m.delete(recId);
          return m;
        });
        _removeRec(recId);
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : typeof err === "string" ? err : "Move failed";
        if (msg.includes("already exists")) {
          setConflicts((prev) => new Map(prev).set(recId, folder));
        } else {
          setConflicts((prev) => {
            const m = new Map(prev);
            m.delete(recId);
            return m;
          });
          setErrors((prev) => new Map(prev).set(recId, msg));
        }
      }
    },
    [_removeRec]
  );

  const handleAccept = useCallback(
    (recId: string, folder: string) => void _doAccept(recId, folder),
    [_doAccept]
  );

  const handleChooseFolder = useCallback(
    async (recId: string) => {
      const selected = await openDialog({ directory: true, multiple: false });
      if (!selected) return;
      void _doAccept(recId, selected as string);
    },
    [_doAccept]
  );

  const handleConflictReplace = useCallback(
    (recId: string) => {
      const folder = conflicts.get(recId);
      if (!folder) return;
      void _doAccept(recId, folder, "replace");
    },
    [_doAccept, conflicts]
  );

  const handleConflictKeepBoth = useCallback(
    (recId: string) => {
      const folder = conflicts.get(recId);
      if (!folder) return;
      void _doAccept(recId, folder, "rename");
    },
    [_doAccept, conflicts]
  );

  const handleConflictCancel = useCallback((recId: string) => {
    setConflicts((prev) => {
      const m = new Map(prev);
      m.delete(recId);
      return m;
    });
  }, []);

  const handleSkip = useCallback(
    async (recId: string) => {
      try {
        await invoke("dismiss_recommendation", { recommendationId: recId });
        _removeRec(recId);
      } catch {
        handleDismiss();
      }
    },
    [_removeRec, handleDismiss]
  );

  // Runs sequentially and never interrupts mid-batch — files that conflict or
  // error stay pending and surface as residue once the batch finishes.
  const handleAcceptMany = useCallback(
    async (key: string, recIds: string[], folder: string) => {
      setBulk({ key, done: 0, total: recIds.length });
      for (let i = 0; i < recIds.length; i++) {
        await _doAccept(recIds[i], folder);
        setBulk({ key, done: i + 1, total: recIds.length });
      }
      setBulk(null);
    },
    [_doAccept]
  );

  const handleSkipMany = useCallback(
    async (key: string, recIds: string[]) => {
      setBulk({ key, done: 0, total: recIds.length });
      for (let i = 0; i < recIds.length; i++) {
        try {
          await invoke("dismiss_recommendation", { recommendationId: recIds[i] });
          _removeRec(recIds[i]);
        } catch {
          // A failed skip shouldn't halt the rest of the batch.
        }
        setBulk({ key, done: i + 1, total: recIds.length });
      }
      setBulk(null);
    },
    [_removeRec]
  );

  return {
    recommendations,
    loading,
    errors,
    conflicts,
    bulk,
    handleAccept,
    handleChooseFolder,
    handleConflictReplace,
    handleConflictKeepBoth,
    handleConflictCancel,
    handleSkip,
    handleAcceptMany,
    handleSkipMany,
    handleDismiss,
  };
}
