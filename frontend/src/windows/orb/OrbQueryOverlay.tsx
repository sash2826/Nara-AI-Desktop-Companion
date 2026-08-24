import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowUp } from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import { useOrbWindowStore } from "./orbWindowStore";

interface SourceItem {
  path: string;
  name: string;
}

interface QueryState {
  status: "idle" | "submitting" | "answered" | "error";
  submittedQuery: string;
  response: string;
  sources: SourceItem[];
  errorMessage: string;
  thinkingPhase: number;
}

const THINKING_PHRASES = [
  "Thinking",
  "Searching your knowledge base",
  "Reading through files",
  "Combining results",
  "Almost there",
];

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
    submittedQuery: "",
    errorMessage: "",
    response: "",
    sources: [],
    thinkingPhase: 0,
  });
  const inputRef = useRef<HTMLInputElement>(null);
  const thinkingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Advance thinking phrase every 1.8s while submitting
  useEffect(() => {
    if (queryState.status === "submitting") {
      thinkingTimerRef.current = setInterval(() => {
        setQueryState((prev) => ({
          ...prev,
          thinkingPhase: (prev.thinkingPhase + 1) % THINKING_PHRASES.length,
        }));
      }, 1800);
    } else {
      if (thinkingTimerRef.current) {
        clearInterval(thinkingTimerRef.current);
        thinkingTimerRef.current = null;
      }
    }
    return () => {
      if (thinkingTimerRef.current) clearInterval(thinkingTimerRef.current);
    };
  }, [queryState.status]);

  const handleDismiss = useCallback(() => {
    setOverlayMode("none");
    setQuery("");
    setQueryState({
      status: "idle",
      submittedQuery: "",
      response: "",
      sources: [],
      errorMessage: "",
      thinkingPhase: 0,
    });
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

    // Clear input immediately and capture query text (Claude-style)
    const capturedQuery = trimmed;
    setQuery("");
    setQueryState({
      status: "submitting",
      submittedQuery: capturedQuery,
      response: "",
      sources: [],
      errorMessage: "",
      thinkingPhase: 0,
    });
    setAnimationState("processing");

    try {
      const result = await invoke<{ response: string; sources: SourceItem[] }>("orb_query", {
        query: capturedQuery,
      });
      setQueryState((prev) => ({
        ...prev,
        status: "answered",
        response: result.response,
        sources: result.sources ?? [],
      }));
      setAnimationState("idle");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setQueryState((prev) => ({
        ...prev,
        status: "error",
        errorMessage: msg,
      }));
      setAnimationState("error");
    }
  }, [query, queryState.status, setAnimationState]);

  const handleOpenInEAC = useCallback(async () => {
    // Route via Rust so the event is guaranteed to arrive in the main webview.
    // Direct frontend emitTo is unreliable across separate Tauri webview windows.
    try {
      await invoke("relay_orb_handoff", {
        query: queryState.submittedQuery,
        response: queryState.response,
        sources: queryState.sources,
      });
    } catch {
      // Best-effort — main window listener handles missing events gracefully
    }
    try {
      await invoke("focus_main_window");
    } catch {
      // Main window may already be focused — ignore
    }
    handleDismiss();
  }, [queryState.submittedQuery, queryState.response, handleDismiss]);

  const isSubmitting = queryState.status === "submitting";
  const hasResult = queryState.status === "answered" || queryState.status === "error";

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
        background: "hsl(var(--popover) / 0.94)",
        backdropFilter: "blur(20px) saturate(180%)",
        WebkitBackdropFilter: "blur(20px) saturate(180%)",
        border: "1px solid hsl(var(--border) / 0.7)",
        borderRadius: 16,
        boxShadow: ["0 8px 32px hsl(0 0% 0% / 0.28)", "inset 0 1px 0 hsl(0 0% 100% / 0.08)"].join(
          ", "
        ),
        padding: "12px 14px",
        color: "hsl(var(--popover-foreground))",
        fontFamily: "var(--font-sans), system-ui, sans-serif",
        fontSize: 13,
      }}
    >
      {/* Submitted query echo — appears after input clears */}
      <AnimatePresence>
        {queryState.submittedQuery && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            style={{
              marginBottom: 8,
              fontSize: 12,
              color: "hsl(var(--muted-foreground))",
              fontStyle: "italic",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {queryState.submittedQuery}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input row */}
      <div
        style={{
          display: "flex",
          gap: 6,
          alignItems: "center",
          padding: "5px 6px 5px 10px",
          background: "hsl(var(--muted) / 0.4)",
          backdropFilter: "blur(12px) saturate(180%)",
          WebkitBackdropFilter: "blur(12px) saturate(180%)",
          border: "1px solid hsl(var(--border))",
          borderRadius: "1.75rem",
          boxShadow: "inset 0 1px 0 hsl(0 0% 100% / 0.1), 0 2px 10px hsl(0 0% 0% / 0.12)",
        }}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSubmit();
          }}
          placeholder={isSubmitting ? "" : "Ask anything…"}
          disabled={isSubmitting}
          style={{
            flex: 1,
            minWidth: 0,
            background: "transparent",
            border: "none",
            padding: "7px 4px",
            color: "inherit",
            fontSize: "inherit",
            outline: "none",
          }}
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!query.trim() || isSubmitting}
          aria-label="Send query"
          title="Send query"
          style={{
            width: 32,
            height: 32,
            display: "flex",
            flexShrink: 0,
            alignItems: "center",
            justifyContent: "center",
            padding: 0,
            borderRadius: "50%",
            border: "none",
            background: !query.trim() || isSubmitting ? "hsl(var(--muted))" : "hsl(var(--primary))",
            color:
              !query.trim() || isSubmitting
                ? "hsl(var(--muted-foreground))"
                : "hsl(var(--primary-foreground))",
            cursor: !query.trim() || isSubmitting ? "default" : "pointer",
            transition: "background 0.2s",
          }}
        >
          <ArrowUp size={15} strokeWidth={2.2} aria-hidden="true" />
        </button>
      </div>

      {/* Animated thinking state */}
      <AnimatePresence>
        {isSubmitting && (
          <motion.div
            key="thinking"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            style={{ marginTop: 10, overflow: "hidden" }}
          >
            <div
              style={{
                paddingTop: 6,
                borderTop: "1px solid hsl(var(--border))",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              {/* Three pulsing dots */}
              <span style={{ display: "inline-flex", gap: 3, alignItems: "center" }}>
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{
                      duration: 1.2,
                      repeat: Infinity,
                      delay: i * 0.2,
                      ease: "easeInOut",
                    }}
                    style={{
                      display: "block",
                      width: 4,
                      height: 4,
                      borderRadius: "50%",
                      background: "hsl(var(--primary))",
                    }}
                  />
                ))}
              </span>
              {/* Cycling phrase */}
              <AnimatePresence mode="wait">
                <motion.span
                  key={queryState.thinkingPhase}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.25, ease: "easeOut" }}
                  style={{ fontSize: 12, color: "hsl(var(--primary))", fontStyle: "italic" }}
                >
                  {THINKING_PHRASES[queryState.thinkingPhase]}…
                </motion.span>
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Response area */}
      <AnimatePresence>
        {hasResult && (
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
                color:
                  queryState.status === "error"
                    ? "hsl(var(--destructive))"
                    : "hsl(var(--popover-foreground))",
                padding: "6px 2px",
                borderTop: "1px solid hsl(var(--border))",
              }}
            >
              {queryState.status === "error"
                ? `Error: ${queryState.errorMessage}`
                : queryState.response}
            </div>

            {/* Source file chips */}
            {queryState.sources.length > 0 && (
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 4,
                  marginTop: 8,
                  paddingTop: 6,
                  borderTop: "1px solid hsl(var(--border))",
                }}
              >
                {queryState.sources.map((src) => (
                  <button
                    key={src.path}
                    onClick={() => invoke("open_file", { path: src.path }).catch(() => {})}
                    title={src.path}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      padding: "3px 8px",
                      borderRadius: 6,
                      border: "1px solid hsl(var(--border))",
                      background: "hsl(var(--muted) / 0.6)",
                      color: "hsl(var(--primary))",
                      fontSize: 11,
                      cursor: "pointer",
                      maxWidth: 160,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    <span style={{ opacity: 0.7 }}>📄</span>
                    <span
                      style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                    >
                      {src.name}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {/* Action row */}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
              {queryState.status === "answered" && (
                <button
                  onClick={handleOpenInEAC}
                  style={{
                    padding: "4px 10px",
                    borderRadius: 7,
                    border: "1px solid hsl(var(--border))",
                    background: "hsl(var(--muted) / 0.6)",
                    color: "hsl(var(--popover-foreground))",
                    fontSize: 12,
                    cursor: "pointer",
                  }}
                >
                  Open in EAC
                </button>
              )}
              <button
                onClick={handleDismiss}
                style={{
                  padding: "4px 10px",
                  borderRadius: 7,
                  border: "none",
                  background: "hsl(var(--muted) / 0.8)",
                  color: "hsl(var(--muted-foreground))",
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
