import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ORB_SIZE } from "@/components/orb/OrbContainer";
import { clamp } from "@/lib/utils";

export interface OrbPosition {
  x: number;
  y: number;
}

interface OrbStore {
  position: OrbPosition;
  setPosition: (position: OrbPosition) => void;
}

function defaultPosition(): OrbPosition {
  return {
    x: window.innerWidth - ORB_SIZE * 2,
    y: window.innerHeight - ORB_SIZE * 2,
  };
}

function clampToViewport(x: number, y: number): OrbPosition {
  return {
    x: clamp(x, 0, window.innerWidth - ORB_SIZE),
    y: clamp(y, 0, window.innerHeight - ORB_SIZE),
  };
}

export const useOrbStore = create<OrbStore>()(
  persist(
    (set) => ({
      position: defaultPosition(),

      setPosition: (position) => set({ position: clampToViewport(position.x, position.y) }),
    }),
    {
      name: "eac-orb-position",
    }
  )
);
