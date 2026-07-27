import { OrbState } from "./OrbState";
import type { OrbStateMachine } from "./OrbStateMachine";

/**
 * Contract for objects that execute state-driven animations on the orb.
 *
 * Every concrete animation driver (CSS, canvas, WebGL, etc.) must implement
 * this interface. The driver is intentionally side-effect-only: it receives
 * the new state and acts on it — it never reads back from the DOM or mutates
 * OrbStateMachine.
 */
export interface OrbAnimationDriver {
  /**
   * Called each time the orb transitions to a new state.
   *
   * Implementations should start or stop the appropriate animation for
   * `state` and cancel any conflicting animation from a prior state.
   */
  onStateChange(state: OrbState): void;
}

/**
 * Subscribes to an OrbStateMachine and delegates state-driven animation
 * work to an OrbAnimationDriver.
 *
 * OrbAnimationController owns the subscription lifecycle — call dispose()
 * to unsubscribe when the controller is no longer needed.
 *
 * This class has no React, DOM, or CSS dependencies. Animation side-effects
 * are fully encapsulated by the injected driver.
 */
export class OrbAnimationController {
  private readonly driver: OrbAnimationDriver;
  private readonly unsubscribe: () => void;

  constructor(machine: OrbStateMachine, driver: OrbAnimationDriver) {
    this.driver = driver;
    this.unsubscribe = machine.subscribe((state) => {
      this.driver.onStateChange(state);
    });
  }

  /**
   * Cancel the subscription to OrbStateMachine.
   *
   * Must be called when the controller is no longer needed to prevent
   * listener leaks. Safe to call multiple times.
   */
  dispose(): void {
    this.unsubscribe();
  }
}
