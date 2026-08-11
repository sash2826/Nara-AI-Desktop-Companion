import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { invoke } from "@tauri-apps/api/core";
import { useOrbWindowStore } from "./orbWindowStore";

interface Recommendation {
  id: string;
  source_path: string;
  candidates: Array<{
    folder: string;
    score: number;
    label: "Strong" | "Good" | "Possible";
  }>;
}

/**
 * Overlay showing pending file placement recommendations.
 * Appears when the user clicks the orb while it is in notification state.
 * Each item shows the file name, the top suggested folder, and Accept/Skip actions.
 */
export function OrbNotificationOverlay() {
  const { setOverlayMode, setPendingCount } = useOrbWindowStore();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    invoke<Recommendation[]>("list_pending_recommendations")
      .then((recs) => {
        setRecommendations(recs);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleDismiss = useCallback(() => {
    setOverlayMode("none");
  }, [setOverlayMode]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleDismiss();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [handleDismiss]);

  const handleAccept = useCallback(
    async (recId: string, folder: string) => {
      try {
        await invoke("accept_recommendation", { recommendationId: recId, folder });
        const updated = recommendations.filter((r) => r.id !== recId);
        setRecommendations(updated);
        setPendingCount(updated.length);
        if (updated.length === 0) setOverlayMode("none");
      } catch {
        // Errors surface in the main window; dismiss quietly here
        handleDismiss();
      }
    },
    [recommendations, setPendingCount, setOverlayMode, handleDismiss]
  );

  const handleSkip = useCallback(
    async (recId: string) => {
      try {
        await invoke("dismiss_recommendation", { recommendationId: recId });
        const updated = recommendations.filter((r) => r.id !== recId);
        setRecommendations(updated);
        setPendingCount(updated.length);
        if (updated.length === 0) setOverlayMode("none");
      } catch {
        handleDismiss();
      }
    },
    [recommendations, setPendingCount, setOverlayMode, handleDismiss]
  );

  const labelColor = (label: Recommendation["candidates"][0]["label"]) => {
    if (label === "Strong") return "hsl(142 70% 55%)";
    if (label === "Good") return "hsl(210 80% 65%)";
    return "hsl(0 0% 65%)";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.95 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      style={{
        position: "absolute",
        bottom: "calc(100% + 10px)",
        left: "50%",
        transform: "translateX(-50%)",
        width: 360,
        zIndex: 100,
        background: "hsl(0 0% 100% / 0.12)",
        backdropFilter: "blur(20px) saturate(180%)",
        WebkitBackdropFilter: "blur(20px) saturate(180%)",
        border: "1px solid hsl(0 0% 100% / 0.20)",
        borderRadius: 16,
        boxShadow: ["0 8px 32px hsl(0 0% 0% / 0.28)", "inset 0 1px 0 hsl(0 0% 100% / 0.15)"].join(
          ", "
        ),
        color: "hsl(0 0% 95%)",
        fontFamily: "system-ui, sans-serif",
        fontSize: 13,
        maxHeight: 420,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 14px 8px",
          borderBottom: "1px solid hsl(0 0% 100% / 0.10)",
          fontWeight: 600,
          fontSize: 12,
          color: "hsl(38 95% 72%)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        <span>File Placement Suggestions</span>
        <button
          onClick={handleDismiss}
          style={{
            background: "none",
            border: "none",
            color: "hsl(0 0% 60%)",
            cursor: "pointer",
            fontSize: 16,
            lineHeight: 1,
            padding: "0 2px",
          }}
          aria-label="Close suggestions"
        >
          ×
        </button>
      </div>

      {/* List */}
      <div style={{ overflowY: "auto", flex: 1 }}>
        {loading && <div style={{ padding: "16px 14px", color: "hsl(0 0% 60%)" }}>Loading…</div>}

        {!loading && recommendations.length === 0 && (
          <div style={{ padding: "16px 14px", color: "hsl(0 0% 60%)" }}>
            No pending suggestions.
          </div>
        )}

        <AnimatePresence>
          {recommendations.map((rec) => {
            const top = rec.candidates[0];
            const fileName = rec.source_path.split(/[\\/]/).pop() ?? rec.source_path;
            return (
              <motion.div
                key={rec.id}
                initial={{ opacity: 1 }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.18 }}
                style={{
                  padding: "10px 14px",
                  borderBottom: "1px solid hsl(0 0% 100% / 0.06)",
                }}
              >
                <div
                  style={{
                    fontWeight: 500,
                    marginBottom: 4,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                  title={rec.source_path}
                >
                  {fileName}
                </div>

                {top && (
                  <div style={{ fontSize: 12, color: "hsl(0 0% 72%)", marginBottom: 8 }}>
                    <span style={{ color: labelColor(top.label), fontWeight: 600 }}>
                      {top.label}
                    </span>
                    {" · "}
                    <span
                      style={{
                        fontFamily: "monospace",
                        fontSize: 11,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        display: "inline-block",
                        maxWidth: 220,
                        verticalAlign: "bottom",
                      }}
                      title={top.folder}
                    >
                      {top.folder}
                    </span>
                  </div>
                )}

                <div style={{ display: "flex", gap: 8 }}>
                  {top && (
                    <button
                      onClick={() => handleAccept(rec.id, top.folder)}
                      style={{
                        padding: "4px 12px",
                        borderRadius: 7,
                        border: "none",
                        background: "hsl(142 60% 42%)",
                        color: "hsl(0 0% 98%)",
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Move here
                    </button>
                  )}
                  <button
                    onClick={() => handleSkip(rec.id)}
                    style={{
                      padding: "4px 10px",
                      borderRadius: 7,
                      border: "1px solid hsl(0 0% 100% / 0.15)",
                      background: "hsl(0 0% 100% / 0.07)",
                      color: "hsl(0 0% 72%)",
                      fontSize: 12,
                      cursor: "pointer",
                    }}
                  >
                    Skip
                  </button>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
