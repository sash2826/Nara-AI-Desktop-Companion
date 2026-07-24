import { cn } from "@/lib/utils";

type StatusVariant = "online" | "offline" | "degraded" | "unknown";

interface StatusIndicatorProps {
  label: string;
  status: StatusVariant;
  className?: string;
}

const STATUS_CLASSES: Record<StatusVariant, string> = {
  online: "bg-success",
  offline: "bg-destructive",
  degraded: "bg-warning",
  unknown: "bg-muted-foreground",
};

const STATUS_LABELS: Record<StatusVariant, string> = {
  online: "Online",
  offline: "Offline",
  degraded: "Degraded",
  unknown: "Unknown",
};

export function StatusIndicator({ label, status, className }: StatusIndicatorProps) {
  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <span
        className={cn("h-1.5 w-1.5 flex-shrink-0 rounded-full", STATUS_CLASSES[status])}
        aria-hidden="true"
      />
      <span className="text-2xs text-muted-foreground">
        {label}
        <span className="sr-only">: {STATUS_LABELS[status]}</span>
      </span>
    </div>
  );
}
