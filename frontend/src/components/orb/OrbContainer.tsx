import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { ORB_SIZE } from "@/theme/orbTheme";

export { ORB_SIZE };

interface OrbContainerProps {
  x: number;
  y: number;
  children: ReactNode;
  className?: string;
}

/**
 * Positions the orb absolutely within a fixed full-screen layer using
 * GPU-composited transform. Sizing comes from orbTheme.
 *
 * Responsibility: layout and positioning only.
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
