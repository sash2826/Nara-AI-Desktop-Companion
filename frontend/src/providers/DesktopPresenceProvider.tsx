import { useEffect, useState, type ReactNode } from "react";
import { DesktopPresenceContext } from "./DesktopPresenceContext";
import { DesktopPresenceService } from "@/services/desktop/DesktopPresenceService";

interface DesktopPresenceProviderProps {
  children: ReactNode;
}

/**
 * Creates and provides a single DesktopPresenceService instance to the React tree.
 *
 * The service is initialized automatically on mount and shut down on unmount.
 * useState with a lazy initializer creates the service exactly once per mount,
 * preventing re-creation on re-renders.
 */
export function DesktopPresenceProvider({ children }: DesktopPresenceProviderProps) {
  // Initialize synchronously so child effects (e.g. OrbLayer) can register overlays
  // immediately on their first useEffect run without racing against this parent effect.
  const [service] = useState<DesktopPresenceService>(() => {
    const svc = new DesktopPresenceService();
    svc.initialize();
    return svc;
  });

  useEffect(() => {
    return () => {
      void service.shutdown();
    };
  }, [service]);

  return (
    <DesktopPresenceContext.Provider value={service}>{children}</DesktopPresenceContext.Provider>
  );
}
