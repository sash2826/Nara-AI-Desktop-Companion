import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GlassPrompt } from "@/components/glass-prompt/GlassPrompt";

// Framer Motion: replace animated components with plain divs so tests
// can inspect the DOM without waiting for animation frames.
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

function renderPrompt(isOpen: boolean, onClose: () => void = vi.fn()) {
  return render(
    <GlassPrompt isOpen={isOpen} onClose={onClose}>
      <input data-testid="inner-input" />
    </GlassPrompt>
  );
}

describe("GlassPrompt", () => {
  let onClose: () => void;

  beforeEach(() => {
    onClose = vi.fn();
  });

  // ── Visibility ───────────────────────────────────────────────────────────

  it("renders content when isOpen is true", () => {
    renderPrompt(true, onClose);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("renders nothing when isOpen is false", () => {
    renderPrompt(false, onClose);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  // ── Escape key ───────────────────────────────────────────────────────────

  it("calls onClose when Escape is pressed", () => {
    renderPrompt(true, onClose);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("does not call onClose for other keys", () => {
    renderPrompt(true, onClose);
    fireEvent.keyDown(window, { key: "Enter" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("does not listen for Escape when closed", () => {
    renderPrompt(false, onClose);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).not.toHaveBeenCalled();
  });

  // ── Backdrop click ───────────────────────────────────────────────────────

  it("calls onClose when the backdrop is clicked", () => {
    renderPrompt(true, onClose);
    fireEvent.click(screen.getByRole("dialog"));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("does not call onClose when the panel itself is clicked", () => {
    renderPrompt(true, onClose);
    // Click the inner input (inside the panel, not the backdrop)
    fireEvent.click(screen.getByTestId("inner-input"));
    expect(onClose).not.toHaveBeenCalled();
  });

  // ── Close button ─────────────────────────────────────────────────────────

  it("renders a close button", () => {
    renderPrompt(true, onClose);
    expect(screen.getByRole("button", { name: /close/i })).toBeInTheDocument();
  });

  it("calls onClose when the close button is clicked", () => {
    renderPrompt(true, onClose);
    fireEvent.click(screen.getByRole("button", { name: /close/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  // ── Accessibility ────────────────────────────────────────────────────────

  it("has role dialog and aria-label", () => {
    renderPrompt(true, onClose);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-label", "AI Companion prompt");
  });

  it("has aria-modal true", () => {
    renderPrompt(true, onClose);
    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
  });
});
