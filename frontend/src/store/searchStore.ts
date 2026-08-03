import { create } from "zustand";
import type { SearchResultItem } from "@/services/ipc/IPCClient";

export type SearchMode = "semantic" | "keyword";

export interface SearchFilters {
  workspacePath: string | null;
  topK: number;
}

interface SearchStore {
  query: string;
  mode: SearchMode;
  filters: SearchFilters;
  results: SearchResultItem[];
  isSearching: boolean;
  error: string | null;
  hasSearched: boolean;

  setQuery: (query: string) => void;
  setMode: (mode: SearchMode) => void;
  setFilters: (filters: Partial<SearchFilters>) => void;
  setResults: (results: SearchResultItem[]) => void;
  setSearching: (searching: boolean) => void;
  setError: (error: string | null) => void;
  clearResults: () => void;
}

const DEFAULT_FILTERS: SearchFilters = {
  workspacePath: null,
  topK: 10,
};

export const useSearchStore = create<SearchStore>((set) => ({
  query: "",
  mode: "semantic",
  filters: DEFAULT_FILTERS,
  results: [],
  isSearching: false,
  error: null,
  hasSearched: false,

  setQuery: (query) => set({ query }),

  setMode: (mode) => set({ mode }),

  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),

  setResults: (results) => set({ results, hasSearched: true, error: null }),

  setSearching: (searching) => set({ isSearching: searching }),

  setError: (error) => set({ error, isSearching: false }),

  clearResults: () => set({ results: [], hasSearched: false, error: null, query: "" }),
}));
