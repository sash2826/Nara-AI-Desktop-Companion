import { type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface PlaceholderPageProps {
  title: string;
  description: string;
  icon: LucideIcon;
  className?: string;
}

export function PlaceholderPage({
  title,
  description,
  icon: Icon,
  className,
}: PlaceholderPageProps) {
  return (
    <div
      className={cn(
        "flex h-full flex-col items-center justify-center gap-4 text-center",
        className
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted">
        <Icon size={24} className="text-muted-foreground" strokeWidth={1.5} />
      </div>
      <div className="max-w-xs space-y-1">
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
