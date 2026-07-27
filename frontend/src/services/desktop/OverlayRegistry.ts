import type { Overlay } from "./Overlay";

/**
 * Maintains the set of overlays known to the DesktopPresenceService.
 *
 * All mutation methods are synchronous; callers are responsible for
 * async lifecycle operations (initialize, destroy) on the overlay itself.
 */
export class OverlayRegistry {
  private readonly overlays = new Map<string, Overlay>();

  /**
   * Add an overlay to the registry.
   *
   * @throws {Error} if an overlay with the same id has already been registered.
   */
  register(overlay: Overlay): void {
    if (this.overlays.has(overlay.id)) {
      throw new Error(`OverlayRegistry: an overlay with id "${overlay.id}" is already registered.`);
    }
    this.overlays.set(overlay.id, overlay);
  }

  /**
   * Remove an overlay from the registry.
   * Does nothing if the id is not present.
   */
  unregister(id: string): void {
    this.overlays.delete(id);
  }

  /**
   * Look up an overlay by id.
   *
   * @returns The overlay, or `undefined` if not found.
   */
  get(id: string): Overlay | undefined {
    return this.overlays.get(id);
  }

  /**
   * Return a snapshot of all currently registered overlays.
   */
  listAll(): Overlay[] {
    return Array.from(this.overlays.values());
  }

  /**
   * Remove every overlay from the registry without calling lifecycle methods.
   * Callers must call `destroy()` on each overlay before clearing if needed.
   */
  clear(): void {
    this.overlays.clear();
  }
}
