import { useCallback, useEffect, useState } from "react";
import { LivingOrb } from "@/components/orb/LivingOrb";
import { useOrbPosition } from "@/hooks/useOrbPosition";
import { useOrbDrag } from "@/hooks/useOrbDrag";
import { useDesktopPresence } from "@/hooks/useDesktopPresence";
import { OrbController } from "@/services/desktop/OrbController";
import { OrbState } from "@/services/orb/OrbState";
import { useGlassPromptStore } from "@/store/glassPromptStore";

/**
 * A fixed full-screen layer that hosts the Living Orb above all other content.
 *
 * Wires together:
 *  - position persistence (useOrbPosition)
 *  - mouse dragging (useOrbDrag)
 *  - OrbController registration with DesktopPresenceService
 *  - OrbStateMachine subscription → orbState prop forwarded to LivingOrb
 *  - hover/focus → OrbController state forwarding
 */
export function OrbLayer() {
  const { position, setPosition } = useOrbPosition();
  const { handleMouseDown } = useOrbDrag({ position, onPositionChange: setPosition });
  const service = useDesktopPresence();
  const { isOpen, open, close } = useGlassPromptStore();

  const [controller] = useState<OrbController>(() => new OrbController());
  const [orbState, setOrbState] = useState<OrbState>(OrbState.Idle);

  useEffect(() => {
    void controller.register(service);
    return () => {
      void controller.dispose(service);
    };
  }, [controller, service]);

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
