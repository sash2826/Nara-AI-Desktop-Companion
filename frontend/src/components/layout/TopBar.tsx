import { Menu, Search } from "lucide-react";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { useLayout } from "@/hooks/useLayout";
import { useNavigationStore } from "@/store/navigationStore";
import { cn } from "@/lib/utils";
import { TOP_BAR_HEIGHT } from "@/layouts/constants";

interface TopBarProps {
  className?: string;
}

export function TopBar({ className }: TopBarProps) {
  const setActiveItem = useNavigationStore((s) => s.setActiveItem);
  const { toggleSidebar } = useLayout();

  return (
    <header
      style={{ height: TOP_BAR_HEIGHT }}
      className={cn(
        "relative z-sticky flex flex-shrink-0 items-center gap-3 border-b border-border bg-background px-4",
        className
      )}
      aria-label="Top bar"
    >
      {/* Left: sidebar toggle + brand lockup */}
      <div className="flex min-w-0 items-center gap-3">
        <button
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
          className={cn(
            "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-muted-foreground",
            "transition-colors duration-fast hover:bg-muted hover:text-foreground"
          )}
        >
          <Menu size={18} strokeWidth={1.8} aria-hidden="true" />
        </button>

        <span
          className="text-sm font-normal tracking-wide text-foreground select-none"
          style={{ fontFamily: "'Volvo Novum', 'Inter', sans-serif" }}
        >
          Productivity Agent
        </span>
      </div>

      {/* Right: search + theme + account */}
      <div className="ml-auto flex items-center gap-3">
        <button
          aria-label="Open search"
          onClick={() => setActiveItem("search")}
          className={cn(
            "flex h-8 w-56 items-center gap-2 rounded-lg border border-border bg-muted px-3",
            "text-sm text-muted-foreground transition-colors duration-fast",
            "hover:border-ring hover:bg-background hover:text-foreground"
          )}
        >
          <Search size={13} strokeWidth={1.8} aria-hidden="true" />
          <span className="truncate">Search...</span>
          <kbd className="ml-auto hidden text-2xs text-muted-foreground sm:block">Ctrl+K</kbd>
        </button>

        <ThemeToggle />

        <div
          className={cn(
            "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full",
            "bg-muted text-xs font-semibold text-muted-foreground select-none"
          )}
          aria-label="Account"
        >
          N
        </div>
      </div>
    </header>
  );
}
