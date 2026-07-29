import { useCallback, useEffect, useState } from "react";
import { LivingOrb } from "@/components/orb/LivingOrb";
import { useOrbPosition } from "@/hooks/useOrbPosition";
import { useOrbDrag } from "@/hooks/useOrbDrag";
import { OrbState } from "@/services/orb/OrbState";
import { useGlassPromptStore } from "@/store/glassPromptStore";
import { useOrbController } from "@/hooks/useOrbController";

/**
 * A fixed full-screen layer that hosts the Living Orb above all other content.
 *
 * Wires together:
 *  - position persistence (useOrbPosition)
 *  - mouse dragging (useOrbDrag)
 *  - OrbStateMachine subscription → orbState prop forwarded to LivingOrb
 *  - hover/focus → OrbController state forwarding
 *
 * OrbController is provided by OrbControllerProvider higher in the tree.
 */
export function OrbLayer() {
  const { position, setPosition } = useOrbPosition();
  const { handleMouseDown } = useOrbDrag({ position, onPositionChange: setPosition });
  const controller = useOrbController();
  const { isOpen, open, close } = useGlassPromptStore();

  const [orbState, setOrbState] = useState<OrbState>(OrbState.Idle);

  useEffect(() => {
    const unsubscribe = controller.subscribe((snapshot) => {
      setOrbState(snapshot.orbState);
    });
    return unsubscribe;
  }, [controller]);

  // Sync orb Active state with Glass Prompt open/closed state
  useEffect(() => {
    if (isOpen) {
      controller.onActivate();
    } else {
      controller.onDeactivate();
    }
  }, [isOpen, controller]);

  const handleClick = useCallback(() => {
    if (isOpen) {
      close();
    } else {
      open();
    }
  }, [isOpen, open, close]);

  const handleHoverChange = useCallback(
    (hovered: boolean) => {
      if (hovered) {
        controller.onHoverEnter();
      } else {
        controller.onHoverLeave();
      }
    },
    [controller]
  );

  return (
    <div className="pointer-events-none fixed inset-0" style={{ zIndex: "var(--z-top)" }}>
      <div className="pointer-events-auto">
        <LivingOrb
          x={position.x}
          y={position.y}
          orbState={orbState}
          onMouseDown={handleMouseDown}
          onHoverChange={handleHoverChange}
          onClick={handleClick}
        />
      </div>
    </div>
  );
}
