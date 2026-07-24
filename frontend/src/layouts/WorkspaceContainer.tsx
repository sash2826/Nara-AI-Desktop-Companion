import React from "react";
import { cn } from "@/lib/utils";

interface WorkspaceContainerProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * The scrollable region that hosts the active page content.
 * Sits between the TopBar and StatusBar, beside the Sidebar.
 * Future features (Character Widget, split panes) will be positioned inside this container.
 */
export function WorkspaceContainer({ children, className }: WorkspaceContainerProps) {
  return <div className={cn("relative flex flex-1 overflow-hidden", className)}>{children}</div>;
}
