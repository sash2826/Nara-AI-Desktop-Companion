import { motion } from "framer-motion";
import {
  Home,
  MessageSquare,
  LayoutDashboard,
  Search,
  Network,
  Zap,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Logo } from "@/components/common/Logo";
import { NavItem } from "./NavItem";
import { NAV_ITEMS } from "./NAV_ITEMS";
import { useLayout } from "@/hooks/useLayout";
import { useNavigationStore } from "@/store/navigationStore";
import { SIDEBAR_COLLAPSED_WIDTH, SIDEBAR_EXPANDED_WIDTH } from "@/layouts/constants";
import { cn } from "@/lib/utils";
import type { NavItemId } from "@/types/navigation";

const ICON_MAP: Record<string, LucideIcon> = {
  Home,
  MessageSquare,
  LayoutDashboard,
  Search,
  Network,
  Zap,
  Settings,
};

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useLayout();
  const { activeItem, setActiveItem } = useNavigationStore();

  const mainItems = NAV_ITEMS.filter((item) => item.id !== "settings");
  const settingsItem = NAV_ITEMS.find((item) => item.id === "settings");

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarCollapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_EXPANDED_WIDTH }}
      transition={{ type: "spring", stiffness: 320, damping: 32 }}
      className={cn(
        "relative flex flex-shrink-0 flex-col overflow-hidden",
        "border-r border-sidebar-border bg-sidebar"
      )}
      aria-label="Primary navigation"
    >
      {/* Header */}
      <div
        className={cn(
          "flex h-12 flex-shrink-0 items-center border-b border-sidebar-border px-3",
          sidebarCollapsed ? "justify-center" : "justify-between"
        )}
      >
        <Logo collapsed={sidebarCollapsed} />

        {!sidebarCollapsed && (
          <button
            onClick={toggleSidebar}
            aria-label="Collapse sidebar"
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors duration-fast hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <PanelLeftClose size={15} strokeWidth={1.8} />
          </button>
        )}
      </div>

      {/* Main navigation */}
      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-2 scroll-y">
        {mainItems.map((item) => {
          const icon = ICON_MAP[item.iconName];
          if (!icon) return null;
          return (
            <NavItem
              key={item.id}
              id={item.id}
              label={item.label}
              icon={icon}
              isActive={activeItem === item.id}
              isCollapsed={sidebarCollapsed}
              onClick={(id: NavItemId) => setActiveItem(id)}
            />
          );
        })}
      </nav>

      {/* Footer — settings + collapse toggle */}
      <div className="flex flex-shrink-0 flex-col gap-0.5 border-t border-sidebar-border p-2">
        {settingsItem && ICON_MAP[settingsItem.iconName] && (
          <NavItem
            id={settingsItem.id}
            label={settingsItem.label}
            icon={ICON_MAP[settingsItem.iconName]}
            isActive={activeItem === settingsItem.id}
            isCollapsed={sidebarCollapsed}
            onClick={(id: NavItemId) => setActiveItem(id)}
          />
        )}

        {sidebarCollapsed && (
          <button
            onClick={toggleSidebar}
            aria-label="Expand sidebar"
            className="flex h-8 w-full items-center justify-center rounded-lg text-muted-foreground transition-colors duration-fast hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <PanelLeftOpen size={15} strokeWidth={1.8} />
          </button>
        )}
      </div>
    </motion.aside>
  );
}
