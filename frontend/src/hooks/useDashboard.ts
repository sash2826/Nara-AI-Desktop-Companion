import { useState, useEffect, useCallback, useRef } from "react";
import { IPCClient, type DashboardStats } from "@/services/ipc/IPCClient";

const SUGGESTIONS_CACHE_KEY = "eac-suggested-queries";
const SUGGESTIONS_TTL_MS = 20 * 60 * 1000; // 20 minutes
const POOL_SIZE = 12;
const VISIBLE_COUNT = 3;
const RESHUFFLE_BUST_THRESHOLD = 4; // fresh fetch after 4 local reshuffles

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

function pickRandom<T>(arr: T[], n: number): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, Math.min(n, copy.length));
}

interface DashboardState {
  stats: DashboardStats | null;
  suggestionPool: string[];
  suggestions: string[]; // visible slice — 3 randomly picked from pool
  isLoadingStats: boolean;
  isLoadingSuggestions: boolean;
  statsError: string | null;
}

export function useDashboard() {
  const [state, setState] = useState<DashboardState>({
    stats: null,
    suggestionPool: [],
    suggestions: [],
    isLoadingStats: true,
    isLoadingSuggestions: false,
    statsError: null,
  });

  const reshuffleCountRef = useRef(0);
  const recentFilePathsRef = useRef<string[]>([]);

  const applyPool = useCallback((pool: string[]) => {
    setState((s) => ({
      ...s,
      suggestionPool: pool,
      suggestions: pickRandom(pool, VISIBLE_COUNT),
      isLoadingSuggestions: false,
    }));
    reshuffleCountRef.current = 0;
  }, []);

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

  const loadSuggestions = useCallback(
    async (recentFilePaths: string[], bust = false) => {
      if (!recentFilePaths.length) return;
      recentFilePathsRef.current = recentFilePaths;

      if (!bust) {
        const cached = loadCachedSuggestions();
        if (cached) {
          applyPool(cached);
          return;
        }
      }

      setState((s) => ({ ...s, isLoadingSuggestions: true }));
      try {
        const pool = await IPCClient.getSuggestedQueries(recentFilePaths, POOL_SIZE);
        saveSuggestionsCache(pool);
        applyPool(pool);
      } catch {
        setState((s) => ({ ...s, isLoadingSuggestions: false }));
      }
    },
    [applyPool]
  );

  const reshuffleSuggestions = useCallback(() => {
    reshuffleCountRef.current += 1;

    // Pick a new random 3 from the existing pool immediately
    setState((s) => ({
      ...s,
      suggestions: pickRandom(s.suggestionPool, VISIBLE_COUNT),
    }));

    // After threshold reshuffles, bust cache and fetch a genuinely fresh pool
    if (
      reshuffleCountRef.current >= RESHUFFLE_BUST_THRESHOLD &&
      recentFilePathsRef.current.length
    ) {
      reshuffleCountRef.current = 0;
      localStorage.removeItem(SUGGESTIONS_CACHE_KEY);
      loadSuggestions(recentFilePathsRef.current, true);
    }
  }, [loadSuggestions]);

  const refresh = useCallback(async () => {
    const stats = await loadStats();
    if (stats?.recent_files.length) {
      const paths = stats.recent_files.map((f) => f.file_path);
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
    reshuffleSuggestions,
  };
}
