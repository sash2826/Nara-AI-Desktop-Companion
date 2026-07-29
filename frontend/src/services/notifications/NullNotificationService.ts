import type { Notification, NotificationService } from "./NotificationService";

/**
 * No-op implementation of NotificationService.
 *
 * Used in Phase 00 and Phase 01 while the real notification UI does not exist.
 * All methods are safe to call — nothing is stored, surfaced, or emitted.
 *
 * Replace with a real implementation in Phase 04.
 */
export class NullNotificationService implements NotificationService {
  notify(_notification: Omit<Notification, "id" | "createdAt">): void {
    // Intentional no-op.
  }

  getUnread(): Notification[] {
    return [];
  }

  markRead(_id: string): void {
    // Intentional no-op.
  }

  clearAll(): void {
    // Intentional no-op.
  }
}
