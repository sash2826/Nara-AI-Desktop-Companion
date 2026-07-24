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
        "group relative flex w-full items-center gap-3 rounded-lg px-2 py-2 text-sm transition-colors duration-fast",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        isActive
          ? "bg-accent text-accent-foreground"
          : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
      )}
    >
      {isActive && (
        <motion.div
          layoutId="nav-active-indicator"
          className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-primary"
          transition={{ type: "spring", stiffness: 400, damping: 35 }}
        />
      )}

      <Icon
        size={17}
        strokeWidth={isActive ? 2.2 : 1.8}
        className={cn(
          "flex-shrink-0 transition-colors duration-fast",
          isActive ? "text-primary" : "text-sidebar-foreground"
        )}
        aria-hidden="true"
      />

      <AnimatePresence initial={false}>
        {!isCollapsed && (
          <motion.span
            key="label"
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="truncate font-medium"
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
}
