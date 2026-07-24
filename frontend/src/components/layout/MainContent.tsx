import { AnimatePresence, motion } from "framer-motion";
import type { Transition } from "framer-motion";
import { useNavigationStore } from "@/store/navigationStore";
import { HomePage } from "@/pages/HomePage";
import { ChatPage } from "@/pages/ChatPage";
import { WorkspacePage } from "@/pages/WorkspacePage";
import { SearchPage } from "@/pages/SearchPage";
import { KnowledgeGraphPage } from "@/pages/KnowledgeGraphPage";
import { AutomationPage } from "@/pages/AutomationPage";
import { SettingsPage } from "@/pages/SettingsPage";
import type { NavItemId } from "@/types/navigation";
import type { ComponentType } from "react";

const PAGE_MAP: Record<NavItemId, ComponentType> = {
  home: HomePage,
  chat: ChatPage,
  workspace: WorkspacePage,
  search: SearchPage,
  "knowledge-graph": KnowledgeGraphPage,
  automation: AutomationPage,
  settings: SettingsPage,
};

const PAGE_TRANSITION: Transition = { duration: 0.15, ease: "easeOut" };

export function MainContent() {
  const { activeItem } = useNavigationStore();
  const ActivePage = PAGE_MAP[activeItem];

  return (
    <div className="relative flex-1 overflow-hidden bg-background">
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={activeItem}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={PAGE_TRANSITION}
          className="absolute inset-0 scroll-y p-6"
        >
          <ActivePage />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
