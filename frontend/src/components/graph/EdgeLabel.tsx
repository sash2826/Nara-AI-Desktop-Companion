/**
 * EdgeLabel — standalone tooltip pill for a graph relationship type.
 *
 * Rendered by GraphCanvas on hover over an edge line.
 * Kept as a pure presentational component so the canvas can import just the
 * styles and render the label inline in SVG (no React portal needed).
 */

import { cn } from "@/lib/utils";

interface EdgeLabelProps {
  relationshipType: string;
  confidence: number;
  className?: string;
}

export function EdgeLabel({ relationshipType, confidence, className }: EdgeLabelProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border bg-popover px-2 py-0.5 text-xs shadow-sm",
        className
      )}
    >
      <span className="font-mono font-medium text-foreground">{relationshipType}</span>
      <span className="text-muted-foreground">·</span>
      <span className="tabular-nums text-muted-foreground">{Math.round(confidence * 100)}%</span>
    </div>
  );
}
