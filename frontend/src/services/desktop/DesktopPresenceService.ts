import type { Overlay } from "./Overlay";
import { OverlayRegistry } from "./OverlayRegistry";

/**
 * Manages the lifecycle of all desktop presence overlays.
 *
 * This service is framework-agnostic: it has no dependency on React, Zustand,
 * DOM APIs, or any other overlay implementation.  React integration is
 * provided exclusively through DesktopPresenceContext.
 *
 * Initialization is idempotent — calling initialize() more than once is safe.
 */
export class DesktopPresenceService {
  private readonly registry = new OverlayRegistry();
  private initialized = false;

  /**
   * Prepare the service for use.  Safe to call multiple times; subsequent
   * calls after the first are no-ops.
   */
  initialize(): void {
    if (this.initialized) {
      return;
    }
    this.initialized = true;
  }

  /**
   * Destroy all registered overlays and reset the service to an
   * uninitialized state.
   */
  async shutdown(): Promise<void> {
    const overlays = this.registry.listAll();
    await Promise.all(overlays.map((o) => o.destroy()));
    this.registry.clear();
    this.initialized = false;
  }

  /**
   * Register an overlay and call its initialize() lifecycle method.
   *
   * @throws {Error} if the service has not been initialized.
   * @throws {Error} if an overlay with the same id is already registered.
   */
  async registerOverlay(overlay: Overlay): Promise<void> {
    this.assertInitialized();
    this.registry.register(overlay);
    await overlay.initialize();
  }

  /**
   * Unregister an overlay by id and call its destroy() lifecycle method.
   * Does nothing if the id is not present.
   */
  async unregisterOverlay(id: string): Promise<void> {
    const overlay = this.registry.get(id);
    if (overlay === undefined) {
      return;
    }
    this.registry.unregister(id);
    await overlay.destroy();
  }

  /**
   * Look up a registered overlay by id.
   *
   * @returns The overlay, or `undefined` if not found.
   */
  getOverlay(id: string): Overlay | undefined {
    return this.registry.get(id);
  }

  /**
   * Return a snapshot of all currently registered overlays.
   */
  listOverlays(): Overlay[] {
    return this.registry.listAll();
  }

  /** True after initialize() has been called and before shutdown() completes. */
  get isInitialized(): boolean {
    return this.initialized;
  }

  private assertInitialized(): void {
    if (!this.initialized) {
      throw new Error(
        "DesktopPresenceService: service must be initialized before registering overlays."
      );
    }
  }
}
