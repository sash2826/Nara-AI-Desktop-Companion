import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Physical size of the orb hit-target in pixels. Meets the 44 × 44 minimum touch target. */
export const ORB_SIZE = 56;

interface OrbContainerProps {
  x: number;
  y: number;
  children: ReactNode;
  className?: string;
}

/**
 * Positions the orb absolutely within a fixed full-screen layer.
 *
 * Responsibility: layout and sizing only.
 * Drag logic, interaction, and hover state live in LivingOrb.
 */
export function OrbContainer({ x, y, children, className }: OrbContainerProps) {
  const style: CSSProperties = {
    width: ORB_SIZE,
    height: ORB_SIZE,
    transform: `translate(${x}px, ${y}px)`,
  };

  return (
    <div style={style} className={cn("absolute left-0 top-0 select-none", className)}>
      {children}
    </div>
  );
}
