import { motion, AnimatePresence } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { NavItemId } from "@/types/navigation";

interface NavItemProps {
  id: NavItemId;
  label: string;
  icon: LucideIcon;
  isActive: boolean;
  isCollapsed: boolean;
  onClick: (id: NavItemId) => void;
}

export function NavItem({ id, label, icon: Icon, isActive, isCollapsed, onClick }: NavItemProps) {
  return (
    <button
      onClick={() => onClick(id)}
      aria-current={isActive ? "page" : undefined}
      aria-label={isCollapsed ? label : undefined}
      title={isCollapsed ? label : undefined}
      className={cn(
        "group relative flex w-full items-center gap-3 rounded-xl py-1.5 pr-3 text-sm transition-colors duration-fast",
        isCollapsed ? "justify-center px-0" : "pl-1.5",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        isActive ? "bg-sidebar-accent" : "hover:bg-sidebar-accent/60"
      )}
    >
      {/* Circular icon badge — filled dark when active, subtle when idle */}
      <span
        className={cn(
          "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-colors duration-fast",
          isActive
            ? "bg-foreground text-background"
            : "bg-muted text-sidebar-foreground group-hover:bg-background"
        )}
      >
        <Icon size={16} strokeWidth={isActive ? 2 : 1.8} aria-hidden="true" />
      </span>

      <AnimatePresence initial={false}>
        {!isCollapsed && (
          <motion.span
            key="label"
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className={cn(
              "truncate font-medium",
              isActive ? "text-foreground" : "text-sidebar-foreground"
            )}
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
}
