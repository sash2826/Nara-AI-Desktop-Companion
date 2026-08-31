import { cn } from "@/lib/utils";

interface LogoProps {
  collapsed?: boolean;
  className?: string;
}

/** Volvo ring-and-arrow mark, white on black, sized to fit a 28×28 container. */
function VolvoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 130 130"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className={className}
    >
      <rect width="130" height="130" fill="black" rx="6" />
      {/* Ring — near-complete circle, gap at upper-right (~315°) */}
      <path
        d="M 90.1 52.0 A 44 44 0 1 0 74.0 35.9"
        stroke="white"
        strokeWidth="9"
        fill="none"
        strokeLinecap="butt"
      />
      {/* Arrow shaft along the 315° radial */}
      <line x1="83" y1="43" x2="110" y2="16" stroke="white" strokeWidth="9" strokeLinecap="butt" />
      {/* Arrowhead */}
      <polygon points="116,10 92.6,17.8 108.2,33.4" fill="white" />
    </svg>
  );
}

export function Logo({ collapsed = false, className }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2 select-none", className)}>
      <VolvoMark className="h-7 w-7 flex-shrink-0" />
      {!collapsed && (
        <div className="flex min-w-0 flex-col leading-none">
          <span className="truncate text-sm font-semibold tracking-tight text-foreground">
            Document-Management-RAG-Graph-Agent
          </span>
          <span className="mt-0.5 truncate text-2xs text-muted-foreground">
            Your workspace, within reach.
          </span>
        </div>
      )}
    </div>
  );
}
