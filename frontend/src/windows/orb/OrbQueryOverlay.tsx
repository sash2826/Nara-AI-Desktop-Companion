import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowUp } from "lucide-react";
import { invoke } from "@tauri-apps/api/core";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { useOrbWindowStore } from "./orbWindowStore";
import { Folder } from "lucide-react";
import { CitationChip } from "@/components/assistant/CitationChip";
import type { CitationMeta } from "@/types/conversation";

interface SourceItem {
  path: string;
  name: string;
}

function toCitationMeta(source: SourceItem, index: number): CitationMeta {
  return {
    chunkId: `orb-source-${index}`,
    documentPath: source.path,
    chunkIndex: index - 1,
    rrfScore: 0,
  };
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

// ---------------------------------------------------------------------------
// Inline citation badge — mirrors the one in MessageBubble.tsx
// ---------------------------------------------------------------------------

function OrbCitationBadge({ index, source }: { index: number; source: SourceItem }) {
  const [hovered, setHovered] = useState(false);
  const segments = source.path.replace(/\\/g, "/").split("/").filter(Boolean);
  const parent = segments.at(-2) ?? null;

  return (
    <sup
      style={{
        position: "relative",
        display: "inline-flex",
        verticalAlign: "super",
        margin: "0 1px",
      }}
    >
      <button
        onClick={() => invoke("open_file", { path: source.path }).catch(() => {})}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          fontSize: 9,
          fontWeight: 700,
          color: "hsl(var(--primary))",
          background: "none",
          border: "none",
          padding: 0,
          cursor: "pointer",
          fontFamily: "inherit",
        }}
        aria-label={`Source ${index}: ${source.name}`}
      >
        {index}
      </button>
      {hovered && (
        <div
          style={{
            pointerEvents: "none",
            position: "absolute",
            bottom: "100%",
            left: 0,
            zIndex: 200,
            marginBottom: 6,
            width: 180,
            borderRadius: 8,
            border: "1px solid hsl(var(--border))",
            background: "hsl(var(--popover))",
            padding: "6px 8px",
            boxShadow: "0 4px 16px hsl(0 0% 0% / 0.25)",
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 10,
              fontFamily: "monospace",
              wordBreak: "break-all",
              color: "hsl(var(--foreground))",
            }}
          >
            {parent ? `${parent} / ${source.name}` : source.name}
          </p>
        </div>
      )}
    </sup>
  );
}

// Replaces [N] tokens in a text string with OrbCitationBadge elements.
const CITATION_RE = /(?:\[\d+\])+/g;

