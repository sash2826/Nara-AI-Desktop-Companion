import { describe, it, expect, beforeEach, vi } from "vitest";
import { OrbController, ORB_OVERLAY_ID } from "@/services/desktop/OrbController";
import { DesktopPresenceService } from "@/services/desktop/DesktopPresenceService";

function makeService(): DesktopPresenceService {
  const service = new DesktopPresenceService();
  service.initialize();
  return service;
}

describe("OrbController", () => {
  let service: DesktopPresenceService;
  let controller: OrbController;

  beforeEach(() => {
    service = makeService();
    controller = new OrbController();
  });

  // ── Identity ──────────────────────────────────────────────────────────────

  it("has the expected stable id", () => {
    expect(controller.id).toBe(ORB_OVERLAY_ID);
  });

  // ── Registration ──────────────────────────────────────────────────────────

  it("registers with DesktopPresenceService", async () => {
    await controller.register(service);
    expect(service.getOverlay(ORB_OVERLAY_ID)).toBe(controller);
  });

  it("is visible after registration (initialize() is called by service)", async () => {
    await controller.register(service);
    expect(controller.isVisible()).toBe(true);
  });

  it("double register is a no-op and does not throw", async () => {
    await controller.register(service);
    await expect(controller.register(service)).resolves.toBeUndefined();
    expect(service.listOverlays()).toHaveLength(1);
  });

  // ── Show / Hide ───────────────────────────────────────────────────────────

  it("show makes the orb visible", async () => {
    await controller.register(service);
    await controller.hide();
    await controller.show();
    expect(controller.isVisible()).toBe(true);
  });

  it("hide makes the orb invisible", async () => {
    await controller.register(service);
    await controller.hide();
    expect(controller.isVisible()).toBe(false);
  });

  it("show is idempotent when already visible", async () => {
    await controller.register(service);
    const listener = vi.fn();
    controller.subscribe(listener);
    listener.mockClear();

    await controller.show();
    expect(listener).not.toHaveBeenCalled();
  });

  it("hide is idempotent when already hidden", async () => {
    await controller.register(service);
    await controller.hide();
    const listener = vi.fn();
    controller.subscribe(listener);
    listener.mockClear();

    await controller.hide();
    expect(listener).not.toHaveBeenCalled();
  });

  // ── Hover interaction ─────────────────────────────────────────────────────

  it("orbState starts as idle", async () => {
    await controller.register(service);
    expect(controller.getState().orbState).toBe("idle");
  });

  it("onHoverEnter transitions state to hover", async () => {
    await controller.register(service);
    controller.onHoverEnter();
    expect(controller.getState().orbState).toBe("hover");
  });

  it("onHoverLeave transitions state back to idle", async () => {
    await controller.register(service);
    controller.onHoverEnter();
    controller.onHoverLeave();
    expect(controller.getState().orbState).toBe("idle");
  });

  it("onHoverEnter is idempotent", async () => {
    await controller.register(service);
    controller.onHoverEnter();
    const listener = vi.fn();
    controller.subscribe(listener);

    controller.onHoverEnter();
    expect(listener).not.toHaveBeenCalled();
  });

  // ── Subscribe / notify ────────────────────────────────────────────────────

  it("subscribe listener is called when visibility changes", async () => {
    await controller.register(service);
    const listener = vi.fn();
    controller.subscribe(listener);

    await controller.hide();
    expect(listener).toHaveBeenCalledWith({ visible: false, orbState: "idle" });
  });

  it("subscribe listener is called when orbState changes", async () => {
    await controller.register(service);
    const listener = vi.fn();
    controller.subscribe(listener);

    controller.onHoverEnter();
    expect(listener).toHaveBeenCalledWith({ visible: true, orbState: "hover" });
  });

  it("unsubscribe stops listener from receiving updates", async () => {
    await controller.register(service);
    const listener = vi.fn();
    const unsubscribe = controller.subscribe(listener);
    unsubscribe();

    await controller.hide();
    expect(listener).not.toHaveBeenCalled();
  });

  it("getState returns a consistent snapshot", async () => {
    await controller.register(service);
    controller.onHoverEnter();
    const state = controller.getState();
    expect(state).toEqual({ visible: true, orbState: "hover" });
  });

  // ── Dispose ───────────────────────────────────────────────────────────────

  it("dispose unregisters the orb from the service", async () => {
    await controller.register(service);
    await controller.dispose(service);
    expect(service.getOverlay(ORB_OVERLAY_ID)).toBeUndefined();
  });

  it("dispose clears all listeners", async () => {
    await controller.register(service);
    const listener = vi.fn();
    controller.subscribe(listener);

    await controller.dispose(service);
    expect(listener).toHaveBeenCalledTimes(1); // the destroy() notification
    listener.mockClear();

    // No further notifications possible after dispose
    expect(listener).not.toHaveBeenCalled();
  });

  it("dispose is safe to call for an already-unregistered id", async () => {
    await expect(controller.dispose(service)).resolves.toBeUndefined();
  });
});
