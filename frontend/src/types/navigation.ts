export type NavItemId =
  "home" | "chat" | "workspace" | "search" | "knowledge-graph" | "automation" | "settings";

export interface NavItem {
  id: NavItemId;
  label: string;
  icon: string;
}
