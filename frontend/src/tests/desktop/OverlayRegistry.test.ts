import { describe, it, expect, beforeEach } from "vitest";
import { OverlayRegistry } from "@/services/desktop/OverlayRegistry";
import type { Overlay } from "@/services/desktop/Overlay";

function makeOverlay(id: string): Overlay {
  return {
    id,
    initialize: async () => {},
    show: async () => {},
    hide: async () => {},
    destroy: async () => {},
    isVisible: () => false,
  };
}

describe("OverlayRegistry", () => {
  let registry: OverlayRegistry;

  beforeEach(() => {
    registry = new OverlayRegistry();
  });

  it("registers an overlay and retrieves it by id", () => {
    const overlay = makeOverlay("orb");
    registry.register(overlay);
    expect(registry.get("orb")).toBe(overlay);
  });

  it("throws when registering a duplicate id", () => {
    const overlay = makeOverlay("orb");
    registry.register(overlay);
    expect(() => registry.register(makeOverlay("orb"))).toThrow(
      'OverlayRegistry: an overlay with id "orb" is already registered.'
    );
  });

  it("returns undefined for an unknown id", () => {
    expect(registry.get("unknown")).toBeUndefined();
  });

  it("unregisters an overlay by id", () => {
    registry.register(makeOverlay("orb"));
    registry.unregister("orb");
    expect(registry.get("orb")).toBeUndefined();
  });

  it("unregister is a no-op for an unknown id", () => {
    expect(() => registry.unregister("ghost")).not.toThrow();
  });

  it("listAll returns all registered overlays", () => {
    const a = makeOverlay("a");
    const b = makeOverlay("b");
    registry.register(a);
    registry.register(b);
    expect(registry.listAll()).toHaveLength(2);
    expect(registry.listAll()).toEqual(expect.arrayContaining([a, b]));
  });

  it("listAll returns an empty array when no overlays are registered", () => {
    expect(registry.listAll()).toEqual([]);
  });

  it("clear removes all overlays", () => {
    registry.register(makeOverlay("a"));
    registry.register(makeOverlay("b"));
    registry.clear();
    expect(registry.listAll()).toEqual([]);
  });
});
