import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LivingOrb } from "@/components/orb/LivingOrb";
import { OrbState } from "@/services/orb/OrbState";

function renderOrb(props: Partial<React.ComponentProps<typeof LivingOrb>> = {}) {
  return render(<LivingOrb x={100} y={100} {...props} />);
}

describe("LivingOrb", () => {
  // ── Rendering ──────────────────────────────────────────────────────────────

  it("renders without crashing", () => {
    renderOrb();
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("has the expected accessible label", () => {
    renderOrb();
    expect(screen.getByRole("button", { name: "Enterprise AI Companion" })).toBeInTheDocument();
  });

  // ── OrbState CSS classes ───────────────────────────────────────────────────

  it("applies orb-state-idle class by default", () => {
    renderOrb();
    expect(screen.getByRole("button")).toHaveClass("orb-state-idle");
  });

  it("applies the correct class for each OrbState", () => {
    const states = Object.values(OrbState);
    for (const state of states) {
      const { unmount } = renderOrb({ orbState: state });
      expect(screen.getByRole("button")).toHaveClass(`orb-state-${state}`);
      unmount();
    }
  });

  it("sets data-orb-state attribute to the current state", () => {
    renderOrb({ orbState: OrbState.Thinking });
    expect(screen.getByRole("button")).toHaveAttribute("data-orb-state", OrbState.Thinking);
  });

  it("updates data-orb-state when orbState prop changes", () => {
    const { rerender } = renderOrb({ orbState: OrbState.Idle });
    expect(screen.getByRole("button")).toHaveAttribute("data-orb-state", OrbState.Idle);

    rerender(<LivingOrb x={100} y={100} orbState={OrbState.Hover} />);
    expect(screen.getByRole("button")).toHaveAttribute("data-orb-state", OrbState.Hover);
  });

  // ── Hover interaction ─────────────────────────────────────────────────────

  it("calls onHoverChange(true) on mouseenter", () => {
    const onHoverChange = vi.fn();
    renderOrb({ onHoverChange });
    fireEvent.mouseEnter(screen.getByRole("button"));
    expect(onHoverChange).toHaveBeenCalledWith(true);
  });

  it("calls onHoverChange(false) on mouseleave", () => {
    const onHoverChange = vi.fn();
    renderOrb({ onHoverChange });
    fireEvent.mouseEnter(screen.getByRole("button"));
    fireEvent.mouseLeave(screen.getByRole("button"));
    expect(onHoverChange).toHaveBeenLastCalledWith(false);
  });

  it("calls onHoverChange exactly once per mouseenter", () => {
    const onHoverChange = vi.fn();
    renderOrb({ onHoverChange });
    fireEvent.mouseEnter(screen.getByRole("button"));
    expect(onHoverChange).toHaveBeenCalledTimes(1);
  });

  // ── Keyboard focus ────────────────────────────────────────────────────────

  it("calls onHoverChange(true) on focus", () => {
    const onHoverChange = vi.fn();
    renderOrb({ onHoverChange });
    fireEvent.focus(screen.getByRole("button"));
    expect(onHoverChange).toHaveBeenCalledWith(true);
  });

  it("calls onHoverChange(false) on blur", () => {
    const onHoverChange = vi.fn();
    renderOrb({ onHoverChange });
    fireEvent.focus(screen.getByRole("button"));
    fireEvent.blur(screen.getByRole("button"));
    expect(onHoverChange).toHaveBeenLastCalledWith(false);
  });

  // ── Click / keyboard activation ───────────────────────────────────────────

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    renderOrb({ onClick });
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("calls onClick on Enter key", () => {
    const onClick = vi.fn();
    renderOrb({ onClick });
    fireEvent.keyDown(screen.getByRole("button"), { key: "Enter" });
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("calls onClick on Space key", () => {
    const onClick = vi.fn();
    renderOrb({ onClick });
    fireEvent.keyDown(screen.getByRole("button"), { key: " " });
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("does not call onClick on unrelated keys", () => {
    const onClick = vi.fn();
    renderOrb({ onClick });
    fireEvent.keyDown(screen.getByRole("button"), { key: "Tab" });
    expect(onClick).not.toHaveBeenCalled();
  });

  // ── Mouse down forwarding ─────────────────────────────────────────────────

  it("forwards onMouseDown to the button", () => {
    const onMouseDown = vi.fn();
    renderOrb({ onMouseDown });
    fireEvent.mouseDown(screen.getByRole("button"));
    expect(onMouseDown).toHaveBeenCalledOnce();
  });

  // ── Cleanup (no prop) safety ──────────────────────────────────────────────

  it("does not throw on mouseenter when onHoverChange is not provided", () => {
    renderOrb();
    expect(() => fireEvent.mouseEnter(screen.getByRole("button"))).not.toThrow();
  });

  it("does not throw on click when onClick is not provided", () => {
    renderOrb();
    expect(() => fireEvent.click(screen.getByRole("button"))).not.toThrow();
  });
});
