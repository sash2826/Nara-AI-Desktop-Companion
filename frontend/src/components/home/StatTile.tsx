import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatTileProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  suffix?: string;
  accent?: "default" | "warning" | "success";
  className?: string;
}

const ACCENT_CLASSES = {
  default: "text-foreground",
  warning: "text-warning",
  success: "text-success",
};

const ICON_ACCENT_CLASSES = {
  default: "text-muted-foreground",
  warning: "text-warning",
  success: "text-success",
};

function formatValue(value: number | string): string {
  if (typeof value === "string") return value;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return String(value);
}

export function StatTile({
  label,
  value,
  icon: Icon,
  suffix,
  accent = "default",
  className,
}: StatTileProps) {
  return (
    <div
      className={cn("flex flex-col gap-3 rounded-xl border border-border bg-card p-4", className)}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        <Icon size={15} strokeWidth={1.75} className={ICON_ACCENT_CLASSES[accent]} />
      </div>
      <div className="flex items-baseline gap-1">
        <span className={cn("text-2xl font-semibold tabular-nums", ACCENT_CLASSES[accent])}>
          {formatValue(value)}
        </span>
        {suffix && <span className="text-xs text-muted-foreground">{suffix}</span>}
      </div>
    </div>
  );
}
