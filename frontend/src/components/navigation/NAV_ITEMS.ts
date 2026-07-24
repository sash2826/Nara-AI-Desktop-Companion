import type { NavItemId } from "@/types/navigation";

export interface NavItemConfig {
  id: NavItemId;
  label: string;
  iconName: string;
}

export const NAV_ITEMS: NavItemConfig[] = [
  { id: "home", label: "Home", iconName: "Home" },
  { id: "chat", label: "Chat", iconName: "MessageSquare" },
  { id: "workspace", label: "Workspace", iconName: "LayoutDashboard" },
  { id: "search", label: "Search", iconName: "Search" },
  { id: "knowledge-graph", label: "Knowledge Graph", iconName: "Network" },
  { id: "automation", label: "Automation", iconName: "Zap" },
  { id: "settings", label: "Settings", iconName: "Settings" },
];
