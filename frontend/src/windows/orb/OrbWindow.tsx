import { OrbShell } from "./OrbShell";

/**
 * Root component for the standalone orb WebviewWindow.
 *
 * This is intentionally minimal — all logic lives in OrbShell.
 * The window is 80×340px (orb + overlay space), transparent, no decorations.
 */
export function OrbWindow() {
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
