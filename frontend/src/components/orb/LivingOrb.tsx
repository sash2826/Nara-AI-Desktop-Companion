import { useCallback, useState } from "react";
import type { CSSProperties } from "react";
import { OrbContainer, ORB_SIZE } from "./OrbContainer";
import { OrbIcon } from "./OrbIcon";
import { cn } from "@/lib/utils";
import { OrbState } from "@/services/orb/OrbState";
import { ORB_FOCUS_RING } from "@/theme/orbTheme";

export interface LivingOrbProps {
  /** Current x position of the orb in viewport pixels. */
  x: number;
  /** Current y position of the orb in viewport pixels. */
  y: number;
  /** Current state from OrbStateMachine. Drives CSS classes. Defaults to Idle. */
  orbState?: OrbState;
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
 *   - Apply a CSS class and data attribute reflecting the current OrbState
 *   - Expose click and hover callbacks for parent wiring
 *   - Meet accessibility requirements (label, focus, touch target)
 *
 * This component owns NO service dependencies. Position, drag logic,
 * persistence, and state machine subscription belong to the parent (OrbLayer).
 * All visual tokens (colours, shadows, sizing) come from orbTheme.
 */
export function LivingOrb({
  x,
  y,
  orbState = OrbState.Idle,
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

  const focusStyle: CSSProperties = {
    "--orb-focus-ring": ORB_FOCUS_RING,
  } as CSSProperties;

  return (
    <OrbContainer x={x} y={y} className={className}>
      <button
        type="button"
        aria-label="Nara"
        data-orb-state={orbState}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onMouseDown={onMouseDown}
        onClick={onClick}
        onKeyDown={handleKeyDown}
        style={{ ...focusStyle, width: ORB_SIZE, height: ORB_SIZE }}
        className={cn(
          "relative rounded-full",
          "cursor-grab",
          "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
          "focus-visible:outline-[var(--orb-focus-ring)]",
          `orb-state-${orbState}`
        )}
      >
        <OrbIcon isHovered={isActive} />
      </button>
    </OrbContainer>
  );
}
