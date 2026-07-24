import { StatusIndicator } from "@/components/common/StatusIndicator";
import { useTheme } from "@/hooks/useTheme";
import { cn } from "@/lib/utils";
import { STATUS_BAR_HEIGHT } from "@/layouts/constants";

interface StatusBarProps {
  className?: string;
}

export function StatusBar({ className }: StatusBarProps) {
  const { resolvedTheme } = useTheme();

  return (
    <footer
      style={{ height: STATUS_BAR_HEIGHT }}
      className={cn(
        "z-sticky flex flex-shrink-0 items-center gap-4 border-t border-border bg-background px-4",
        className
      )}
      aria-label="Application status"
    >
      {/* Left section — service statuses */}
      <div className="flex items-center gap-4">
        <StatusIndicator label="AI Provider" status="unknown" />
        <StatusIndicator label="Database" status="unknown" />
        <StatusIndicator label="Search Index" status="unknown" />
      </div>

      {/* Right section — sync and theme */}
      <div className="ml-auto flex items-center gap-4">
        <StatusIndicator label="Sync" status="unknown" />
        <span className="text-2xs text-muted-foreground capitalize">{resolvedTheme}</span>
      </div>
    </footer>
  );
}
