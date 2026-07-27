import { useOrbStore, type OrbPosition } from "@/store/orbStore";

/**
 * Provides the persisted orb position and a setter that clamps to the viewport.
 *
 * Position is persisted to localStorage via the Zustand `persist` middleware
 * and is restored automatically on the next application launch.
 */
export function useOrbPosition(): { position: OrbPosition; setPosition: (p: OrbPosition) => void } {
  const position = useOrbStore((s) => s.position);
  const setPosition = useOrbStore((s) => s.setPosition);
  return { position, setPosition };
}
