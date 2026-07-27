import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { OrbPosition } from "@/store/orbStore";
import { useOrbDrag } from "@/hooks/useOrbDrag";

function makePointerEvent(type: string, init: Partial<PointerEvent> = {}): PointerEvent {
  return new PointerEvent(type, { bubbles: true, cancelable: true, ...init });
}

describe("useOrbDrag", () => {
  // mockFn retains the mock type so mockClear / toHaveBeenCalled work.
  // onPositionChange is the typed alias passed to the hook.
  let mockFn: ReturnType<typeof vi.fn>;
  let onPositionChange: (position: OrbPosition) => void;

  beforeEach(() => {
    mockFn = vi.fn();
    onPositionChange = mockFn as (position: OrbPosition) => void;
  });

  afterEach(() => {
    // Ensure document listeners don't leak between tests.
    document.dispatchEvent(makePointerEvent("pointerup"));
  });

  it("does not call onPositionChange before any drag starts", () => {
    renderHook(() => useOrbDrag({ position: { x: 100, y: 100 }, onPositionChange }));
    expect(mockFn).not.toHaveBeenCalled();
  });

  it("calls onPositionChange when the pointer moves after mousedown", () => {
    const { result } = renderHook(() =>
      useOrbDrag({ position: { x: 100, y: 100 }, onPositionChange })
    );

    act(() => {
      // Simulate mousedown at (150, 150).
      const e = {
        button: 0,
        clientX: 150,
        clientY: 150,
        preventDefault: vi.fn(),
      } as unknown as React.MouseEvent;
      result.current.handleMouseDown(e);
    });

    act(() => {
      // Move pointer to (200, 180) — delta (+50, +30).
      document.dispatchEvent(makePointerEvent("pointermove", { clientX: 200, clientY: 180 }));
    });

    expect(mockFn).toHaveBeenCalledWith({ x: 150, y: 130 });
  });

  it("stops calling onPositionChange after pointerup", () => {
    const { result } = renderHook(() =>
      useOrbDrag({ position: { x: 100, y: 100 }, onPositionChange })
    );

    act(() => {
      const e = {
        button: 0,
        clientX: 150,
        clientY: 150,
        preventDefault: vi.fn(),
      } as unknown as React.MouseEvent;
      result.current.handleMouseDown(e);
    });

    act(() => {
      document.dispatchEvent(makePointerEvent("pointerup"));
    });

    mockFn.mockClear();

    act(() => {
      document.dispatchEvent(makePointerEvent("pointermove", { clientX: 300, clientY: 300 }));
    });

    expect(mockFn).not.toHaveBeenCalled();
  });

  it("ignores non-primary mouse button presses", () => {
    const { result } = renderHook(() =>
      useOrbDrag({ position: { x: 100, y: 100 }, onPositionChange })
    );

    act(() => {
      // button: 2 = right click
      const e = {
        button: 2,
        clientX: 150,
        clientY: 150,
        preventDefault: vi.fn(),
      } as unknown as React.MouseEvent;
      result.current.handleMouseDown(e);
    });

    act(() => {
      document.dispatchEvent(makePointerEvent("pointermove", { clientX: 200, clientY: 200 }));
    });

    expect(mockFn).not.toHaveBeenCalled();
  });

  it("computes the correct position delta for multiple moves", () => {
    const { result } = renderHook(() =>
      useOrbDrag({ position: { x: 50, y: 60 }, onPositionChange })
    );

    act(() => {
      const e = {
        button: 0,
        clientX: 100,
        clientY: 100,
        preventDefault: vi.fn(),
      } as unknown as React.MouseEvent;
      result.current.handleMouseDown(e);
    });

    act(() => {
      document.dispatchEvent(makePointerEvent("pointermove", { clientX: 110, clientY: 120 }));
    });
    expect(mockFn).toHaveBeenLastCalledWith({ x: 60, y: 80 });

    act(() => {
      document.dispatchEvent(makePointerEvent("pointermove", { clientX: 90, clientY: 95 }));
    });
    expect(mockFn).toHaveBeenLastCalledWith({ x: 40, y: 55 });
  });

  it("calls preventDefault on mousedown to prevent text selection", () => {
    const { result } = renderHook(() => useOrbDrag({ position: { x: 0, y: 0 }, onPositionChange }));

    const preventDefault = vi.fn();
    act(() => {
      const e = {
        button: 0,
        clientX: 0,
        clientY: 0,
        preventDefault,
      } as unknown as React.MouseEvent;
      result.current.handleMouseDown(e);
    });

    expect(preventDefault).toHaveBeenCalledOnce();
  });
});
