import { useState, useEffect } from "react";
import type { ReactNode } from "react";
import { OrbController } from "@/services/desktop/OrbController";
import { OrbControllerContext } from "./OrbControllerContext";
import { useDesktopPresence } from "@/hooks/useDesktopPresence";

/**
 * Creates the single OrbController instance for the application, registers it
 * with DesktopPresenceService, and provides it to the subtree via context.
 *
 * Must be rendered inside DesktopPresenceProvider. Both OrbLayer (which
 * subscribes to orb state) and GlassPromptContainer (which drives orb state
 * transitions) must be descendants so they can both call useOrbController().
 */
export function OrbControllerProvider({ children }: { children: ReactNode }) {
  const service = useDesktopPresence();
  const [controller] = useState<OrbController>(() => new OrbController());

  useEffect(() => {
    void controller.register(service);
    return () => {
      void controller.dispose(service);
    };
  }, [controller, service]);

  return (
    <OrbControllerContext.Provider value={controller}>{children}</OrbControllerContext.Provider>
  );
}
