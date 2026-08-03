import { IPCClient, type SearchResultItem } from "@/services/ipc/IPCClient";
import type { SearchMode, SearchFilters } from "@/store/searchStore";

export interface SearchRequest {
  query: string;
  mode: SearchMode;
  filters: SearchFilters;
}

export interface SearchResponse {
  results: SearchResultItem[];
  mode: SearchMode;
  durationMs: number;
}

export class SearchService {
  async search(request: SearchRequest): Promise<SearchResponse> {
    const { query, mode, filters } = request;
    const trimmed = query.trim();

    if (!trimmed) {
      return { results: [], mode, durationMs: 0 };
    }

    const start = performance.now();

    const raw =
      mode === "keyword"
        ? await IPCClient.searchKeyword(trimmed, filters.topK, filters.workspacePath ?? undefined)
        : await IPCClient.searchSemantic(trimmed, filters.topK, filters.workspacePath ?? undefined);

    const durationMs = Math.round(performance.now() - start);

    return { results: raw.results, mode, durationMs };
  }
}

export const searchService = new SearchService();
