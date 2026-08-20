import { cn } from "@/lib/utils";

interface LogoProps {
  collapsed?: boolean;
  className?: string;
}

export function Logo({ collapsed = false, className }: LogoProps) {
  if (collapsed) {
    return (
      <div className={cn("flex items-center justify-center select-none", className)}>
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-sidebar-accent">
          <span className="font-display text-xs font-bold tracking-widest text-sidebar-foreground">
            V
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-0 select-none", className)}>
      <span className="font-display text-sm font-bold tracking-widest text-sidebar-foreground uppercase leading-tight">
        VOLVO
      </span>
      <span className="text-2xs tracking-wide text-sidebar-foreground/50 leading-tight">Nara</span>
    </div>
  );
}
