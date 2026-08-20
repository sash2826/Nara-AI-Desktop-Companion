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

// Per-capability icon square colours — hardcoded to avoid CSS var resolution
// failures when inline styles are computed before stylesheet hydration.
const NAV_ICON_BG: Record<string, string> = {
  home: "hsl(215 20% 32%)",
  chat: "hsl(210 58% 56%)",
  workspace: "hsl(171 36% 45%)",
  search: "hsl(27 79% 60%)",
  "knowledge-graph": "hsl(238 30% 50%)",
  automation: "hsl(42 63% 55%)",
  settings: "hsl(220 9% 46%)",
};

export function NavItem({ id, label, icon: Icon, isActive, isCollapsed, onClick }: NavItemProps) {
  const iconBg = NAV_ICON_BG[id] ?? "hsl(var(--color-nav-settings))";

  return (
    <button
      onClick={() => onClick(id)}
      aria-current={isActive ? "page" : undefined}
      aria-label={isCollapsed ? label : undefined}
      title={isCollapsed ? label : undefined}
      className={cn(
        "group flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-sm transition-colors duration-fast",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        isCollapsed ? "justify-center" : "justify-start"
      )}
    >
      {/* Capability-coloured icon square */}
      <div
        style={{ backgroundColor: iconBg }}
        className={cn(
          "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg transition-all duration-fast",
          isActive
            ? "ring-2 ring-white/60 ring-offset-1 ring-offset-black/40"
            : "opacity-70 group-hover:opacity-100"
        )}
      >
        <Icon size={16} strokeWidth={2} className="text-white" aria-hidden="true" />
      </div>

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
              isActive ? "text-sidebar-foreground" : "text-sidebar-foreground/60"
            )}
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
}
