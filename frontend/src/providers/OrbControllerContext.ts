import { createContext } from "react";
import type { OrbController } from "@/services/desktop/OrbController";

export const OrbControllerContext = createContext<OrbController | null>(null);
