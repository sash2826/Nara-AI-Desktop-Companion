import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { DesktopPresenceProvider } from "@/providers/DesktopPresenceProvider";
import { OrbLayer } from "@/layouts/OrbLayer";
import { ORB_OVERLAY_ID } from "@/services/desktop/OrbController";

// Stub window dimensions so orbStore.defaultPosition() returns a deterministic value.
vi.stubGlobal("innerWidth", 1280);
vi.stubGlobal("innerHeight", 800);

// Stub localStorage to avoid "not implemented" warnings from jsdom.
const localStorageStore: Record<string, string> = {};
vi.stubGlobal("localStorage", {
  getItem: (key: string) => localStorageStore[key] ?? null,
  setItem: (key: string, value: string) => {
    localStorageStore[key] = value;
  },
  removeItem: (key: string) => {
    delete localStorageStore[key];
  },
  clear: () => Object.keys(localStorageStore).forEach((k) => delete localStorageStore[k]),
});

function renderOrbLayer() {
  return render(
    <DesktopPresenceProvider>
      <OrbLayer />
    </DesktopPresenceProvider>
  );
}

describe("OrbLayer", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  // ── Rendering ──────────────────────────────────────────────────────────────

  it("renders the Living Orb button", () => {
    renderOrbLayer();
    expect(screen.getByRole("button", { name: "Enterprise AI Companion" })).toBeInTheDocument();
  });

  // ── OrbController registration ────────────────────────────────────────────

  it("registers OrbController with DesktopPresenceService on mount", async () => {
    renderOrbLayer();
    // Registration is async (useEffect); flush pending effects.
    await act(async () => {});
    // Successful registration makes the orb visible, so the button is present.
    expect(screen.getByRole("button", { name: "Enterprise AI Companion" })).toBeInTheDocument();
  });

  // ── Hover forwarding ──────────────────────────────────────────────────────

  it("does not throw when the orb is hovered", async () => {
    renderOrbLayer();
    await act(async () => {});
    const button = screen.getByRole("button", { name: "Enterprise AI Companion" });
    expect(() => fireEvent.mouseEnter(button)).not.toThrow();
  });

  it("does not throw when the orb loses hover", async () => {
    renderOrbLayer();
    await act(async () => {});
    const button = screen.getByRole("button", { name: "Enterprise AI Companion" });
    fireEvent.mouseEnter(button);
    expect(() => fireEvent.mouseLeave(button)).not.toThrow();
  });

  // ── Unmount cleanup ───────────────────────────────────────────────────────

  it("unmounts cleanly without throwing", () => {
    const { unmount } = renderOrbLayer();
    expect(() => unmount()).not.toThrow();
  });

  it("re-mounts after unmount without a duplicate-registration error", async () => {
    const { unmount } = renderOrbLayer();
    await act(async () => {});
    unmount();
    // After unmount the OrbController is unregistered. A fresh tree must not throw.
    expect(() => renderOrbLayer()).not.toThrow();
  });

  // ── Z-index token ─────────────────────────────────────────────────────────

  it("applies the --z-top CSS variable to the overlay container", () => {
    const { container } = renderOrbLayer();
    // The first div child of the render root is the fixed overlay layer.
    const overlay = container.firstElementChild as HTMLElement;
    expect(overlay.style.zIndex).toBe("var(--z-top)");
  });

  // ── Stable orb id ─────────────────────────────────────────────────────────

  it("uses the canonical ORB_OVERLAY_ID constant", () => {
    expect(ORB_OVERLAY_ID).toBe("living-orb");
  });
});
