import React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";

interface LayoutProviderProps {
  children: React.ReactNode;
}

/**
 * Provides infrastructure required by layout and UI components:
 * - Radix TooltipProvider (required at the root for all Tooltip usage)
 *
 * Intentionally kept thin. Additional layout-scoped providers are added here,
 * not directly in App.tsx, to keep the application entry point clean.
 */
export function LayoutProvider({ children }: LayoutProviderProps) {
  return (
    <TooltipPrimitive.Provider delayDuration={400} skipDelayDuration={100}>
      {children}
    </TooltipPrimitive.Provider>
  );
}
