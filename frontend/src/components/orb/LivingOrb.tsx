import { useCallback, useState } from "react";
import { OrbContainer, ORB_SIZE } from "./OrbContainer";
import { OrbIcon } from "./OrbIcon";
import { cn } from "@/lib/utils";

export interface LivingOrbProps {
  /** Current x position of the orb in viewport pixels. */
  x: number;
  /** Current y position of the orb in viewport pixels. */
  y: number;
  /** Called when the user clicks or activates the orb via keyboard. */
  onClick?: () => void;
  /** Called when hover or keyboard-focus state changes. */
  onHoverChange?: (hovered: boolean) => void;
  /** Called on primary mouse button down — used by the parent to initiate dragging. */
  onMouseDown?: (e: React.MouseEvent) => void;
  className?: string;
}

/**
 * The Living Orb — the primary visual identity of the Enterprise AI Companion.
 *
 * Responsibilities:
 *   - Render the orb at the given (x, y) position
 *   - Expose click and hover callbacks for parent wiring
 *   - Meet accessibility requirements (role, label, focus, touch target)
 *
 * This component owns NO state beyond hover. Position, drag logic, persistence,
 * and DesktopPresenceService registration belong to the parent or dedicated hooks.
 */
export function LivingOrb({
  x,
  y,
  onClick,
  onHoverChange,
  onMouseDown,
  className,
}: LivingOrbProps) {
  const [isActive, setIsActive] = useState(false);

  const handleMouseEnter = useCallback(() => {
    setIsActive(true);
    onHoverChange?.(true);
  }, [onHoverChange]);

  const handleMouseLeave = useCallback(() => {
    setIsActive(false);
    onHoverChange?.(false);
  }, [onHoverChange]);

  const handleFocus = useCallback(() => {
    setIsActive(true);
    onHoverChange?.(true);
  }, [onHoverChange]);

  const handleBlur = useCallback(() => {
    setIsActive(false);
    onHoverChange?.(false);
  }, [onHoverChange]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onClick?.();
      }
    },
    [onClick]
  );

  return (
    <OrbContainer x={x} y={y} className={className}>
      <button
        type="button"
        aria-label="Enterprise AI Companion"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onMouseDown={onMouseDown}
        onClick={onClick}
        onKeyDown={handleKeyDown}
        style={{ width: ORB_SIZE, height: ORB_SIZE }}
        className={cn(
          "rounded-full",
          "cursor-grab",
          "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary",
          isActive && "ring-2 ring-primary/30"
        )}
      >
        <OrbIcon isHovered={isActive} />
      </button>
    </OrbContainer>
  );
}
