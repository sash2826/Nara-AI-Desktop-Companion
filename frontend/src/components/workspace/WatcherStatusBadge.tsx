import { cn } from "@/lib/utils";
import type { WatcherStatus } from "@/types/workspace";

interface WatcherStatusBadgeProps {
  status: WatcherStatus | null;
  className?: string;
}

export function WatcherStatusBadge({ status, className }: WatcherStatusBadgeProps) {
  if (!status) {
    return (
      <span
        className={cn("inline-flex items-center gap-1.5 text-xs text-muted-foreground", className)}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
        Unknown
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs font-medium",
        status.running ? "text-success" : "text-destructive",
        className
      )}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full", status.running ? "bg-success" : "bg-destructive")}
      />
      {status.running
        ? `Watching ${status.watched_count} folder${status.watched_count !== 1 ? "s" : ""}`
        : "Stopped"}
    </span>
  );
}
