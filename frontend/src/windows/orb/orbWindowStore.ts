import { create } from "zustand";

/**
 * Animation states for the standalone orb window.
 * These mirror the Phase 08 spec and drive Framer Motion variants in OrbAnimationEngine.
 */
export type OrbAnimationState = "idle" | "listening" | "processing" | "notification" | "error";

/** Which overlay (if any) is visible above the orb. */
export type OrbOverlayMode = "none" | "query" | "notifications";

interface OrbWindowStore {
  /** Current animation state. */
  animationState: OrbAnimationState;
  /** Number of pending file placement recommendations. Drives notification glow. */
  pendingCount: number;
  /** Which overlay is currently open. */
  overlayMode: OrbOverlayMode;
  /**
   * False when a new batch of suggestions has arrived and the notification
   * overlay hasn't been shown yet. Drives the auto-open on first arrival.
   * Resets to false whenever pendingCount rises from 0.
   */
  notificationsViewed: boolean;

  setAnimationState: (state: OrbAnimationState) => void;
  setPendingCount: (count: number) => void;
  setOverlayMode: (mode: OrbOverlayMode) => void;
  markNotificationsViewed: () => void;
}

export const useOrbWindowStore = create<OrbWindowStore>((set) => ({
  animationState: "idle",
  pendingCount: 0,
  overlayMode: "none",
  notificationsViewed: false,

  setAnimationState: (animationState) => set({ animationState }),
  markNotificationsViewed: () => set({ notificationsViewed: true }),
  setPendingCount: (pendingCount) =>
    set((s) => ({
      pendingCount,
      // Reset viewed flag when a fresh batch of suggestions arrives.
      notificationsViewed: pendingCount > 0 && s.pendingCount === 0 ? false : s.notificationsViewed,
      // Auto-transition to notification state when recommendations arrive
      animationState:
        pendingCount > 0 && s.animationState === "idle"
          ? "notification"
          : s.animationState === "notification" && pendingCount === 0
            ? "idle"
            : s.animationState,
    })),
  setOverlayMode: (overlayMode) =>
    set((s) => ({
      overlayMode,
      // When overlay opens for query: listening; when closed: back to idle/notification
      animationState:
        overlayMode === "query"
          ? "listening"
          : overlayMode === "none"
            ? s.pendingCount > 0
              ? "notification"
              : "idle"
            : s.animationState,
    })),
}));
