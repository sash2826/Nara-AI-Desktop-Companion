import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DocumentFilter, DocumentSort, DocumentSortKey } from "@/types/workspace";

const EXTENSION_OPTIONS = [
  { label: "All types", value: null },
  { label: "PDF", value: ".pdf" },
  { label: "Word", value: ".docx" },
  { label: "Markdown", value: ".md" },
  { label: "Text", value: ".txt" },
] as const;

const SORT_OPTIONS: { label: string; key: DocumentSortKey }[] = [
  { label: "Recently indexed", key: "indexed_at" },
  { label: "File name", key: "file_path" },
  { label: "Chunks", key: "chunk_count" },
];

interface DocumentFiltersProps {
  filter: DocumentFilter;
  sort: DocumentSort;
  onFilterChange: (f: Partial<DocumentFilter>) => void;
  onSortChange: (s: DocumentSort) => void;
  onReset: () => void;
  totalCount: number;
  filteredCount: number;
}

export function DocumentFilters({
  filter,
  sort,
  onFilterChange,
  onSortChange,
  onReset,
  totalCount,
  filteredCount,
}: DocumentFiltersProps) {
  const isFiltered = filter.search || filter.extension;

  return (
    <div className="space-y-2">
      {/* Search input */}
      <div className="relative">
        <Search
          size={13}
          className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
          strokeWidth={1.5}
        />
        <input
          type="text"
          value={filter.search}
          onChange={(e) => onFilterChange({ search: e.target.value })}
          placeholder="Filter by file name…"
          className={cn(
            "h-8 w-full rounded-md border border-border bg-background pl-7 pr-3 text-sm",
            "text-foreground placeholder:text-muted-foreground",
            "focus:outline-none focus:ring-1 focus:ring-ring"
          )}
        />
        {filter.search && (
          <button
            onClick={() => onFilterChange({ search: "" })}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X size={12} />
          </button>
        )}
      </div>

      {/* Extension + sort row */}
      <div className="flex items-center gap-2">
        <div className="flex gap-1">
          {EXTENSION_OPTIONS.map((opt) => (
            <button
              key={String(opt.value)}
              onClick={() => onFilterChange({ extension: opt.value })}
              className={cn(
                "rounded-md px-2 py-1 text-xs font-medium transition-colors",
                filter.extension === opt.value
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <select
            value={sort.key}
            onChange={(e) => onSortChange({ ...sort, key: e.target.value as DocumentSortKey })}
            className={cn(
              "h-7 rounded-md border border-border bg-background px-2 text-xs text-foreground",
              "focus:outline-none focus:ring-1 focus:ring-ring"
            )}
            aria-label="Sort by"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.key} value={o.key}>
                {o.label}
              </option>
            ))}
          </select>

          {isFiltered && (
            <button
              onClick={onReset}
              className="text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Count */}
      <p className="text-xs text-muted-foreground">
        {isFiltered ? `${filteredCount} of ${totalCount}` : totalCount} document
        {totalCount !== 1 ? "s" : ""}
      </p>
    </div>
  );
}
