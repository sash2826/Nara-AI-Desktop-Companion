import { motion, type Variants } from "framer-motion";
import type { OrbAnimationState } from "./orbWindowStore";
import {
  ORB_SPHERE_SIZE,
  ORB_GRADIENT_FROM,
  ORB_GRADIENT_MID,
  ORB_GRADIENT_TO,
  ORB_BORDER_COLOR,
  ORB_HIGHLIGHT_COLOR,
  ORB_HIGHLIGHT_SIZE,
  ORB_SPHERE_INSET,
  ORB_SHADOW,
  ORB_SHADOW_HOVER,
} from "@/theme/orbTheme";

// ── SVG Filter IDs ────────────────────────────────────────────────────────────

export const LIQUID_FILTER_ID = "orb-liquid-filter";
export const AMBER_GLOW_FILTER_ID = "orb-amber-filter";

// ── Framer Motion variants per animation state ────────────────────────────────

/**
 * Outer container variants — controls scale morph and rotation for blob states.
 * Only Listening and Processing morph away from a perfect circle via borderRadius.
 */
const containerVariants: Variants = {
  idle: {
    scale: 1,
    rotate: 0,
    borderRadius: "50%",
    transition: { duration: 0.6, ease: "easeOut" },
  },
  listening: {
    scale: [1, 1.06, 0.97, 1.04, 1],
    borderRadius: ["50%", "44% 56% 52% 48%", "52% 48% 44% 56%", "48% 52% 56% 44%", "50%"],
    transition: {
      duration: 1.4,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
  processing: {
    scale: [1, 1.04, 0.98, 1.05, 1],
    rotate: [0, 6, -4, 8, 0],
    borderRadius: ["50%", "48% 52% 44% 56%", "56% 44% 52% 48%", "44% 56% 48% 52%", "50%"],
    transition: {
      duration: 1.0,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
  notification: {
    scale: 1,
    rotate: 0,
    borderRadius: "50%",
    transition: { duration: 0.4, ease: "easeOut" },
  },
  error: {
    scale: 1,
    rotate: 0,
    borderRadius: "50%",
    transition: { duration: 0.3, ease: "easeOut" },
  },
};

/**
 * Sphere surface variants — controls opacity and the breathing pulse.
 * Only Idle pulses; Notification uses amber overrides applied via boxShadow.
 */
const sphereVariants: Variants = {
  idle: {
    opacity: [0.88, 1, 0.88],
    transition: { duration: 3.2, repeat: Infinity, ease: "easeInOut" },
  },
  listening: {
    opacity: 1,
    transition: { duration: 0.2 },
  },
  processing: {
    opacity: 1,
    transition: { duration: 0.2 },
  },
  notification: {
    opacity: [0.9, 1, 0.9],
    transition: { duration: 2.0, repeat: Infinity, ease: "easeInOut" },
  },
  error: {
    opacity: [0.7, 1, 0.7, 1, 1],
    transition: { duration: 0.5, repeat: 2, ease: "easeInOut" },
  },
};

// ── Box shadow per state (drives the glow) ─────────────────────────────────────

function boxShadowForState(state: OrbAnimationState): string {
  switch (state) {
    case "notification":
      return [
        "var(--shadow-elevation-4)",
        "0 0 0 2px hsl(38 95% 55% / 0.35)",
        "0 0 18px 4px hsl(38 95% 55% / 0.50)",
      ].join(", ");
    case "error":
      return [
        "var(--shadow-elevation-4)",
        "0 0 0 2px hsl(0 72% 51% / 0.40)",
        "0 0 16px 3px hsl(0 72% 51% / 0.35)",
      ].join(", ");
    case "listening":
    case "processing":
      return ORB_SHADOW_HOVER;
    default:
      return ORB_SHADOW;
  }
}

// ── Gradient per state ────────────────────────────────────────────────────────

function gradientForState(state: OrbAnimationState): string {
  if (state === "notification") {
    return "linear-gradient(135deg, hsl(38 95% 65%) 0%, hsl(38 95% 50%) 50%, hsl(30 90% 42%) 100%)";
  }
  if (state === "error") {
    return "linear-gradient(135deg, hsl(0 72% 65%) 0%, hsl(0 72% 51%) 50%, hsl(0 65% 40%) 100%)";
  }
  return `linear-gradient(135deg, ${ORB_GRADIENT_FROM} 0%, ${ORB_GRADIENT_MID} 50%, ${ORB_GRADIENT_TO} 100%)`;
}

// ── SVG Filters ───────────────────────────────────────────────────────────────

/**
 * Renders hidden SVG defs that provide the liquid-distortion and amber-glow
 * SVG filters. These are referenced by id on the orb canvas element.
 * Must be mounted once in the orb window DOM.
 */
export function OrbSvgFilters() {
  return (
    <svg
      aria-hidden="true"
      style={{ position: "absolute", width: 0, height: 0, overflow: "hidden" }}
    >
      <defs>
        {/* Liquid turbulence distortion — applied during listening/processing */}
        <filter id={LIQUID_FILTER_ID} x="-20%" y="-20%" width="140%" height="140%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.015 0.015"
            numOctaves="3"
            seed="2"
            result="noise"
          >
            <animate
              attributeName="baseFrequency"
              values="0.015 0.015;0.025 0.020;0.015 0.015"
              dur="2s"
              repeatCount="indefinite"
            />
          </feTurbulence>
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="6" result="displaced" />
          <feComposite in="displaced" in2="SourceGraphic" operator="in" />
        </filter>

        {/* Amber glow — applied during notification state */}
        <filter id={AMBER_GLOW_FILTER_ID} x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feFlood floodColor="hsl(38 95% 55%)" floodOpacity="0.4" result="color" />
          <feComposite in="color" in2="blur" operator="in" result="glow" />
          <feMerge>
            <feMergeNode in="glow" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
    </svg>
  );
}

// ── Main animated orb sphere ──────────────────────────────────────────────────

interface OrbSphereProps {
  state: OrbAnimationState;
  // isHovered is accepted for forward compatibility with hover-based shadow overrides
  isHovered?: boolean;
}

/**
 * The animated glass sphere rendered inside OrbShell.
 * Drives all motion directly from the OrbAnimationState.
 */
export function OrbSphere({ state }: OrbSphereProps) {
  const useLiquidFilter = state === "listening" || state === "processing";

  return (
    <motion.div
      variants={containerVariants}
      animate={state}
      style={{
        width: ORB_SPHERE_SIZE,
        height: ORB_SPHERE_SIZE,
        position: "absolute",
        top: ORB_SPHERE_INSET,
        left: ORB_SPHERE_INSET,
        filter: useLiquidFilter ? `url(#${LIQUID_FILTER_ID})` : undefined,
      }}
    >
      <motion.div
        variants={sphereVariants}
        animate={state}
        style={{
          width: "100%",
          height: "100%",
          borderRadius: "50%",
          position: "relative",
          overflow: "hidden",
          background: gradientForState(state),
          border: `1px solid ${ORB_BORDER_COLOR}`,
          boxShadow: boxShadowForState(state),
          transition: "background 0.6s ease, box-shadow 0.4s ease",
        }}
      >
        {/* Depth overlay — convexity illusion */}
        <div
          aria-hidden="true"
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: "50%",
            background:
              "radial-gradient(ellipse at 72% 78%, hsl(0 0% 0% / 0.20) 0%, transparent 62%)",
            pointerEvents: "none",
          }}
        />
        {/* Specular highlight */}
        <div
          aria-hidden="true"
          style={{
            position: "absolute",
            top: "13%",
            left: "15%",
            width: ORB_HIGHLIGHT_SIZE,
            height: Math.round(ORB_HIGHLIGHT_SIZE * 0.65),
            borderRadius: "50%",
            background: ORB_HIGHLIGHT_COLOR,
            filter: "blur(1.5px)",
            pointerEvents: "none",
          }}
        />
      </motion.div>
    </motion.div>
  );
}
