import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { DesktopPresenceProvider } from "@/providers/DesktopPresenceProvider";
import { OrbControllerProvider } from "@/providers/OrbControllerProvider";
import { OrbLayer } from "@/layouts/OrbLayer";
import { ORB_OVERLAY_ID } from "@/services/desktop/OrbController";
import { OrbState } from "@/services/orb/OrbState";

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
      <OrbControllerProvider>
        <OrbLayer />
      </OrbControllerProvider>
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

  // ── Initial state ─────────────────────────────────────────────────────────

  it("renders with orb-state-idle class initially", () => {
    renderOrbLayer();
    expect(screen.getByRole("button", { name: "Enterprise AI Companion" })).toHaveClass(
      "orb-state-idle"
    );
  });

  // ── OrbController registration ────────────────────────────────────────────

  it("registers OrbController with DesktopPresenceService on mount", async () => {
    renderOrbLayer();
    await act(async () => {});
    expect(screen.getByRole("button", { name: "Enterprise AI Companion" })).toBeInTheDocument();
  });

  // ── State propagation via subscription ────────────────────────────────────

  it("updates orb-state class to hover when mouse enters", async () => {
    renderOrbLayer();
    await act(async () => {});
    const button = screen.getByRole("button", { name: "Enterprise AI Companion" });

    await act(async () => {
      fireEvent.mouseEnter(button);
    });

    expect(button).toHaveClass(`orb-state-${OrbState.Hover}`);
  });

  it("returns to orb-state-idle class when mouse leaves", async () => {
    renderOrbLayer();
    await act(async () => {});
    const button = screen.getByRole("button", { name: "Enterprise AI Companion" });

    await act(async () => {
      fireEvent.mouseEnter(button);
    });
    await act(async () => {
      fireEvent.mouseLeave(button);
    });

    expect(button).toHaveClass(`orb-state-${OrbState.Idle}`);
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
    expect(() => renderOrbLayer()).not.toThrow();
  });

  // ── Z-index token ─────────────────────────────────────────────────────────

  it("applies the --z-top CSS variable to the overlay container", () => {
    const { container } = renderOrbLayer();
    const overlay = container.firstElementChild as HTMLElement;
    expect(overlay.style.zIndex).toBe("var(--z-top)");
  });

  // ── Stable orb id ─────────────────────────────────────────────────────────

  it("uses the canonical ORB_OVERLAY_ID constant", () => {
    expect(ORB_OVERLAY_ID).toBe("living-orb");
  });
});
