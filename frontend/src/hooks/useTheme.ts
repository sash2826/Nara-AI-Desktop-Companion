import { useContext } from "react";
import { ThemeContext } from "@/providers/ThemeContext";
import type { ThemeContextValue } from "@/types/theme";

/**
 * Returns the current theme context.
 * Must be used inside a ThemeProvider.
 */
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
