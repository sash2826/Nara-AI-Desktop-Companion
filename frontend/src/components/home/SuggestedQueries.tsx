import { Sparkles, Search, Loader2, RefreshCw } from "lucide-react";
import { useNavigationStore } from "@/store/navigationStore";
import { useSearchStore } from "@/store/searchStore";

interface SuggestedQueriesProps {
  suggestions: string[];
  isLoading: boolean;
  onReshuffle?: () => void;
}

export function SuggestedQueries({ suggestions, isLoading, onReshuffle }: SuggestedQueriesProps) {
  const { setActiveItem } = useNavigationStore();
  const { setQuery } = useSearchStore();

  const handleQuery = (query: string) => {
    setQuery(query);
    setActiveItem("search");
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Sparkles size={13} className="text-muted-foreground" strokeWidth={1.75} />
          <span className="text-xs font-medium text-muted-foreground">Suggested searches</span>
        </div>
        {onReshuffle && suggestions.length > 0 && !isLoading && (
          <button
            type="button"
            onClick={onReshuffle}
            aria-label="Show different suggestions"
            className="flex items-center gap-1 rounded-md px-1.5 py-1 text-2xs text-muted-foreground/60 transition-colors hover:bg-muted hover:text-muted-foreground"
          >
            <RefreshCw size={10} strokeWidth={1.75} />
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 size={12} className="animate-spin" />
          Generating suggestions…
        </div>
      ) : suggestions.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          Index some documents to get AI-generated search suggestions.
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((query) => (
            <button
              key={query}
              type="button"
              onClick={() => handleQuery(query)}
              className="flex items-center gap-1.5 rounded-full border border-border bg-muted px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/30 hover:bg-primary/10 hover:text-primary"
            >
              <Search size={11} />
              {query}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
