import { create } from "zustand";
import type { ThemeMode } from "@/types/theme";

// ─── Persisted settings shape ─────────────────────────────────────────────────

export interface AIProviderSettings {
  endpoint: string;
  model: string;
  timeoutMs: number;
  maxRetries: number;
}

export interface IndexingSettings {
  chunkSize: number;
  chunkOverlap: number;
  maxFileSizeKb: number;
  autoIndexOnStartup: boolean;
}

export interface AppSettings {
  theme: ThemeMode;
  sidebarCollapsed: boolean;
  aiProvider: AIProviderSettings;
  indexing: IndexingSettings;
}

// ─── Defaults ─────────────────────────────────────────────────────────────────

const DEFAULT_AI_PROVIDER: AIProviderSettings = {
  endpoint: import.meta.env.VITE_APIM_ENDPOINT ?? "",
  model: "gpt-5.4-mini_gb_2026-03-17",
  timeoutMs: 30_000,
  maxRetries: 3,
};

const DEFAULT_INDEXING: IndexingSettings = {
  chunkSize: 1500,
  chunkOverlap: 200,
  maxFileSizeKb: 10_240,
  autoIndexOnStartup: false,
};

export const DEFAULT_SETTINGS: AppSettings = {
  theme: "system",
  sidebarCollapsed: false,
  aiProvider: DEFAULT_AI_PROVIDER,
  indexing: DEFAULT_INDEXING,
};

const STORAGE_KEY = "eac-settings";

// ─── Persistence helpers ──────────────────────────────────────────────────────

function load(): AppSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<AppSettings>;
    return {
      ...DEFAULT_SETTINGS,
      ...parsed,
      aiProvider: { ...DEFAULT_AI_PROVIDER, ...(parsed.aiProvider ?? {}) },
      indexing: { ...DEFAULT_INDEXING, ...(parsed.indexing ?? {}) },
    };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

function save(settings: AppSettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Silently ignore — Tauri sandboxed context may restrict storage
  }
}

// ─── Store ────────────────────────────────────────────────────────────────────

interface SettingsStore {
  settings: AppSettings;
  isDirty: boolean;
  apiKeyVersion: number;

  updateTheme: (theme: ThemeMode) => void;
  updateAIProvider: (patch: Partial<AIProviderSettings>) => void;
  updateIndexing: (patch: Partial<IndexingSettings>) => void;
  saveSettings: () => void;
  resetToDefaults: () => void;
  bumpApiKeyVersion: () => void;
}

export const useSettingsStore = create<SettingsStore>((set, get) => ({
  settings: load(),
  isDirty: false,
  apiKeyVersion: 0,

  updateTheme: (theme) =>
    set((state) => ({
      settings: { ...state.settings, theme },
      isDirty: true,
    })),

  updateAIProvider: (patch) =>
    set((state) => ({
      settings: {
        ...state.settings,
        aiProvider: { ...state.settings.aiProvider, ...patch },
      },
      isDirty: true,
    })),

  updateIndexing: (patch) =>
    set((state) => ({
      settings: {
        ...state.settings,
        indexing: { ...state.settings.indexing, ...patch },
      },
      isDirty: true,
    })),

  saveSettings: () => {
    const { settings } = get();
    save(settings);
    set({ isDirty: false });
  },

  resetToDefaults: () => {
    save(DEFAULT_SETTINGS);
    set({ settings: DEFAULT_SETTINGS, isDirty: false });
  },

  bumpApiKeyVersion: () => set((state) => ({ apiKeyVersion: state.apiKeyVersion + 1 })),
}));
