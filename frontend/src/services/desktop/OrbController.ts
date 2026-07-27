import type { Overlay } from "./Overlay";
import type { DesktopPresenceService } from "./DesktopPresenceService";

/** Stable id used to locate the orb in the OverlayRegistry. */
export const ORB_OVERLAY_ID = "living-orb";

/** The two interaction states supported in this task. */
export type OrbState = "idle" | "hover";

/** Snapshot of the controller's current observable state. */
export interface OrbControllerState {
  visible: boolean;
  orbState: OrbState;
}

/** Listener called whenever the controller state changes. */
export type OrbStateListener = (state: OrbControllerState) => void;

/**
 * Manages the behavioural state of the Living Orb.
 *
 * OrbController implements the Overlay interface so it can be registered with
 * DesktopPresenceService.  It owns visibility and interaction state; React
 * components must never mutate these fields directly.
 *
 * React integration is achieved through a subscribe/unsubscribe pattern.
 * The controller notifies listeners synchronously whenever state changes,
 * allowing hooks to push updates into local React state without the controller
 * having any dependency on React, Zustand, or the DOM.
 *
 * Animation logic and additional states (processing, listening, sleeping, etc.)
 * belong to Task 0.6.4.3 and must not be added here.
 */
export class OrbController implements Overlay {
  readonly id = ORB_OVERLAY_ID;

  private visible = false;
  private orbState: OrbState = "idle";
  private readonly listeners = new Set<OrbStateListener>();
  private registered = false;

  /**
   * Register this controller with DesktopPresenceService.
   *
   * Must be called before any other method.  Safe to call only once.
   * Calling a second time without first calling dispose() is a no-op.
   */
  async register(service: DesktopPresenceService): Promise<void> {
    if (this.registered) {
      return;
    }
    await service.registerOverlay(this);
    this.registered = true;
  }

  /**
   * Unregister this controller from DesktopPresenceService and release all
   * resources.  After dispose() returns, listeners are cleared and the
   * controller must not be used again.
   */
  async dispose(service: DesktopPresenceService): Promise<void> {
    await service.unregisterOverlay(this.id);
    this.listeners.clear();
    this.registered = false;
  }

  // ── Overlay interface ────────────────────────────────────────────────────

  /** Called by DesktopPresenceService immediately after registration. */
  async initialize(): Promise<void> {
    this.visible = true;
    this.orbState = "idle";
    this.notify();
  }

  async show(): Promise<void> {
    if (this.visible) return;
    this.visible = true;
    this.notify();
  }

  async hide(): Promise<void> {
    if (!this.visible) return;
    this.visible = false;
    this.notify();
  }

  async destroy(): Promise<void> {
    this.visible = false;
    this.orbState = "idle";
    this.notify();
  }

  isVisible(): boolean {
    return this.visible;
  }

  // ── Interaction events ───────────────────────────────────────────────────

  /** Notify the controller that the user's pointer has entered the orb. */
  onHoverEnter(): void {
    if (this.orbState === "hover") return;
    this.orbState = "hover";
    this.notify();
  }

  /** Notify the controller that the user's pointer has left the orb. */
  onHoverLeave(): void {
    if (this.orbState === "idle") return;
    this.orbState = "idle";
    this.notify();
  }

  // ── Observable state ─────────────────────────────────────────────────────

  /** Returns a snapshot of the current state. */
  getState(): OrbControllerState {
    return { visible: this.visible, orbState: this.orbState };
  }

  /**
   * Subscribe to state changes.  The listener is called synchronously
   * whenever visible or orbState changes.
   *
   * @returns An unsubscribe function.
   */
  subscribe(listener: OrbStateListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify(): void {
    const state = this.getState();
    this.listeners.forEach((l) => l(state));
  }
}
