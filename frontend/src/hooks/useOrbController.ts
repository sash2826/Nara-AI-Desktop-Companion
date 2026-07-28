import { useContext } from "react";
import { OrbControllerContext } from "@/providers/OrbControllerContext";
import type { OrbController } from "@/services/desktop/OrbController";

/**
 * Returns the OrbController from context.
 *
 * @throws {Error} if called outside of OrbLayer (which provides the context).
 */
export function useOrbController(): OrbController {
  const controller = useContext(OrbControllerContext);
  if (controller === null) {
    throw new Error("useOrbController must be called inside OrbLayer.");
  }
  return controller;
}
