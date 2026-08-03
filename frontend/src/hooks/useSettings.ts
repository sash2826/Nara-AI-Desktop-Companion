import { useCallback, useEffect } from "react";
import { useSettingsStore, DEFAULT_SETTINGS } from "@/store/settingsStore";
import { useTheme } from "@/hooks/useTheme";
import type { ThemeMode } from "@/types/theme";
import type { AIProviderSettings, IndexingSettings } from "@/store/settingsStore";

/**
 * Unified settings hook.
 *
 * Bridges settingsStore with the ThemeProvider so that a theme change
 * in Settings is immediately applied to the document — not just stored.
 */
export function useSettings() {
  const store = useSettingsStore();
  const { setTheme } = useTheme();

  // Keep ThemeProvider in sync when the store is hydrated from localStorage
  useEffect(() => {
    setTheme(store.settings.theme);
    // Only run on mount to sync the persisted value — subsequent changes go
    // through updateTheme which calls setTheme directly below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateTheme = useCallback(
    (theme: ThemeMode) => {
      store.updateTheme(theme);
      setTheme(theme);
    },
    [store, setTheme]
  );

  const updateAIProvider = useCallback(
    (patch: Partial<AIProviderSettings>) => {
      store.updateAIProvider(patch);
    },
    [store]
  );

  const updateIndexing = useCallback(
    (patch: Partial<IndexingSettings>) => {
      store.updateIndexing(patch);
    },
    [store]
  );

  const save = useCallback(() => {
    store.saveSettings();
  }, [store]);

  const reset = useCallback(() => {
    store.resetToDefaults();
    setTheme(DEFAULT_SETTINGS.theme);
  }, [store, setTheme]);

  return {
    settings: store.settings,
    isDirty: store.isDirty,
    updateTheme,
    updateAIProvider,
    updateIndexing,
    save,
    reset,
  };
}
