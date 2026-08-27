import { useEffect } from "react";
import { OrbShell } from "./OrbShell";

/**
 * Root component for the standalone orb WebviewWindow.
 * Clamps overflow so the transparent window never shows scrollbars.
 */
export function OrbWindow() {
  useEffect(() => {
    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";
    document.body.style.margin = "0";
    document.body.style.padding = "0";
  }, []);

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: "transparent",
        overflow: "visible",
        position: "relative",
      }}
    >
      <OrbShell />
    </div>
  );
}
