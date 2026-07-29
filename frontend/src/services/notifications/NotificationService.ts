/**
 * NotificationService — interface for surfacing in-app notifications to the user.
 *
 * In Phase 00 / Phase 01 this is a stub: nothing is surfaced. The interface is
 * defined now so that components and services can declare a dependency on it
 * without coupling to an implementation that does not yet exist.
 *
 * The Living Orb's `Notification` state (OrbState) is designed to pair with
 * this service: when `notify()` is called, the concrete implementation will
 * also dispatch a `NotificationReceived` event to the OrbController.
 *
 * Phase 04 (background tasks and automation) will introduce the full
 * implementation including toast overlays, notification history, and the
 * orb integration.
 */

export interface Notification {
  /** Unique identifier — callers may use crypto.randomUUID(). */
  readonly id: string;
  readonly title: string;
  readonly message: string;
  /** ISO 8601 timestamp — set by the service, not the caller. */
  readonly createdAt: string;
  readonly severity: "info" | "warning" | "error";
}

export interface NotificationService {
  /**
   * Surfaces a notification. The concrete implementation determines how it is
   * displayed (toast, orb state change, notification tray, etc.).
   */
  notify(notification: Omit<Notification, "id" | "createdAt">): void;

  /** Returns all unread notifications in descending creation order. */
  getUnread(): Notification[];

  /** Marks a notification as read so it no longer appears in `getUnread()`. */
  markRead(id: string): void;

  /** Clears all notifications. */
  clearAll(): void;
}
