import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GlassPromptContainer } from "@/layouts/GlassPromptContainer";
import { useGlassPromptStore } from "@/store/glassPromptStore";
import { OrbControllerContext } from "@/providers/OrbControllerContext";
import type { OrbController } from "@/services/desktop/OrbController";

// Framer Motion: replace animated components with plain divs.
vi.mock("framer-motion", async (importOriginal) => {
  const actual = await importOriginal<typeof import("framer-motion")>();
  return {
    ...actual,
    AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    motion: {
      ...actual.motion,
      div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
        <div {...props}>{children}</div>
      ),
    },
  };
});

// GlassPromptBody pulls in conversation hooks and OrbController — stub both
// so these tests stay focused on the container's own responsibilities.
vi.mock("@/components/glass-prompt/GlassPromptBody", () => ({
  GlassPromptBody: () => <div data-testid="body-stub" />,
}));

/** Minimal OrbController stub — only the methods GlassPromptBody (mocked) needs. */
function makeControllerStub(): OrbController {
  return {
    onActivate: vi.fn(),
    onDeactivate: vi.fn(),
    onProcessingStart: vi.fn(),
    onStreamingStart: vi.fn(),
    onStreamingComplete: vi.fn(),
    onReturnToActive: vi.fn(),
    onError: vi.fn(),
    onHoverEnter: vi.fn(),
    onHoverLeave: vi.fn(),
    getState: vi.fn(() => ({ visible: true, orbState: "Idle" as never })),
    subscribe: vi.fn(() => vi.fn()),
    register: vi.fn(),
    dispose: vi.fn(),
    initialize: vi.fn(),
    show: vi.fn(),
    hide: vi.fn(),
    destroy: vi.fn(),
    isVisible: vi.fn(() => true),
    id: "living-orb",
  } as unknown as OrbController;
}

function renderContainer(controller = makeControllerStub()) {
  return render(
    <OrbControllerContext.Provider value={controller}>
      <GlassPromptContainer />
    </OrbControllerContext.Provider>
  );
}

describe("GlassPromptContainer", () => {
  beforeEach(() => {
    // Reset Zustand store to closed state before each test.
    useGlassPromptStore.setState({ isOpen: false });
  });

  // ── Ctrl+Shift+Space opens ───────────────────────────────────────────────
  // Note: in Vite/test (non-Tauri) the document keydown listener is active.
  // In Tauri production the Rust global-shortcut covers the same toggle.

  it("opens Glass Prompt on Ctrl+Shift+Space when closed", () => {
    renderContainer();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    fireEvent.keyDown(document, { code: "Space", ctrlKey: true, shiftKey: true });

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("closes Glass Prompt on Ctrl+Shift+Space when already open", () => {
    useGlassPromptStore.setState({ isOpen: true });
    renderContainer();
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    fireEvent.keyDown(document, { code: "Space", ctrlKey: true, shiftKey: true });

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("does not open on Ctrl+Space without Shift", () => {
    renderContainer();
    fireEvent.keyDown(document, { code: "Space", ctrlKey: true, shiftKey: false });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("does not open on Shift+Space without Ctrl", () => {
    renderContainer();
    fireEvent.keyDown(document, { code: "Space", ctrlKey: false, shiftKey: true });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  // ── Listener cleanup ──────────────────────────────────────────────────────

  it("removes the keydown listener on unmount", () => {
    const { unmount } = renderContainer();
    unmount();

    // After unmount, the shortcut must not throw and must not change store state.
    fireEvent.keyDown(document, { code: "Space", ctrlKey: true, shiftKey: true });
    expect(useGlassPromptStore.getState().isOpen).toBe(false);
  });
});
