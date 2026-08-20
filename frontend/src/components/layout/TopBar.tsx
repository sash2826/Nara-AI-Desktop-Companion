import { Search } from "lucide-react";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { useNavigationStore } from "@/store/navigationStore";
import { cn } from "@/lib/utils";
import { TOP_BAR_HEIGHT } from "@/layouts/constants";

interface TopBarProps {
  className?: string;
}

export function TopBar({ className }: TopBarProps) {
  const setActiveItem = useNavigationStore((s) => s.setActiveItem);

  return (
    <header
      style={{ height: TOP_BAR_HEIGHT }}
      className={cn(
        "z-sticky flex flex-shrink-0 items-center gap-4 border-b border-border bg-background px-4",
        className
      )}
      aria-label="Top bar"
    >
      {/* Nara brand — VOLVO wordmark + tagline */}
      <div className="flex flex-col select-none leading-none">
        <span className="font-display text-sm font-bold tracking-widest text-foreground uppercase">
          VOLVO
        </span>
        <span className="text-2xs tracking-wide text-muted-foreground">
          Your workspace, within reach.
        </span>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Search button — navigates to the Search page */}
      <button
        aria-label="Open search"
        onClick={() => setActiveItem("search")}
        className={cn(
          "flex h-8 w-56 items-center gap-2 rounded-full border border-border bg-muted px-3",
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
