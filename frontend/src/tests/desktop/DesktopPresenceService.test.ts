import { describe, it, expect, beforeEach, vi } from "vitest";
import { DesktopPresenceService } from "@/services/desktop/DesktopPresenceService";
import type { Overlay } from "@/services/desktop/Overlay";

function makeOverlay(id: string): Overlay {
  return {
    id,
    initialize: vi.fn(async () => {}),
    show: vi.fn(async () => {}),
    hide: vi.fn(async () => {}),
    destroy: vi.fn(async () => {}),
    isVisible: vi.fn(() => false),
  };
}

describe("DesktopPresenceService", () => {
  let service: DesktopPresenceService;

  beforeEach(() => {
    service = new DesktopPresenceService();
  });

  // ── Initialization ───────────────────────────────────────────────────────

  it("is not initialized before initialize() is called", () => {
    expect(service.isInitialized).toBe(false);
  });

  it("is initialized after initialize() is called", () => {
    service.initialize();
    expect(service.isInitialized).toBe(true);
  });

  it("double initialize() does not throw and remains initialized", () => {
    service.initialize();
    expect(() => service.initialize()).not.toThrow();
    expect(service.isInitialized).toBe(true);
  });

  // ── Shutdown ─────────────────────────────────────────────────────────────

  it("shutdown resets initialized state", async () => {
    service.initialize();
    await service.shutdown();
    expect(service.isInitialized).toBe(false);
  });

  it("shutdown destroys all registered overlays", async () => {
    service.initialize();
    const a = makeOverlay("a");
    const b = makeOverlay("b");
    await service.registerOverlay(a);
    await service.registerOverlay(b);

    await service.shutdown();

    expect(a.destroy).toHaveBeenCalledOnce();
    expect(b.destroy).toHaveBeenCalledOnce();
  });

  it("shutdown removes all overlays so listOverlays is empty afterward", async () => {
    service.initialize();
    await service.registerOverlay(makeOverlay("a"));
    await service.shutdown();
    expect(service.listOverlays()).toEqual([]);
  });

  // ── Register overlay ─────────────────────────────────────────────────────

  it("registerOverlay calls initialize() on the overlay", async () => {
    service.initialize();
    const overlay = makeOverlay("orb");
    await service.registerOverlay(overlay);
    expect(overlay.initialize).toHaveBeenCalledOnce();
  });

  it("registerOverlay throws if service is not initialized", async () => {
    const overlay = makeOverlay("orb");
    await expect(service.registerOverlay(overlay)).rejects.toThrow(
      "DesktopPresenceService: service must be initialized before registering overlays."
    );
  });

  it("registerOverlay throws on duplicate id", async () => {
    service.initialize();
    await service.registerOverlay(makeOverlay("orb"));
    await expect(service.registerOverlay(makeOverlay("orb"))).rejects.toThrow(
      'OverlayRegistry: an overlay with id "orb" is already registered.'
    );
  });

  // ── Unregister overlay ───────────────────────────────────────────────────

  it("unregisterOverlay calls destroy() on the overlay", async () => {
    service.initialize();
    const overlay = makeOverlay("orb");
    await service.registerOverlay(overlay);
    await service.unregisterOverlay("orb");
    expect(overlay.destroy).toHaveBeenCalledOnce();
  });

  it("unregisterOverlay removes the overlay from the registry", async () => {
    service.initialize();
    await service.registerOverlay(makeOverlay("orb"));
    await service.unregisterOverlay("orb");
    expect(service.getOverlay("orb")).toBeUndefined();
  });

  it("unregisterOverlay is a no-op for an unknown id", async () => {
    service.initialize();
    await expect(service.unregisterOverlay("ghost")).resolves.toBeUndefined();
  });

  // ── Lookup and list ──────────────────────────────────────────────────────

  it("getOverlay returns the overlay for a known id", async () => {
    service.initialize();
    const overlay = makeOverlay("orb");
    await service.registerOverlay(overlay);
    expect(service.getOverlay("orb")).toBe(overlay);
  });

  it("getOverlay returns undefined for an unknown id", () => {
    service.initialize();
    expect(service.getOverlay("missing")).toBeUndefined();
  });

  it("listOverlays returns all registered overlays", async () => {
    service.initialize();
    const a = makeOverlay("a");
    const b = makeOverlay("b");
    await service.registerOverlay(a);
    await service.registerOverlay(b);
    expect(service.listOverlays()).toHaveLength(2);
    expect(service.listOverlays()).toEqual(expect.arrayContaining([a, b]));
  });

  it("listOverlays returns an empty array when no overlays are registered", () => {
    service.initialize();
    expect(service.listOverlays()).toEqual([]);
  });
});
