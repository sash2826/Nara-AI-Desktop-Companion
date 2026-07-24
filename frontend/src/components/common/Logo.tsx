import { cn } from "@/lib/utils";

interface LogoProps {
  collapsed?: boolean;
  className?: string;
}

export function Logo({ collapsed = false, className }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2 select-none", className)}>
      <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-primary">
        <span className="text-xs font-bold text-primary-foreground">AI</span>
      </div>
      {!collapsed && (
        <span className="truncate text-sm font-semibold text-foreground">Enterprise AI</span>
      )}
    </div>
  );
}
