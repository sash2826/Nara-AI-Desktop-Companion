import type { Overlay } from "./Overlay";
import type { DesktopPresenceService } from "./DesktopPresenceService";
import { OrbState } from "@/services/orb/OrbState";
import { OrbStateMachine } from "@/services/orb/OrbStateMachine";

/** Stable id used to locate the orb in the OverlayRegistry. */
export const ORB_OVERLAY_ID = "living-orb";

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
 * DesktopPresenceService. It owns one OrbStateMachine instance which is the
 * single source of truth for orb state. React components must never mutate
 * state directly.
 *
 * React integration is achieved through the subscribe/unsubscribe pattern.
 * The controller notifies listeners synchronously whenever visible or orbState
 * changes, with no dependency on React, Zustand, or the DOM.
 */
export class OrbController implements Overlay {
  readonly id = ORB_OVERLAY_ID;

  private visible = false;
  private readonly stateMachine = new OrbStateMachine();
  private readonly listeners = new Set<OrbStateListener>();
  private registered = false;

  /**
   * Register this controller with DesktopPresenceService.
   *
   * Safe to call only once. Calling a second time without first calling
   * dispose() is a no-op.
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
   * resources. After dispose() returns, listeners are cleared and the
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
    this.stateMachine.reset();
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
    this.stateMachine.reset();
    this.notify();
  }

  isVisible(): boolean {
    return this.visible;
  }

  // ── Interaction events ───────────────────────────────────────────────────

  /** Notify the controller that the user's pointer has entered the orb. */
  onHoverEnter(): void {
    if (!this.stateMachine.canTransition(OrbState.Hover)) return;
    this.stateMachine.setState(OrbState.Hover);
    this.notify();
  }

  /** Notify the controller that the user's pointer has left the orb. */
  onHoverLeave(): void {
    if (!this.stateMachine.canTransition(OrbState.Idle)) return;
    this.stateMachine.setState(OrbState.Idle);
    this.notify();
  }

  /** Notify the controller that the Glass Prompt has opened. */
  onActivate(): void {
    if (!this.stateMachine.canTransition(OrbState.Active)) return;
    this.stateMachine.setState(OrbState.Active);
    this.notify();
  }

  /** Notify the controller that the Glass Prompt has closed. */
  onDeactivate(): void {
    if (!this.stateMachine.canTransition(OrbState.Idle)) return;
    this.stateMachine.setState(OrbState.Idle);
    this.notify();
  }

  /** Notify the controller that a conversation request has been submitted. */
  onProcessingStart(): void {
    if (!this.stateMachine.canTransition(OrbState.Processing)) return;
    this.stateMachine.setState(OrbState.Processing);
    this.notify();
  }

  /** Notify the controller that streaming has begun. */
  onStreamingStart(): void {
    if (!this.stateMachine.canTransition(OrbState.Streaming)) return;
    this.stateMachine.setState(OrbState.Streaming);
    this.notify();
  }

  /** Notify the controller that the response completed successfully. */
  onStreamingComplete(): void {
    if (!this.stateMachine.canTransition(OrbState.Success)) return;
    this.stateMachine.setState(OrbState.Success);
    this.notify();
  }

  /**
   * Return the orb to Active state after a conversation turn completes.
   * Used when the Glass Prompt remains open and the user can send another message.
   */
  onReturnToActive(): void {
    if (!this.stateMachine.canTransition(OrbState.Active)) return;
    this.stateMachine.setState(OrbState.Active);
    this.notify();
  }

  /** Notify the controller that an error occurred during a request. */
  onError(): void {
    if (!this.stateMachine.canTransition(OrbState.Error)) return;
    this.stateMachine.setState(OrbState.Error);
    this.notify();
  }

  // ── Observable state ─────────────────────────────────────────────────────

  /** Returns a snapshot of the current state. */
  getState(): OrbControllerState {
    return { visible: this.visible, orbState: this.stateMachine.getState() };
  }

  /**
   * Subscribe to state changes. The listener is called synchronously
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
