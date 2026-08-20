import { motion } from "framer-motion";
import { Sidebar } from "@/components/navigation/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { StatusBar } from "@/components/layout/StatusBar";
import { MainContent } from "@/components/layout/MainContent";
import { WorkspaceContainer } from "./WorkspaceContainer";

/**
 * AppShell is the top-level layout container.
 *
 * Structure:
 *   ┌─────────────────────────────────────────┐
 *   │ TopBar (full width)                      │
 *   ├─────────┬───────────────────────────────│
 *   │ Sidebar │ WorkspaceContainer            │
 *   │         │   └─ MainContent (active page)│
 *   │         ├───────────────────────────────│
 *   │         │ StatusBar                     │
 *   └─────────┴───────────────────────────────┘
 *
 * Sidebar animates its width; the rest of the shell fills the remaining space.
 */
export function AppShell() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="flex h-full w-full flex-col overflow-hidden bg-background"
    >
      {/* Full-width top bar */}
      <TopBar />

      {/* Sidebar + main column */}
      <div className="flex min-w-0 flex-1 overflow-hidden">
        <Sidebar />

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <WorkspaceContainer>
            <MainContent />
          </WorkspaceContainer>

          <StatusBar />
        </div>
      </div>
    </motion.div>
  );
}
