import { motion } from "framer-motion";
import type { AmbientMessage } from "./useOrbAmbientMessages";

interface OrbAmbientBubbleProps {
  message: AmbientMessage;
}

/**
 * Single-line pill hint that floats directly above the orb.
 * Rises into view from just below; reminder variant has an amber tint.
 */
export function OrbAmbientBubble({ message }: OrbAmbientBubbleProps) {
  const isReminder = message.kind === "reminder";

  const borderColor = isReminder ? "hsl(38 95% 55% / 0.55)" : "hsl(var(--border) / 0.55)";

  const bgColor = isReminder ? "hsl(38 30% 10% / 0.94)" : "hsl(var(--popover) / 0.94)";

  const textColor = isReminder ? "hsl(38 90% 80%)" : "hsl(var(--popover-foreground))";

  return (
    <motion.div
      data-orb-surface
      initial={{ opacity: 0, y: 8, scale: 0.94 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.94 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      style={{
        // Anchored above the orb and to its right edge, matching the query overlay.
        position: "absolute",
        bottom: "calc(100% + 12px)",
        right: 0,
        maxWidth: 340,
        zIndex: 90,
        background: bgColor,
        backdropFilter: "blur(20px) saturate(180%)",
        WebkitBackdropFilter: "blur(20px) saturate(180%)",
        border: `1px solid ${borderColor}`,
        borderRadius: 999,
        padding: "8px 16px",
        boxShadow: ["0 4px 24px hsl(0 0% 0% / 0.25)", "inset 0 1px 0 hsl(0 0% 100% / 0.07)"].join(
          ", "
        ),
        color: textColor,
        fontFamily: "var(--font-sans), system-ui, sans-serif",
        fontSize: 13,
        lineHeight: 1.2,
        fontWeight: isReminder ? 500 : 400,
        // Single line — never wraps; overflow is trimmed with an ellipsis.
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
        pointerEvents: "none",
        userSelect: "none",
        WebkitUserSelect: "none",
      }}
    >
      {message.text}
    </motion.div>
  );
}
