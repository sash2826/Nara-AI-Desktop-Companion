import { Search } from "lucide-react";
import { Logo } from "@/components/common/Logo";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { cn } from "@/lib/utils";
import { TOP_BAR_HEIGHT } from "@/layouts/constants";

interface TopBarProps {
  workspaceTitle?: string;
  className?: string;
}

export function TopBar({ workspaceTitle = "Workspace", className }: TopBarProps) {
  return (
    <header
      style={{ height: TOP_BAR_HEIGHT }}
      className={cn(
        "z-sticky flex flex-shrink-0 items-center gap-4 border-b border-border bg-background px-4",
        className
      )}
      aria-label="Top bar"
    >
      {/* Logo — visible only when sidebar is hidden on very small viewports */}
      <div className="hidden items-center lg:hidden">
        <Logo />
      </div>

      {/* Workspace title */}
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <span className="truncate text-sm font-semibold text-foreground">{workspaceTitle}</span>
      </div>

      {/* Search placeholder */}
      <button
        aria-label="Open search"
        className={cn(
          "flex h-8 w-56 items-center gap-2 rounded-lg border border-border bg-muted px-3",
          "text-sm text-muted-foreground transition-colors duration-fast",
          "hover:border-ring hover:bg-background hover:text-foreground"
        )}
      >
        <Search size={13} strokeWidth={1.8} aria-hidden="true" />
        <span className="truncate">Search...</span>
        <kbd className="ml-auto hidden text-2xs text-muted-foreground sm:block">⌘K</kbd>
      </button>

      {/* Theme toggle */}
      <ThemeToggle />

      {/* Window controls placeholder */}
      <div
        className="hidden items-center gap-1.5 pl-2 sm:flex"
        aria-label="Window controls"
        aria-hidden="true"
      >
        <div className="h-3 w-3 rounded-full bg-muted-foreground/30" />
        <div className="h-3 w-3 rounded-full bg-muted-foreground/30" />
        <div className="h-3 w-3 rounded-full bg-muted-foreground/30" />
      </div>
    </header>
  );
}
