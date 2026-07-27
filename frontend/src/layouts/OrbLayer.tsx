import { useCallback, useEffect, useState } from "react";
import { LivingOrb } from "@/components/orb/LivingOrb";
import { useOrbPosition } from "@/hooks/useOrbPosition";
import { useOrbDrag } from "@/hooks/useOrbDrag";
import { useDesktopPresence } from "@/hooks/useDesktopPresence";
import { OrbController } from "@/services/desktop/OrbController";

/**
 * A fixed full-screen layer that hosts the Living Orb above all other content.
 *
 * Wires together:
 *  - position persistence (useOrbPosition)
 *  - mouse dragging (useOrbDrag)
 *  - OrbController registration with DesktopPresenceService
 *  - hover/focus → OrbController state forwarding
 */
export function OrbLayer() {
  const { position, setPosition } = useOrbPosition();
  const { handleMouseDown } = useOrbDrag({ position, onPositionChange: setPosition });
  const service = useDesktopPresence();

  const [controller] = useState<OrbController>(() => new OrbController());

  useEffect(() => {
    void controller.register(service);
    return () => {
      void controller.dispose(service);
    };
  }, [controller, service]);

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
          onMouseDown={handleMouseDown}
          onHoverChange={handleHoverChange}
        />
      </div>
    </div>
  );
}
