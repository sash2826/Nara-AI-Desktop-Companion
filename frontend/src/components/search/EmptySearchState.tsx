import { SearchX, Search } from "lucide-react";
import type { SearchMode } from "@/store/searchStore";

interface EmptySearchStateProps {
  hasSearched: boolean;
  query: string;
  mode: SearchMode;
}

export function EmptySearchState({ hasSearched, query, mode }: EmptySearchStateProps) {
  if (!hasSearched) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
          <Search size={24} className="text-muted-foreground" strokeWidth={1.5} />
        </div>
        <div className="max-w-xs space-y-1">
          <h3 className="text-sm font-semibold text-foreground">Search your knowledge</h3>
          <p className="text-sm text-muted-foreground">
            Type a query above and press Enter. <span className="capitalize">{mode}</span> search
            will find relevant document chunks across your indexed workspace.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
        <SearchX size={24} className="text-muted-foreground" strokeWidth={1.5} />
      </div>
      <div className="max-w-xs space-y-1">
        <h3 className="text-sm font-semibold text-foreground">No results found</h3>
        <p className="text-sm text-muted-foreground">
          No documents matched{" "}
          <span className="font-medium text-foreground">&ldquo;{query}&rdquo;</span> using {mode}{" "}
          search. Try different keywords or switch search modes.
        </p>
      </div>
    </div>
  );
}
