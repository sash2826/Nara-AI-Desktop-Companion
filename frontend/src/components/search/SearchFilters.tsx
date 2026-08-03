import { SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SearchFilters as Filters } from "@/store/searchStore";

interface SearchFiltersProps {
  filters: Filters;
  onChange: (filters: Partial<Filters>) => void;
  className?: string;
}

const TOP_K_OPTIONS = [5, 10, 20, 50] as const;

export function SearchFilters({ filters, onChange, className }: SearchFiltersProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <SlidersHorizontal size={13} strokeWidth={1.75} />
        Filters
      </span>

      {/* Result count */}
      <div className="flex items-center gap-1.5">
        <label htmlFor="top-k-select" className="text-xs text-muted-foreground">
          Results
        </label>
        <select
          id="top-k-select"
          value={filters.topK}
          onChange={(e) => onChange({ topK: Number(e.target.value) })}
          className="h-7 rounded-md border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {TOP_K_OPTIONS.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>

      {/* Workspace path filter */}
      <div className="flex items-center gap-1.5">
        <label htmlFor="workspace-filter" className="text-xs text-muted-foreground">
          Workspace
        </label>
        <input
          id="workspace-filter"
          type="text"
          value={filters.workspacePath ?? ""}
          onChange={(e) => onChange({ workspacePath: e.target.value || null })}
          placeholder="All workspaces"
          className="h-7 w-48 rounded-md border border-input bg-background px-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>
    </div>
  );
}
