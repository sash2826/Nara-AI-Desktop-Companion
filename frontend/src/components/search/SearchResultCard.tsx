import { FileText, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
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

function truncatePath(path: string, maxLen = 60): string {
  if (path.length <= maxLen) return path;
  return "…" + path.slice(-maxLen);
}

export function SearchResultCard({ result, rank, query, className }: SearchResultCardProps) {
  const scorePercent = Math.round(result.score * 100);

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
          <span className="truncate text-sm font-medium text-foreground">
            {fileName(result.document_path)}
          </span>
          <span className="flex-shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-2xs text-muted-foreground">
            #{rank}
          </span>
        </div>

        <div className="flex flex-shrink-0 items-center gap-2">
          <span
            className="text-xs tabular-nums text-muted-foreground"
            title={`Relevance score: ${result.score.toFixed(4)}`}
          >
            {scorePercent}%
          </span>
          <button
            type="button"
            aria-label={`Open ${fileName(result.document_path)}`}
            className="opacity-0 transition-opacity group-hover:opacity-100 text-muted-foreground hover:text-foreground"
          >
            <ExternalLink size={13} />
          </button>
        </div>
      </div>

      {/* Content excerpt */}
      <p className="text-sm leading-relaxed text-muted-foreground line-clamp-4">
        {highlightMatches(result.content, query)}
      </p>

      {/* Footer — path + chunk info */}
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs text-muted-foreground/70" title={result.document_path}>
          {truncatePath(result.document_path)}
        </span>
        <span className="flex-shrink-0 text-xs text-muted-foreground/70">
          chunk {result.chunk_index + 1}
        </span>
      </div>
    </article>
  );
}