function processOrbText(text: string, citationMap: Map<number, SourceItem>): React.ReactNode[] {
  if (citationMap.size === 0) return [text];
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  CITATION_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = CITATION_RE.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    const numRe = /\[(\d+)\]/g;
    let nm: RegExpExecArray | null;
    let rendered = false;
    while ((nm = numRe.exec(match[0])) !== null) {
      const n = parseInt(nm[1], 10);
      const src = citationMap.get(n);
      if (src) {
        parts.push(<OrbCitationBadge key={`${match.index}-${n}`} index={n} source={src} />);
        rendered = true;
      } else {
        parts.push(`[${n}]`);
      }
    }
    if (!rendered) parts.push(match[0]);
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

function walkOrbChildren(
  children: React.ReactNode,
  citationMap: Map<number, SourceItem>
): React.ReactNode {
  if (typeof children === "string") return processOrbText(children, citationMap);
  if (Array.isArray(children)) {
    return children.flatMap((child, i) => {
      if (typeof child === "string") {
        return processOrbText(child, citationMap).map((node, j) => (
          <span key={`${i}-${j}`}>{node}</span>
        ));
      }
      return [child];
    });
  }
  return children;
}

// ---------------------------------------------------------------------------
// Markdown components — inline-styled for the orb's glass window context
// ---------------------------------------------------------------------------

function buildOrbMarkdownComponents(citationMap: Map<number, SourceItem>): Components {
  return {
    p({ children }) {
      return (
        <p style={{ margin: "0 0 6px", lineHeight: 1.65, fontSize: 12 }}>
          {walkOrbChildren(children, citationMap)}
        </p>
      );
    },
    ul({ children }) {
      return <ul style={{ margin: "0 0 6px", paddingLeft: 15, fontSize: 12 }}>{children}</ul>;
    },
    ol({ children }) {
      return <ol style={{ margin: "0 0 6px", paddingLeft: 15, fontSize: 12 }}>{children}</ol>;
    },
    li({ children }) {
      return (
        <li style={{ lineHeight: 1.65, marginBottom: 3 }}>
          {walkOrbChildren(children, citationMap)}
        </li>
      );
    },
    strong({ children }) {
      return <strong style={{ fontWeight: 600 }}>{children}</strong>;
    },
    em({ children }) {
      return <em style={{ fontStyle: "italic" }}>{children}</em>;
    },
    h1({ children }) {
      return <h1 style={{ fontSize: 13, fontWeight: 700, margin: "0 0 6px" }}>{children}</h1>;
    },
    h2({ children }) {
      return <h2 style={{ fontSize: 12, fontWeight: 600, margin: "0 0 4px" }}>{children}</h2>;
    },
    h3({ children }) {
      return <h3 style={{ fontSize: 12, fontWeight: 600, margin: "0 0 4px" }}>{children}</h3>;
    },
    code({ className, children }) {
      const isBlock = !!className;
      if (isBlock) {
        return (
          <pre
            style={{
              background: "hsl(var(--muted) / 0.5)",
              border: "1px solid hsl(var(--border))",
              borderRadius: 6,
              padding: "6px 8px",
              fontSize: 11,
              overflowX: "auto",
              margin: "0 0 6px",
              fontFamily: "monospace",
            }}
          >
            <code>{children}</code>
          </pre>
        );
      }
      return (
        <code
          style={{
            background: "hsl(var(--muted) / 0.5)",
            borderRadius: 3,
            padding: "1px 4px",
            fontSize: 11,
            fontFamily: "monospace",
          }}
        >
          {children}
        </code>
      );
    },
    blockquote({ children }) {
      return (
        <blockquote
          style={{
            borderLeft: "2px solid hsl(var(--primary) / 0.5)",
            paddingLeft: 8,
            margin: "0 0 6px",
            color: "hsl(var(--muted-foreground))",
            fontSize: 12,
          }}
        >
          {children}
        </blockquote>
      );
    },
  };
}

/**
 * Inline query overlay that grows out of the orb on single-click.
 *
 * Provides a text input, submits a query via the main window's backend,
 * renders the response inline (max ~5 lines before scroll), and offers
 * an "Open in Chat" button to escalate to the full window.
 *
 * Dismissed on Escape or after the user acknowledges the response.
 */
export function OrbQueryOverlay() {
  const { setOverlayMode, setAnimationState, pendingCount, markNotificationsViewed } =
    useOrbWindowStore();
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

  const handleOpenInChat = useCallback(async () => {
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
  }, [queryState.submittedQuery, queryState.response, queryState.sources, handleDismiss]);

  // Build 1-based citation map from sources so [N] in response text maps to sources[N-1].
  const citationMap = useMemo(() => {
    const map = new Map<number, SourceItem>();
    queryState.sources.forEach((src, i) => map.set(i + 1, src));
    return map;
  }, [queryState.sources]);

  // Track which [N] indices actually appear in the response to filter Related docs.
  const referencedIndices = useMemo(() => {
    const set = new Set<number>();
    const re = /\[(\d+)\]/g;
    let m: RegExpExecArray | null;
    while ((m = re.exec(queryState.response)) !== null) set.add(parseInt(m[1], 10));
    return set;
  }, [queryState.response]);

  // Deduplicate citations by path, keeping only those actually referenced inline.
  const citedSources = useMemo(() => {
    const seen = new Map<string, { index: number; source: SourceItem }>();
    queryState.sources.forEach((src, i) => {
      const idx = i + 1;
      if (!referencedIndices.has(idx)) return;
      if (!seen.has(src.path)) seen.set(src.path, { index: idx, source: src });
    });
    return Array.from(seen.values());
  }, [queryState.sources, referencedIndices]);

  // All sources shown in Related docs when none are cited inline (non-RAG responses).
  const relatedSources = useMemo(() => {
    if (citedSources.length > 0) return citedSources;
    return queryState.sources.map((src, i) => ({ index: i + 1, source: src }));
  }, [citedSources, queryState.sources]);

  const markdownComponents = useMemo(() => buildOrbMarkdownComponents(citationMap), [citationMap]);

  const isSubmitting = queryState.status === "submitting";
  const hasResult = queryState.status === "answered" || queryState.status === "error";

  return (
    <motion.div
      data-orb-surface
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
        // Anchored at the bottom near the orb; grows upward with content, then
        // the inner scroll area caps it so it never exceeds the orb window.
        maxHeight: "calc(100vh - 96px)",
        display: "flex",
        flexDirection: "column",
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
      {/* Scrollable content — the answer stacks on top and grows in height,
          then this area scrolls. The input pill stays pinned at the bottom. */}
      <div
        style={{
          flex: "1 1 auto",
          minHeight: 0,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
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

        {/* Animated thinking state */}
        <AnimatePresence>
          {isSubmitting && (
            <motion.div
              key="thinking"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              style={{ overflow: "hidden" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 6, paddingBottom: 4 }}>
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
              style={{ overflow: "hidden" }}
            >
              <div
                style={{
                  color:
                    queryState.status === "error"
                      ? "hsl(var(--destructive))"
                      : "hsl(var(--popover-foreground))",
                  padding: "2px 2px",
                }}
              >
                {queryState.status === "error" ? (
                  <span style={{ fontSize: 12, lineHeight: 1.6 }}>
                    Error: {queryState.errorMessage}
                  </span>
                ) : (
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {queryState.response}
                  </ReactMarkdown>
                )}
              </div>

              {/* Related documents — shared source treatment with the main chat. */}
              {relatedSources.length > 0 && (
                <div
                  style={{
                    marginTop: 6,
                    borderRadius: 10,
                    border: "1px solid hsl(var(--border) / 0.5)",
                    background: "hsl(var(--muted) / 0.3)",
                    padding: "6px 8px",
                  }}
                >
                  <p
                    style={{
                      margin: "0 0 4px",
                      fontSize: 10,
                      fontWeight: 500,
                      color: "hsl(var(--muted-foreground))",
                      opacity: 0.7,
                    }}
                  >
                    Related documents
                  </p>
                  <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                    {relatedSources.map(({ index, source }) => (
                      <div
                        key={source.path}
                        style={{ display: "flex", alignItems: "center", gap: 6 }}
                      >
                        <span
                          style={{
                            width: 18,
                            textAlign: "right",
                            fontSize: 10,
                            color: "hsl(var(--muted-foreground))",
                            opacity: 0.5,
                            flexShrink: 0,
                          }}
                        >
                          [{index}]
                        </span>
                        <CitationChip citation={toCitationMeta(source, index)} index={index} />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action row */}
              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
                {queryState.status === "answered" && (
                  <button
                    onClick={handleOpenInChat}
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
                    Open in Chat
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
      </div>

      {/* Pending suggestions chip — always visible when suggestions exist */}
      {pendingCount > 0 && (
        <button
          onClick={() => {
            markNotificationsViewed();
            setOverlayMode("notifications");
          }}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            width: "100%",
            marginTop: 8,
            padding: "6px 10px",
            borderRadius: 8,
            border: "1px solid hsl(38 95% 55% / 0.4)",
            background: "hsl(38 95% 55% / 0.1)",
            color: "hsl(38 80% 45%)",
            fontSize: 12,
            cursor: "pointer",
            textAlign: "left",
            fontFamily: "inherit",
            flexShrink: 0,
          }}
        >
          <Folder size={13} strokeWidth={2} style={{ flexShrink: 0 }} />
          <span style={{ flex: 1 }}>
            {pendingCount} file suggestion{pendingCount !== 1 ? "s" : ""} pending
          </span>
          <span style={{ opacity: 0.7, fontSize: 11 }}>View →</span>
        </button>
      )}

      {/* Input row (pill) — pinned at the bottom, chat-style */}
      <div
        style={{
          display: "flex",
          gap: 6,
          alignItems: "center",
          marginTop: 8,
          flexShrink: 0,
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
    </motion.div>
  );
}
