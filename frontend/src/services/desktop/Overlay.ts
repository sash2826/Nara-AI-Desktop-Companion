/**
 * An Overlay represents a discrete desktop UI surface managed by the
 * DesktopPresenceService.  Implementations (Living Orb, Glass Prompt, etc.)
 * are introduced in later tasks; only the contract is defined here.
 */
export interface Overlay {
  /** Unique identifier used for registry lookup. */
  readonly id: string;

  /** Called once after registration to allow the overlay to allocate resources. */
  initialize(): Promise<void>;

  /** Make the overlay visible. */
  show(): Promise<void>;

  /** Hide the overlay without destroying it. */
  hide(): Promise<void>;

  /** Release all resources; the overlay must not be used after this call. */
  destroy(): Promise<void>;

  /** Returns true while the overlay is in the visible state. */
  isVisible(): boolean;
}
