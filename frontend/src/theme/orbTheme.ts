/**
 * Design tokens for the Living Orb.
 *
 * All colour expressions reference existing CSS custom properties from
 * tokens.css / themes.css so they automatically adapt to light/dark theme
 * without any JavaScript theme detection. Browsers resolve var(--...) inside
 * inline styles at paint time, so theme switching is instantaneous.
 *
 * Sizing and spacing constants are theme-invariant and stored as plain numbers.
 *
 * Components must never hardcode orb colours, shadows, or spacing — import
 * from here instead.
 */

// ── Sizing ────────────────────────────────────────────────────────────────────

/** Outer hit-target diameter in px. Meets the 44 × 44 minimum touch target. */
export const ORB_SIZE = 56;

/** Diameter of the glass sphere surface inside the hit-target in px. */
export const ORB_SPHERE_SIZE = 48;

/** Diameter of the specular highlight ellipse in px. */
export const ORB_HIGHLIGHT_SIZE = 10;

// ── Spacing ───────────────────────────────────────────────────────────────────

/** Inset from hit-target edge to sphere edge — centres the sphere. */
export const ORB_SPHERE_INSET = (ORB_SIZE - ORB_SPHERE_SIZE) / 2;

// ── Border radius ─────────────────────────────────────────────────────────────

/** All circular orb elements use the full-radius token. */
export const ORB_RADIUS = "var(--radius-full)";

// ── Colours — reference CSS custom properties only ────────────────────────────
//
// These resolve to the active theme's values automatically.
// Opacity suffixes (/0.N) are CSS Color Level 4 notation supported by all
// modern browsers and by the hsl() values already used in themes.css.

/** Top of sphere gradient — brighter, lighter. */
export const ORB_GRADIENT_FROM = "hsl(var(--color-primary-400))";

/** Mid-point of sphere gradient. */
export const ORB_GRADIENT_MID = "hsl(var(--color-primary-500))";

/** Bottom of sphere gradient — deeper, more saturated. */
export const ORB_GRADIENT_TO = "hsl(var(--color-primary-700))";

/** Sphere edge border. Slightly transparent to blend with the background. */
export const ORB_BORDER_COLOR = "hsl(var(--color-primary-400) / 0.45)";

/**
 * Specular highlight colour. Uses the neutral-0 (white) token so it remains
 * crisp on both light and dark backgrounds. Opacity is deliberately low to
 * keep the effect subtle.
 */
export const ORB_HIGHLIGHT_COLOR = "hsl(var(--color-neutral-0) / 0.52)";

// ── Shadows ───────────────────────────────────────────────────────────────────
//
// Composed from:
//   - var(--shadow-elevation-4): the theme's standard elevation shadow, which
//     already has light/dark variants defined in themes.css
//   - A tinted ambient shadow using var(--primary) for brand presence
//   - A faint halo ring using var(--primary) for the hover state

/** Default drop shadow. */
export const ORB_SHADOW = "var(--shadow-elevation-4), 0 0 0 1px hsl(var(--primary) / 0.15)";

/**
 * Hover drop shadow. Adds a coloured halo that reinforces interactivity
 * without animation — a static elevation increase.
 */
export const ORB_SHADOW_HOVER = [
  "var(--shadow-elevation-4)",
  "0 0 0 3px hsl(var(--primary) / 0.22)",
  "0 4px 20px hsl(var(--primary) / 0.28)",
].join(", ");

/** Focus-ring colour token, sourced from the theme's ring variable. */
export const ORB_FOCUS_RING = "var(--ring)";
