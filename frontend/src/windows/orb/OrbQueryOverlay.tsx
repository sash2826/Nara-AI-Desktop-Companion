import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { invoke } from "@tauri-apps/api/core";
import { useOrbWindowStore } from "./orbWindowStore";

interface QueryState {
  status: "idle" | "submitting" | "answered" | "error";
  response: string;
  errorMessage: string;
}

const OVERLAY_WIDTH = 340;

/**
 * Inline query overlay that grows out of the orb on single-click.
 *
 * Provides a text input, submits a query via the main window's backend,
 * renders the response inline (max ~5 lines before scroll), and offers
 * an "Open in EAC" button to escalate to the full window.
 *
 * Dismissed on Escape or after the user acknowledges the response.
 */
export function OrbQueryOverlay() {
  const { setOverlayMode, setAnimationState } = useOrbWindowStore();
  const [query, setQuery] = useState("");
  const [queryState, setQueryState] = useState<QueryState>({
    status: "idle",
    errorMessage: "",
    response: "",
  });
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleDismiss = useCallback(() => {
    setOverlayMode("none");
    setQuery("");
    setQueryState({ status: "idle", response: "", errorMessage: "" });
  }, [setOverlayMode]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleDismiss();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [handleDismiss]);

  const handleSubmit = useCallback(async () => {
    const trimmed = query.trim();
    if (!trimmed || queryState.status === "submitting") return;

    setQueryState({ status: "submitting", response: "", errorMessage: "" });
    setAnimationState("processing");

    try {
      // Ask the Tauri backend to run the query via the Python sidecar
      const response = await invoke<string>("orb_query", { query: trimmed });
      setQueryState({ status: "answered", response, errorMessage: "" });
      setAnimationState("idle");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setQueryState({ status: "error", response: "", errorMessage: msg });
      setAnimationState("error");
    }
  }, [query, queryState.status, setAnimationState]);

  const handleOpenInEAC = useCallback(async () => {
    try {
      await invoke("focus_main_window");
    } catch {
      // Main window may already be focused — ignore
    }
    handleDismiss();
  }, [handleDismiss]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.95 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      style={{
        position: "absolute",
        bottom: "calc(100% + 10px)",
        right: 0,
        width: OVERLAY_WIDTH,
        zIndex: 100,
        // Liquid Glass styling
        background: "hsl(0 0% 100% / 0.12)",
        backdropFilter: "blur(20px) saturate(180%)",
        WebkitBackdropFilter: "blur(20px) saturate(180%)",
        border: "1px solid hsl(0 0% 100% / 0.20)",
        borderRadius: 16,
        boxShadow: ["0 8px 32px hsl(0 0% 0% / 0.28)", "inset 0 1px 0 hsl(0 0% 100% / 0.15)"].join(
          ", "
        ),
        padding: "12px 14px",
        color: "hsl(0 0% 95%)",
        fontFamily: "system-ui, sans-serif",
        fontSize: 13,
      }}
    >
      {/* Input row */}
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSubmit();
          }}
          placeholder="Ask anything…"
          disabled={queryState.status === "submitting"}
          style={{
            flex: 1,
            background: "hsl(0 0% 100% / 0.08)",
            border: "1px solid hsl(0 0% 100% / 0.15)",
            borderRadius: 8,
            padding: "6px 10px",
            color: "inherit",
            fontSize: "inherit",
            outline: "none",
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || queryState.status === "submitting"}
          style={{
            padding: "6px 12px",
            borderRadius: 8,
            border: "none",
            background:
              !query.trim() || queryState.status === "submitting"
                ? "hsl(0 0% 100% / 0.10)"
                : "hsl(var(--color-primary-500))",
            color: "hsl(0 0% 95%)",
            cursor: !query.trim() || queryState.status === "submitting" ? "default" : "pointer",
            fontSize: 12,
            fontWeight: 600,
            transition: "background 0.2s",
          }}
        >
          {queryState.status === "submitting" ? "…" : "Ask"}
        </button>
      </div>

      {/* Response area */}
      <AnimatePresence>
        {(queryState.status === "answered" || queryState.status === "error") && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            style={{ marginTop: 10, overflow: "hidden" }}
          >
            <div
              style={{
                maxHeight: 120,
                overflowY: "auto",
                lineHeight: 1.55,
                color: queryState.status === "error" ? "hsl(0 72% 75%)" : "hsl(0 0% 92%)",
                padding: "6px 2px",
                borderTop: "1px solid hsl(0 0% 100% / 0.10)",
              }}
            >
              {queryState.status === "error"
                ? `Error: ${queryState.errorMessage}`
                : queryState.response}
            </div>

            {/* Action row */}
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: 8,
                marginTop: 8,
              }}
            >
              <button
                onClick={handleOpenInEAC}
                style={{
                  padding: "4px 10px",
                  borderRadius: 7,
                  border: "1px solid hsl(0 0% 100% / 0.18)",
                  background: "hsl(0 0% 100% / 0.08)",
                  color: "hsl(0 0% 92%)",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Open in EAC
              </button>
              <button
                onClick={handleDismiss}
                style={{
                  padding: "4px 10px",
                  borderRadius: 7,
                  border: "none",
                  background: "hsl(0 0% 100% / 0.12)",
                  color: "hsl(0 0% 80%)",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Dismiss
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
