import React, { useCallback, useEffect, useMemo, useState } from "react";
import type { ThemeMode } from "@/types/theme";
import { ThemeContext } from "./ThemeContext";

const STORAGE_KEY = "eac-theme";
const THEME_CLASSES: Record<ThemeMode, string> = {
  light: "theme-light",
  dark: "theme-dark",
  system: "theme-system",
};

function getSystemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function loadPersistedTheme(): ThemeMode {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "system") {
      return stored;
    }
  } catch {
    // localStorage unavailable (e.g. sandboxed iframe) — fall through to default
  }
  return "system";
}

function persistTheme(theme: ThemeMode): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Silently ignore storage failures
  }
}

function applyThemeToDocument(theme: ThemeMode): void {
  const root = document.documentElement;
  Object.values(THEME_CLASSES).forEach((cls) => root.classList.remove(cls));
  root.classList.add(THEME_CLASSES[theme]);

  // Keep the `dark` class in sync so Tailwind's darkMode: ["class"] strategy works.
  const resolved = theme === "system" ? getSystemTheme() : theme;
  root.classList.toggle("dark", resolved === "dark");
}

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: ThemeMode;
}

export function ThemeProvider({ children, defaultTheme }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    return defaultTheme ?? loadPersistedTheme();
  });

  const resolvedTheme: "light" | "dark" = useMemo(
    () => (theme === "system" ? getSystemTheme() : theme),
    [theme]
  );

  const setTheme = useCallback((next: ThemeMode) => {
    setThemeState(next);
    persistTheme(next);
    applyThemeToDocument(next);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  }, [resolvedTheme, setTheme]);

  // Apply theme on mount and respond to system preference changes.
  useEffect(() => {
    applyThemeToDocument(theme);

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleSystemChange = () => {
      if (theme === "system") {
        applyThemeToDocument("system");
      }
    };

    mediaQuery.addEventListener("change", handleSystemChange);
    return () => mediaQuery.removeEventListener("change", handleSystemChange);
  }, [theme]);

  const value = useMemo(
    () => ({ theme, resolvedTheme, setTheme, toggleTheme }),
    [theme, resolvedTheme, setTheme, toggleTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
