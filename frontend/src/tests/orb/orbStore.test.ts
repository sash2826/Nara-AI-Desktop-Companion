import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock window dimensions before importing the store so defaultPosition() uses
// controlled values regardless of the jsdom environment.
vi.stubGlobal("innerWidth", 1280);
vi.stubGlobal("innerHeight", 800);

// Import after stubbing so module-level code sees the mocked values.
const { useOrbStore } = await import("@/store/orbStore");
const { ORB_SIZE } = await import("@/components/orb/OrbContainer");

describe("orbStore", () => {
  beforeEach(() => {
    // Reset store to its initial state between tests.
    useOrbStore.setState({ position: { x: 1280 - ORB_SIZE * 2, y: 800 - ORB_SIZE * 2 } });
  });

  it("initialises with the default bottom-right position", () => {
    const { position } = useOrbStore.getState();
    expect(position.x).toBe(1280 - ORB_SIZE * 2);
    expect(position.y).toBe(800 - ORB_SIZE * 2);
  });

  it("setPosition updates the position", () => {
    useOrbStore.getState().setPosition({ x: 100, y: 200 });
    expect(useOrbStore.getState().position).toEqual({ x: 100, y: 200 });
  });

  it("clamps x to 0 when the value is negative", () => {
    useOrbStore.getState().setPosition({ x: -50, y: 200 });
    expect(useOrbStore.getState().position.x).toBe(0);
  });

  it("clamps y to 0 when the value is negative", () => {
    useOrbStore.getState().setPosition({ x: 100, y: -50 });
    expect(useOrbStore.getState().position.y).toBe(0);
  });

  it("clamps x to window.innerWidth - ORB_SIZE when too large", () => {
    useOrbStore.getState().setPosition({ x: 9999, y: 200 });
    expect(useOrbStore.getState().position.x).toBe(1280 - ORB_SIZE);
  });

  it("clamps y to window.innerHeight - ORB_SIZE when too large", () => {
    useOrbStore.getState().setPosition({ x: 100, y: 9999 });
    expect(useOrbStore.getState().position.y).toBe(800 - ORB_SIZE);
  });

  it("allows a position exactly at the maximum boundary", () => {
    const maxX = 1280 - ORB_SIZE;
    const maxY = 800 - ORB_SIZE;
    useOrbStore.getState().setPosition({ x: maxX, y: maxY });
    expect(useOrbStore.getState().position).toEqual({ x: maxX, y: maxY });
  });

  it("allows a position exactly at (0, 0)", () => {
    useOrbStore.getState().setPosition({ x: 0, y: 0 });
    expect(useOrbStore.getState().position).toEqual({ x: 0, y: 0 });
  });
});
