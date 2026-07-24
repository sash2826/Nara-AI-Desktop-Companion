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
import { cn } from "@/lib/utils";

interface PageModule {
  component: ComponentType;
  /** When true the page manages its own padding — host renders no p-6 */
  fullBleed?: boolean;
}

const PAGE_MAP: Record<NavItemId, PageModule> = {
  home: { component: HomePage },
  chat: { component: ChatPage, fullBleed: true },
  workspace: { component: WorkspacePage },
  search: { component: SearchPage },
  "knowledge-graph": { component: KnowledgeGraphPage },
  automation: { component: AutomationPage },
  settings: { component: SettingsPage },
};

const PAGE_TRANSITION: Transition = { duration: 0.15, ease: "easeOut" };

export function MainContent() {
  const { activeItem } = useNavigationStore();
  const { component: ActivePage, fullBleed } = PAGE_MAP[activeItem];

  return (
    <div className="relative flex-1 overflow-hidden bg-background">
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={activeItem}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={PAGE_TRANSITION}
          className={cn("absolute inset-0", fullBleed ? "overflow-hidden" : "scroll-y p-6")}
        >
          <ActivePage />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
