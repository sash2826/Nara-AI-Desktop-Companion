import type { CSSProperties } from "react";
import {
  ORB_SPHERE_SIZE,
  ORB_SPHERE_INSET,
  ORB_GRADIENT_FROM,
  ORB_GRADIENT_MID,
  ORB_GRADIENT_TO,
  ORB_BORDER_COLOR,
  ORB_HIGHLIGHT_COLOR,
  ORB_HIGHLIGHT_SIZE,
  ORB_SHADOW,
  ORB_SHADOW_HOVER,
} from "@/theme/orbTheme";

interface OrbIconProps {
  isHovered: boolean;
  className?: string;
}

/**
 * Production visual surface of the Living Orb.
 *
 * Three composited layers create the glass-sphere illusion:
 *   1. Linear-gradient base  — primary colour ramp, top-left → bottom-right
 *   2. Radial depth overlay  — darkens the lower-right quadrant for convexity
 *   3. Specular highlight    — a small bright ellipse at top-left, simulates
 *                              a light source striking the glass surface
 *
 * All colour and shadow values come from orbTheme, which references CSS custom
 * properties that resolve automatically for light and dark themes.
 *
 * Static visuals only — no animations, transitions, or DOM mutations.
 */
export function OrbIcon({ isHovered, className }: OrbIconProps) {
  const sphereStyle: CSSProperties = {
    width: ORB_SPHERE_SIZE,
    height: ORB_SPHERE_SIZE,
    borderRadius: "50%",
    position: "relative",
    overflow: "hidden",
    background: `linear-gradient(135deg, ${ORB_GRADIENT_FROM} 0%, ${ORB_GRADIENT_MID} 50%, ${ORB_GRADIENT_TO} 100%)`,
    border: `1px solid ${ORB_BORDER_COLOR}`,
    boxShadow: isHovered ? ORB_SHADOW_HOVER : ORB_SHADOW,
  };

  /**
   * Depth overlay: a radial gradient darkening the lower-right quadrant.
   * Gives the sphere a convex, three-dimensional appearance by simulating
   * a shadow on the face turned away from the light source.
   */
  const depthOverlayStyle: CSSProperties = {
    position: "absolute",
    inset: 0,
    borderRadius: "50%",
    background: "radial-gradient(ellipse at 72% 78%, hsl(0 0% 0% / 0.20) 0%, transparent 62%)",
    pointerEvents: "none",
  };

  /**
   * Specular highlight: a soft bright ellipse at the top-left that simulates
   * light refracting off a curved glass surface. Positioned slightly off-centre
   * to feel natural rather than perfectly symmetric.
   */
  const highlightStyle: CSSProperties = {
    position: "absolute",
    top: "13%",
    left: "15%",
    width: ORB_HIGHLIGHT_SIZE,
    height: Math.round(ORB_HIGHLIGHT_SIZE * 0.65),
    borderRadius: "50%",
    background: ORB_HIGHLIGHT_COLOR,
    filter: "blur(1.5px)",
    pointerEvents: "none",
  };

  return (
    <div
      aria-hidden="true"
      className={className}
      style={{
        position: "absolute",
        top: ORB_SPHERE_INSET,
        left: ORB_SPHERE_INSET,
        width: ORB_SPHERE_SIZE,
        height: ORB_SPHERE_SIZE,
      }}
    >
      <div style={sphereStyle}>
        <div style={depthOverlayStyle} />
        <div style={highlightStyle} />
      </div>
    </div>
  );
}
