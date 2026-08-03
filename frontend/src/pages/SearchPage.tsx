import { useCallback } from "react";
import { AlertCircle } from "lucide-react";
import { useSearch } from "@/hooks/useSearch";
import { SearchInput } from "@/components/search/SearchInput";
import { SearchModeSelector } from "@/components/search/SearchModeSelector";
import { SearchFilters } from "@/components/search/SearchFilters";
import { SearchResultCard } from "@/components/search/SearchResultCard";
import { EmptySearchState } from "@/components/search/EmptySearchState";

export function SearchPage() {
  const {
    query,
    mode,
    filters,
    results,
    isSearching,
    error,
    hasSearched,
    setQuery,
    setMode,
    setFilters,
    search,
    clear,
  } = useSearch();

  const handleSearch = useCallback(() => {
    search();
  }, [search]);

  const handleQueryChange = useCallback(
    (value: string) => {
      setQuery(value);
    },
    [setQuery]
  );

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Search bar row */}
      <div className="flex items-center gap-3">
        <SearchInput
          value={query}
          isSearching={isSearching}
          onChange={handleQueryChange}
          onSearch={handleSearch}
          onClear={clear}
          className="flex-1"
        />
        <SearchModeSelector mode={mode} onChange={setMode} className="flex-shrink-0" />
      </div>

      {/* Filters row */}
      <SearchFilters filters={filters} onChange={setFilters} />

      {/* Error banner */}
      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <AlertCircle size={14} className="flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Results / empty state */}
      <div className="flex-1 overflow-y-auto">
        {results.length > 0 ? (
          <div className="flex flex-col gap-2">
            {/* Results header */}
            <div className="mb-1 flex items-center justify-between">
              <span className="text-xs text-muted-foreground">
                {results.length} result{results.length !== 1 ? "s" : ""} for{" "}
                <span className="font-medium text-foreground">&ldquo;{query}&rdquo;</span>
              </span>
              <span className="text-xs text-muted-foreground capitalize">{mode} search</span>
            </div>

            {results.map((result, index) => (
              <SearchResultCard
                key={result.chunk_id}
                result={result}
                rank={index + 1}
                query={query}
              />
            ))}
          </div>
        ) : (
          <EmptySearchState hasSearched={hasSearched} query={query} mode={mode} />
        )}
      </div>
    </div>
  );
}
