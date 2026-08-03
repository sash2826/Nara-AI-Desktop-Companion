import { useCallback, useRef } from "react";
import { useSearchStore } from "@/store/searchStore";
import { searchService } from "@/services/search/SearchService";

export function useSearch() {
  const store = useSearchStore();
  const abortRef = useRef<AbortController | null>(null);

  const search = useCallback(
    async (overrideQuery?: string) => {
      const query = (overrideQuery ?? store.query).trim();
      if (!query) return;

      // Cancel any in-flight search
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      store.setSearching(true);
      store.setError(null);

      try {
        const response = await searchService.search({
          query,
          mode: store.mode,
          filters: store.filters,
        });
        store.setResults(response.results);
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") return;
        store.setError(err instanceof Error ? err.message : "Search failed. Please try again.");
      } finally {
        store.setSearching(false);
      }
    },
    [store]
  );

  const clear = useCallback(() => {
    abortRef.current?.abort();
    store.clearResults();
  }, [store]);

  return {
    query: store.query,
    mode: store.mode,
    filters: store.filters,
    results: store.results,
    isSearching: store.isSearching,
    error: store.error,
    hasSearched: store.hasSearched,
    setQuery: store.setQuery,
    setMode: store.setMode,
    setFilters: store.setFilters,
    search,
    clear,
  };
}
