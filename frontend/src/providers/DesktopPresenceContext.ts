import { createContext } from "react";
import type { DesktopPresenceService } from "@/services/desktop/DesktopPresenceService";

export const DesktopPresenceContext = createContext<DesktopPresenceService | null>(null);
