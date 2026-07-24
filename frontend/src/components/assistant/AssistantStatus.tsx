import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

type StatusKind = "online" | "thinking" | "streaming" | "offline";

interface AssistantStatusProps {
  status: StatusKind;
  className?: string;
}

const STATUS_CONFIG: Record<StatusKind, { label: string; color: string }> = {
  online: { label: "Online", color: "bg-success" },
  thinking: { label: "Thinking…", color: "bg-warning" },
  streaming: { label: "Responding…", color: "bg-primary" },
  offline: { label: "Offline", color: "bg-muted-foreground" },
};

export function AssistantStatus({ status, className }: AssistantStatusProps) {
  const config = STATUS_CONFIG[status];

  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <motion.span
        className={cn("h-1.5 w-1.5 rounded-full", config.color)}
        animate={
          status === "thinking" || status === "streaming"
            ? { opacity: [1, 0.3, 1] }
            : { opacity: 1 }
        }
        transition={
          status === "thinking" || status === "streaming"
            ? { duration: 1.2, repeat: Infinity, ease: "easeInOut" }
            : {}
        }
        aria-hidden="true"
      />
      <AnimatePresence mode="wait">
        <motion.span
          key={status}
          initial={{ opacity: 0, y: 2 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -2 }}
          transition={{ duration: 0.15 }}
          className="text-2xs text-muted-foreground"
        >
          {config.label}
        </motion.span>
      </AnimatePresence>
    </div>
  );
}
