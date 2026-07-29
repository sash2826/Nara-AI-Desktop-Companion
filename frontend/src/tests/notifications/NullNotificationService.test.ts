import { describe, it, expect } from "vitest";
import { NullNotificationService } from "@/services/notifications/NullNotificationService";

describe("NullNotificationService", () => {
  it("notify() does not throw", () => {
    const svc = new NullNotificationService();
    expect(() => svc.notify({ title: "Test", message: "hello", severity: "info" })).not.toThrow();
  });

  it("getUnread() always returns an empty array", () => {
    const svc = new NullNotificationService();
    svc.notify({ title: "Test", message: "hello", severity: "info" });
    expect(svc.getUnread()).toEqual([]);
  });

  it("markRead() does not throw", () => {
    const svc = new NullNotificationService();
    expect(() => svc.markRead("nonexistent-id")).not.toThrow();
  });

  it("clearAll() does not throw", () => {
    const svc = new NullNotificationService();
    expect(() => svc.clearAll()).not.toThrow();
  });
});
