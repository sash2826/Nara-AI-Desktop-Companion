import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface QuickAction {
  id: string;
  label: string;
  prompt: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  {
    id: "catchup",
    label: "Catch me up",
    prompt: "Summarise the key decisions and action items from my recent documents",
  },
  {
    id: "status",
    label: "What's in progress?",
    prompt: "What projects or tasks are currently in progress based on my documents?",
  },
  {
    id: "decisions",
    label: "Recent decisions",
    prompt: "What important decisions have been made recently across my documents?",
  },
  {
    id: "actions",
    label: "My action items",
    prompt: "List any action items or tasks assigned to me across my documents",
  },
  {
    id: "risks",
    label: "Risks & blockers",
    prompt: "What risks, blockers, or open issues are mentioned in my documents?",
  },
];

interface QuickActionsProps {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
  className?: string;
}

export function QuickActions({ onSelect, disabled = false, className }: QuickActionsProps) {
  return (
    <div
      className={cn("flex flex-wrap gap-1.5 px-4 py-2", className)}
      role="group"
      aria-label="Quick actions"
    >
      {QUICK_ACTIONS.map((action, i) => (
        <motion.button
          key={action.id}
          type="button"
          onClick={() => onSelect(action.prompt)}
          disabled={disabled}
          aria-label={`Quick action: ${action.label}`}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.15, delay: i * 0.04 }}
          whileHover={!disabled ? { scale: 1.02 } : {}}
          whileTap={!disabled ? { scale: 0.97 } : {}}
          className={cn(
            "rounded-full border border-border px-3 py-1 text-xs font-medium",
            "transition-colors duration-fast",
            disabled
              ? "cursor-not-allowed text-muted-foreground/50"
              : "text-muted-foreground hover:border-primary/50 hover:bg-accent hover:text-accent-foreground"
          )}
        >
          {action.label}
        </motion.button>
      ))}
    </div>
  );
}
