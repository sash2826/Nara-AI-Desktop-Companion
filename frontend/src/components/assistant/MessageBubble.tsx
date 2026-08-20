import { useMemo, useState, useCallback } from "react";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { Square, FileText, Cloud } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { CopyButton } from "@/components/common/CopyButton";
import { isAbsolutePath } from "./filePathUtils";
import { FilePathChip } from "./FilePathChip";
import { CitationChip } from "./CitationChip";
import { IPCClient } from "@/services/ipc/IPCClient";
import { cn } from "@/lib/utils";
import type { Message, CitationMeta } from "@/types/conversation";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

// ---------------------------------------------------------------------------
// Inline citation badge — renders [N] references as a small clickable icon
// ---------------------------------------------------------------------------

function InlineCitationBadge({ index, citation }: { index: number; citation: CitationMeta }) {
  const [hovered, setHovered] = useState(false);

  const normalised = citation.documentPath.replace(/\\/g, "/");
  const segments = normalised.split("/").filter(Boolean);
  const filename = segments.at(-1) ?? citation.documentPath;
  const parentFolder = segments.at(-2) ?? null;
  const isOneDrive = /\/OneDrive[^/]*/i.test(normalised);

  const handleOpen = useCallback(async () => {
    if (!IS_TAURI) return;
    try {
      await IPCClient.openFile(citation.documentPath);
    } catch {
      // ignore — file may not be locally available
    }
  }, [citation.documentPath]);

  return (
    <span className="relative inline-flex align-baseline">
      <button
        onClick={handleOpen}
        disabled={!IS_TAURI}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        onFocus={() => setHovered(true)}
        onBlur={() => setHovered(false)}
        aria-label={`Source ${index}: ${filename}`}
        className="mx-0.5 inline-flex items-center gap-0.5 rounded border border-border bg-muted px-1 py-0.5 text-2xs text-muted-foreground transition-colors hover:border-primary/40 hover:bg-primary/5 hover:text-primary disabled:pointer-events-none"
      >
        {isOneDrive ? (
          <Cloud size={8} strokeWidth={1.5} className="flex-shrink-0" />
        ) : (
          <FileText size={8} strokeWidth={1.5} className="flex-shrink-0" />
        )}
        <span>{index}</span>
      </button>

      {hovered && (
        <div className="pointer-events-none absolute bottom-full left-0 z-50 mb-1.5 w-56 rounded-lg border border-border bg-popover px-2.5 py-1.5 shadow-md">
          <p className="break-all font-mono text-2xs text-foreground">
            {parentFolder ? `${parentFolder} / ${filename}` : filename}
          </p>
        </div>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Citation text processing — replaces [N] tokens with InlineCitationBadge
// ---------------------------------------------------------------------------

// Matches one or more consecutive [N] references, e.g. "[3]" or "[3][4]"
const INLINE_CITATION_RE = /(?:\[\d+\])+/g;

function processTextWithCitations(
  text: string,
  citationMap: Map<number, CitationMeta>
): ReactNode[] {
  if (citationMap.size === 0) return [text];

  const parts: ReactNode[] = [];
  let lastIndex = 0;
  INLINE_CITATION_RE.lastIndex = 0;

  let match: RegExpExecArray | null;
  while ((match = INLINE_CITATION_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    // Parse individual [N] tokens within the matched run (e.g. [3][4])
    const numRe = /\[(\d+)\]/g;
    let nm: RegExpExecArray | null;
    let renderedAny = false;
    while ((nm = numRe.exec(match[0])) !== null) {
      const num = parseInt(nm[1], 10);
      const citation = citationMap.get(num);
      if (citation) {
        parts.push(
          <InlineCitationBadge key={`${match.index}-${num}`} index={num} citation={citation} />
        );
        renderedAny = true;
      } else {
        parts.push(`[${num}]`);
      }
    }
    if (!renderedAny) parts.push(match[0]);

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

function walkChildrenWithCitations(
  children: ReactNode,
  citationMap: Map<number, CitationMeta>
): ReactNode {
  if (typeof children === "string") {
    return processTextWithCitations(children, citationMap);
  }
  if (Array.isArray(children)) {
    return children.flatMap((child, i) => {
      if (typeof child === "string") {
        return processTextWithCitations(child, citationMap).map((node, j) => (
          <span key={`${i}-${j}`}>{node}</span>
        ));
      }
      return [child];
    });
  }
  return children;
}

// ---------------------------------------------------------------------------
// Markdown component factory — injects citation map into text renderers
// ---------------------------------------------------------------------------

function buildMarkdownComponents(citationMap: Map<number, CitationMeta>): Components {
  return {
    code({ className, children, ...props }) {
      const isInline = !className;
      const language = className?.replace("language-", "") ?? "";
      const code = String(children).replace(/\n$/, "");

      if (isInline) {
        if (isAbsolutePath(code)) return <FilePathChip path={code} />;
        return (
          <code
            className="rounded-sm bg-muted px-1 py-0.5 font-mono text-xs text-foreground"
            {...props}
          >
            {children}
          </code>
        );
      }

      return (
        <div className="group relative my-2 overflow-hidden rounded-lg border border-border bg-muted">
          {language && (
            <div className="flex items-center justify-between border-b border-border px-3 py-1.5">
              <span className="font-mono text-2xs text-muted-foreground">{language}</span>
              <CopyButton text={code} />
            </div>
          )}
          {!language && (
            <div className="absolute right-2 top-2 opacity-0 transition-opacity duration-fast group-hover:opacity-100">
              <CopyButton text={code} />
            </div>
          )}
          <pre className="overflow-x-auto p-3 text-xs">
            <code className="font-mono text-foreground">{children}</code>
          </pre>
        </div>
      );
    },

    table({ children }) {
      return (
        <div className="my-2 overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">{children}</table>
        </div>
      );
    },

    th({ children }) {
      return (
        <th className="border-b border-border bg-muted px-3 py-2 text-left text-xs font-semibold text-foreground">
          {children}
        </th>
      );
    },

    td({ children }) {
      return (
        <td className="border-b border-border px-3 py-2 text-xs text-foreground">{children}</td>
      );
    },

    blockquote({ children }) {
      return (
        <blockquote className="my-2 border-l-2 border-primary pl-3 text-muted-foreground">
          {children}
        </blockquote>
      );
    },

    p({ children }) {
      return (
        <p className="mb-2 last:mb-0 text-sm leading-relaxed">
          {walkChildrenWithCitations(children, citationMap)}
        </p>
      );
    },

    ul({ children }) {
      return <ul className="mb-2 ml-4 list-disc space-y-1 text-sm">{children}</ul>;
    },

    ol({ children }) {
      return <ol className="mb-2 ml-4 list-decimal space-y-1 text-sm">{children}</ol>;
    },

    li({ children }) {
      return (
        <li className="leading-relaxed">{walkChildrenWithCitations(children, citationMap)}</li>
      );
    },

    h1({ children }) {
      return <h1 className="mb-2 text-lg font-bold text-foreground">{children}</h1>;
    },

    h2({ children }) {
      return <h2 className="mb-2 text-base font-semibold text-foreground">{children}</h2>;
    },

    h3({ children }) {
      return <h3 className="mb-1.5 text-sm font-semibold text-foreground">{children}</h3>;
    },

    strong({ children }) {
      return <strong className="font-semibold text-foreground">{children}</strong>;
    },
  };
}

// ---------------------------------------------------------------------------
// Bubble components
// ---------------------------------------------------------------------------

interface MessageBubbleProps {
  message: Message;
}

function UserBubble({ message }: { message: Message }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex justify-end px-4 py-1"
    >
      <div className="group flex max-w-[80%] flex-col items-end gap-1">
        <div className="rounded-2xl rounded-br-sm bg-primary px-3.5 py-2.5 text-sm text-primary-foreground">
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        </div>
        <div className="flex items-center gap-2 opacity-0 transition-opacity duration-fast group-hover:opacity-100">
          <CopyButton text={message.content} />
          <span className="text-2xs text-muted-foreground">{formatTime(message.timestamp)}</span>
        </div>
      </div>
    </motion.div>
  );
}

function AssistantBubble({ message }: { message: Message }) {
  const isStreaming = message.status === "streaming";
  const isCancelled = message.status === "cancelled";

  // citationMap preserves the original 1-based chunk index the LLM used —
  // [N] in the response text maps directly to message.citations[N-1].
  const citationMap = useMemo(() => {
    const map = new Map<number, CitationMeta>();
    (message.citations ?? []).forEach((c, i) => map.set(i + 1, c));
    return map;
  }, [message.citations]);

  // Deduplicate by file path for the "Related documents" list; keep first
  // occurrence so the displayed index matches the lowest inline [N] reference.
  const uniqueCitations = useMemo(() => {
    const seen = new Map<string, { index: number; citation: CitationMeta }>();
    (message.citations ?? []).forEach((c, i) => {
      if (!seen.has(c.documentPath)) seen.set(c.documentPath, { index: i + 1, citation: c });
    });
    return Array.from(seen.values());
  }, [message.citations]);

  const markdownComponents = useMemo(() => buildMarkdownComponents(citationMap), [citationMap]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="group px-4 py-3"
    >
      <div className="flex min-w-0 flex-col gap-1">
        <div className={cn("min-w-0 prose prose-sm max-w-none")}>
          {message.content ? (
            <>
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {message.content}
              </ReactMarkdown>
              {isStreaming && (
                <span className="ml-0.5 inline-flex items-center align-middle">
                  <motion.span
                    className="inline-block h-4 w-0.5 rounded-full bg-foreground"
                    animate={{ opacity: [1, 0] }}
                    transition={{ duration: 0.55, repeat: Infinity, ease: "easeInOut" }}
                    aria-hidden="true"
                  />
                </span>
              )}
              {isCancelled && (
                <span className="ml-1 inline-flex items-center gap-1 rounded-sm bg-muted px-1.5 py-0.5 align-middle text-2xs text-muted-foreground">
                  <Square size={9} fill="currentColor" />
                  stopped
                </span>
              )}
            </>
          ) : null}
        </div>

        {/* Related documents — numbered list matching inline [N] badges */}
        {!isStreaming && uniqueCitations.length > 0 && (
          <div className="rounded-xl border border-border/50 bg-muted/40 px-3 py-2">
            <p className="mb-1.5 text-2xs font-medium text-muted-foreground/70">
              Related documents
            </p>
            <div className="flex flex-col gap-1">
              {uniqueCitations.map(({ index, citation }) => (
                <div key={citation.documentPath} className="flex items-center gap-2">
                  <span className="w-5 shrink-0 text-right text-2xs text-muted-foreground/50">
                    [{index}]
                  </span>
                  <CitationChip citation={citation} index={index} />
                </div>
              ))}
            </div>
          </div>
        )}

        {!isStreaming && message.content && (
          <div className="flex items-center gap-2 opacity-0 transition-opacity duration-fast group-hover:opacity-100">
            <CopyButton text={message.content} />
            <span className="text-2xs text-muted-foreground">{formatTime(message.timestamp)}</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function SystemBubble({ message }: { message: Message }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex justify-center px-4 py-2"
      role="status"
      aria-live="polite"
    >
      <span className="rounded-full bg-muted px-3 py-1 text-2xs text-muted-foreground">
        {message.content}
      </span>
    </motion.div>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === "user") return <UserBubble message={message} />;
  if (message.role === "system") return <SystemBubble message={message} />;
  return <AssistantBubble message={message} />;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
