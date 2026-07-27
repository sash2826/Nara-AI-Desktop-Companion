import { useCallback, useRef } from "react";
import type { OrbPosition } from "@/store/orbStore";

interface DragOrigin {
  /** Pointer clientX at drag start. */
  pointerX: number;
  /** Pointer clientY at drag start. */
  pointerY: number;
  /** Orb x at drag start. */
  orbX: number;
  /** Orb y at drag start. */
  orbY: number;
}

interface UseOrbDragOptions {
  position: OrbPosition;
  onPositionChange: (position: OrbPosition) => void;
}

interface UseOrbDragResult {
  /** Attach to the orb element's onMouseDown. */
  handleMouseDown: (e: React.MouseEvent) => void;
  /** True while a drag is in progress. */
  isDragging: boolean;
}

/**
 * Provides mouse-drag behaviour for a positioned element.
 *
 * Listener pairs (pointermove + pointerup) are created as plain closures inside
 * handleMouseDown on each drag start, then removed on pointerup.  Keeping them
 * local eliminates the circular useCallback dependency that would arise from
 * handleMouseUp referencing handleMouseMove (and vice-versa for cleanup).
 *
 * Position clamping is handled by the store's setPosition; this hook is only
 * responsible for computing deltas and forwarding them.
 */
export function useOrbDrag({ position, onPositionChange }: UseOrbDragOptions): UseOrbDragResult {
  const origin = useRef<DragOrigin | null>(null);
  const dragging = useRef(false);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      e.preventDefault();

      dragging.current = true;
      origin.current = {
        pointerX: e.clientX,
        pointerY: e.clientY,
        orbX: position.x,
        orbY: position.y,
      };

      function onMove(ev: PointerEvent) {
        if (!origin.current) return;
        const dx = ev.clientX - origin.current.pointerX;
        const dy = ev.clientY - origin.current.pointerY;
        onPositionChange({
          x: origin.current.orbX + dx,
          y: origin.current.orbY + dy,
        });
      }

      function onUp() {
        dragging.current = false;
        origin.current = null;
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onUp);
      }

      document.addEventListener("pointermove", onMove);
      document.addEventListener("pointerup", onUp);
    },
    [position.x, position.y, onPositionChange]
  );

  return {
    handleMouseDown,
    get isDragging() {
      return dragging.current;
    },
  };
}
