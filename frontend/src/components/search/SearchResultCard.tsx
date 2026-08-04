import { useState } from "react";
import { FileText, FolderOpen, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { IPCClient } from "@/services/ipc/IPCClient";
import type { SearchResultItem } from "@/services/ipc/IPCClient";

interface SearchResultCardProps {
  result: SearchResultItem;
  rank: number;
  query: string;
  className?: string;
}

function highlightMatches(text: string, query: string): React.ReactNode {
  const terms = query
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

  if (!terms.length) return text;

  const pattern = new RegExp(`(${terms.join("|")})`, "gi");
  const parts = text.split(pattern);

  return parts.map((part, i) =>
    pattern.test(part) ? (
      <mark
        key={i}
        className="rounded-sm bg-yellow-200 px-0.5 text-yellow-900 dark:bg-yellow-800 dark:text-yellow-100"
      >
        {part}
      </mark>
    ) : (
      part
    )
  );
}

function fileName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

/** Colour-coded relevance badge: green ≥80 %, amber ≥60 %, muted otherwise. */
function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const colorClass =
    pct >= 80
      ? "bg-success/15 text-success border-success/30"
      : pct >= 60
        ? "bg-yellow-400/15 text-yellow-500 border-yellow-400/30"
        : "bg-muted text-muted-foreground border-border";

  return (
    <span
      className={cn(
        "flex-shrink-0 rounded-full border px-1.5 py-0.5 text-2xs font-semibold tabular-nums",
        colorClass
      )}
      title={`Relevance score: ${score.toFixed(4)}`}
    >
      {pct}%
    </span>
  );
}

/** Inline open-file button — sits in the card header next to the filename. */
function OpenFileButton({ path }: { path: string }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const handleOpen = async () => {
    if (loading) return;
    setLoading(true);
    setError(false);
    try {
      await IPCClient.openFile(path);
    } catch {
      setError(true);
      setTimeout(() => setError(false), 2000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={() => void handleOpen()}
      title={`Open ${path}`}
      aria-label={`Open ${fileName(path)}`}
      className={cn(
        "inline-flex flex-shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-2xs font-medium",
        "border transition-colors",
        error
          ? "border-destructive/30 bg-destructive/10 text-destructive"
          : "border-border bg-muted text-muted-foreground hover:border-primary/30 hover:bg-primary/10 hover:text-primary",
        "opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
      )}
    >
      {loading ? (
        <Loader2 size={10} className="animate-spin" />
      ) : (
        <FolderOpen size={10} strokeWidth={1.5} />
      )}
      {error ? "Error" : "Open"}
    </button>
  );
}

export function SearchResultCard({ result, rank, query, className }: SearchResultCardProps) {
  return (
    <article
      className={cn(
        "group flex flex-col gap-2 rounded-lg border border-border bg-card p-4 transition-colors hover:border-border/80 hover:bg-card/80",
        className
      )}
      aria-label={`Result ${rank}: ${fileName(result.document_path)}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <FileText size={14} className="flex-shrink-0 text-muted-foreground" strokeWidth={1.5} />
          <span
            className="truncate text-sm font-medium text-foreground"
            title={result.document_path}
          >
            {fileName(result.document_path)}
          </span>
          <span className="flex-shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-2xs text-muted-foreground">
            #{rank}
          </span>
        </div>

        <div className="flex flex-shrink-0 items-center gap-2">
          <ScoreBadge score={result.score} />
          <OpenFileButton path={result.document_path} />
        </div>
      </div>

      {/* Content excerpt with query term highlighting */}
      <p className="text-sm leading-relaxed text-muted-foreground line-clamp-4">
        {highlightMatches(result.content, query)}
      </p>

      {/* Footer — clickable full path + chunk info */}
      <div className="flex items-center justify-between gap-2">
        <PathChip path={result.document_path} />
        <span className="flex-shrink-0 text-xs text-muted-foreground/70">
          chunk {result.chunk_index + 1}
        </span>
      </div>
    </article>
  );
}

/** Compact clickable path in the card footer. */
function PathChip({ path }: { path: string }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const handleOpen = async () => {
    if (loading) return;
    setLoading(true);
    setError(false);
    try {
      await IPCClient.openFile(path);
    } catch {
      setError(true);
      setTimeout(() => setError(false), 2000);
    } finally {
      setLoading(false);
    }
  };

  // Show only the last two segments to keep the footer compact.
  const segments = path.split(/[\\/]/);
  const displayPath = segments.length > 2 ? "…\\" + segments.slice(-2).join("\\") : path;

  return (
    <button
      type="button"
      onClick={() => void handleOpen()}
      title={path}
      className={cn(
        "group/path flex min-w-0 items-center gap-1 rounded px-1 py-0.5 text-xs transition-colors",
        error ? "text-destructive" : "text-muted-foreground/70 hover:text-primary"
      )}
    >
      {loading ? (
        <Loader2 size={10} className="flex-shrink-0 animate-spin" />
      ) : (
        <FolderOpen
          size={10}
          strokeWidth={1.5}
          className="flex-shrink-0 opacity-0 transition-opacity group-hover/path:opacity-100"
        />
      )}
      <span className="truncate font-mono">{error ? "Failed to open" : displayPath}</span>
    </button>
  );
}
