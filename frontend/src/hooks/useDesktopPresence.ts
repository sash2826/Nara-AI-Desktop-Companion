import { useContext } from "react";
import { DesktopPresenceContext } from "@/providers/DesktopPresenceContext";
import type { DesktopPresenceService } from "@/services/desktop/DesktopPresenceService";

/**
 * Returns the DesktopPresenceService from context.
 *
 * @throws {Error} if called outside of a DesktopPresenceProvider.
 */
export function useDesktopPresence(): DesktopPresenceService {
  const service = useContext(DesktopPresenceContext);
  if (service === null) {
    throw new Error("useDesktopPresence must be called inside a DesktopPresenceProvider.");
  }
  return service;
}
