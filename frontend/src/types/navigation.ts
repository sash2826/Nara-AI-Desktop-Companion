export type NavItemId = "home" | "chat" | "workspace" | "search" | "knowledge-graph" | "settings";

export interface NavItem {
  id: NavItemId;
  label: string;
  icon: string;
}
