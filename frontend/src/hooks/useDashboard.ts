import { useState, useEffect, useCallback } from "react";
import { IPCClient, type DashboardStats } from "@/services/ipc/IPCClient";

const SUGGESTIONS_CACHE_KEY = "eac-suggested-queries";
const SUGGESTIONS_TTL_MS = 60 * 60 * 1000; // 1 hour

interface CachedSuggestions {
  suggestions: string[];
  cachedAt: number;
}

function loadCachedSuggestions(): string[] | null {
  try {
    const raw = localStorage.getItem(SUGGESTIONS_CACHE_KEY);
    if (!raw) return null;
    const parsed: CachedSuggestions = JSON.parse(raw);
    if (Date.now() - parsed.cachedAt > SUGGESTIONS_TTL_MS) return null;
    return parsed.suggestions;
  } catch {
    return null;
  }
}

function saveSuggestionsCache(suggestions: string[]): void {
  try {
    const payload: CachedSuggestions = { suggestions, cachedAt: Date.now() };
    localStorage.setItem(SUGGESTIONS_CACHE_KEY, JSON.stringify(payload));
  } catch {
    // Ignore storage failures
  }
}

interface DashboardState {
  stats: DashboardStats | null;
  suggestions: string[];
  isLoadingStats: boolean;
  isLoadingSuggestions: boolean;
  statsError: string | null;
}

export function useDashboard() {
  const [state, setState] = useState<DashboardState>({
    stats: null,
    suggestions: [],
    isLoadingStats: true,
    isLoadingSuggestions: false,
    statsError: null,
  });

  const loadStats = useCallback(async () => {
    setState((s) => ({ ...s, isLoadingStats: true, statsError: null }));
    try {
      const stats = await IPCClient.getStats();
      setState((s) => ({ ...s, stats, isLoadingStats: false }));
      return stats;
    } catch (err) {
      setState((s) => ({
        ...s,
        isLoadingStats: false,
        statsError: err instanceof Error ? err.message : "Failed to load statistics.",
      }));
      return null;
    }
  }, []);

  const loadSuggestions = useCallback(async (recentFilePaths: string[], bust = false) => {
    if (!recentFilePaths.length) return;

    // Use cache on initial load; skip it on manual refresh.
    if (!bust) {
      const cached = loadCachedSuggestions();
      if (cached) {
        setState((s) => ({ ...s, suggestions: cached }));
        return;
      }
    }

    setState((s) => ({ ...s, isLoadingSuggestions: true }));
    try {
      const suggestions = await IPCClient.getSuggestedQueries(recentFilePaths, 5);
      saveSuggestionsCache(suggestions);
      setState((s) => ({ ...s, suggestions, isLoadingSuggestions: false }));
    } catch {
      // Suggestions are non-critical — fail silently
      setState((s) => ({ ...s, isLoadingSuggestions: false }));
    }
  }, []);

  const refresh = useCallback(async () => {
    const stats = await loadStats();
    if (stats?.recent_files.length) {
      const paths = stats.recent_files.map((f) => f.file_path);
      // Bust cache on manual refresh so new documents produce fresh suggestions.
      await loadSuggestions(paths, true);
    }
  }, [loadStats, loadSuggestions]);

  useEffect(() => {
    loadStats().then((stats) => {
      if (stats?.recent_files.length) {
        const paths = stats.recent_files.map((f) => f.file_path);
        loadSuggestions(paths, false);
      }
    });
  }, [loadStats, loadSuggestions]);

  return {
    stats: state.stats,
    suggestions: state.suggestions,
    isLoadingStats: state.isLoadingStats,
    isLoadingSuggestions: state.isLoadingSuggestions,
    statsError: state.statsError,
    refresh,
  };
}
