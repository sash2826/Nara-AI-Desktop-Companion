import { cn } from "@/lib/utils";

interface LogoProps {
  collapsed?: boolean;
  className?: string;
}

export function Logo({ collapsed = false, className }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2 select-none", className)}>
      <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md bg-primary">
        <span className="text-sm font-bold text-primary-foreground">N</span>
      </div>
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
