import { cn } from "@/lib/utils";

interface OrbIconProps {
  isHovered: boolean;
  className?: string;
}

/**
 * The visual surface of the Living Orb.
 *
 * Responsibility: appearance only. No interaction logic lives here.
 * Animation, glow, and final visual identity belong to later tasks.
 */
export function OrbIcon({ isHovered, className }: OrbIconProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "flex h-full w-full items-center justify-center rounded-full",
        "bg-primary text-primary-foreground",
        "transition-[opacity,transform] duration-100",
        isHovered ? "scale-105 opacity-90" : "scale-100 opacity-100",
        className
      )}
    >
      {/* Inner mark — placeholder until final identity is defined in Task 0.6.4.3+ */}
      <div className="h-2 w-2 rounded-full bg-current opacity-60" />
    </div>
  );
}
