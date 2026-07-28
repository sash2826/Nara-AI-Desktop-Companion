import { OrbState } from "./OrbState";

/** Called synchronously whenever the state machine transitions to a new state. */
export type OrbStateListener = (state: OrbState) => void;

/** All valid state transitions. Every entry not listed here is rejected. */
const TRANSITIONS = new Map<OrbState, Set<OrbState>>([
  [OrbState.Initializing, new Set<OrbState>([OrbState.Idle])],
  [
    OrbState.Idle,
    new Set<OrbState>([
      OrbState.Hover,
      OrbState.Active,
      OrbState.Processing,
      OrbState.Sleeping,
      OrbState.Notification,
    ]),
  ],
  [OrbState.Hover, new Set<OrbState>([OrbState.Idle, OrbState.Active])],
  [OrbState.Active, new Set<OrbState>([OrbState.Idle, OrbState.Processing])],
  [OrbState.Processing, new Set<OrbState>([OrbState.Streaming, OrbState.Error, OrbState.Idle])],
  [OrbState.Streaming, new Set<OrbState>([OrbState.Success, OrbState.Error, OrbState.Idle])],
  [OrbState.Success, new Set<OrbState>([OrbState.Idle])],
  [OrbState.Notification, new Set<OrbState>([OrbState.Idle])],
  [OrbState.Error, new Set<OrbState>([OrbState.Idle])],
  [OrbState.Sleeping, new Set<OrbState>([OrbState.Idle])],
]);

/**
 * Deterministic state machine for the Living Orb.
 *
 * This is the single source of truth for every orb behavior.
 * All animations, transitions, and interactions must derive from this machine.
 *
 * React integration is handled by OrbController — this class has no React,
 * DOM, or Zustand dependencies.
 */
export class OrbStateMachine {
  private current: OrbState = OrbState.Idle;
  private readonly listeners = new Set<OrbStateListener>();

  /** Returns the current state. */
  getState(): OrbState {
    return this.current;
  }

  /**
   * Returns true if transitioning from the current state to `to` is valid.
   * Transitioning to the same state is never valid.
   */
  canTransition(to: OrbState): boolean {
    return TRANSITIONS.get(this.current)?.has(to) ?? false;
  }

  /**
   * Transition to `to` if the transition is valid.
   *
   * @throws {Error} when the transition is not permitted.
   */
  setState(to: OrbState): void {
    if (!this.canTransition(to)) {
      throw new Error(`OrbStateMachine: invalid transition ${this.current} → ${to}.`);
    }
    this.current = to;
    this.notify();
  }

  /** Reset the machine to the initial Idle state unconditionally. Does not notify listeners. */
  reset(): void {
    this.current = OrbState.Idle;
  }

  /**
   * Subscribe to state changes. The listener is called synchronously after
   * every successful setState().
   *
   * @returns An unsubscribe function.
   */
  subscribe(listener: OrbStateListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.unsubscribe(listener);
    };
  }

  /** Remove a previously registered listener. No-op if the listener is unknown. */
  unsubscribe(listener: OrbStateListener): void {
    this.listeners.delete(listener);
  }

  private notify(): void {
    const state = this.current;
    this.listeners.forEach((l) => l(state));
  }
}
