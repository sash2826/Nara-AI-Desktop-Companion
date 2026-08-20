import { motion } from "framer-motion";
import { ArrowUp, Square } from "lucide-react";
import { cn } from "@/lib/utils";

interface SendButtonProps {
  canSend: boolean;
  isStreaming: boolean;
  onSend: () => void;
  onStop?: () => void;
  className?: string;
}

export function SendButton({ canSend, isStreaming, onSend, onStop, className }: SendButtonProps) {
  if (isStreaming) {
    return (
      <motion.button
        type="button"
        onClick={onStop}
        aria-label="Stop generating"
        title="Stop generating"
        whileTap={{ scale: 0.92 }}
        className={cn(
          "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full",
          "bg-foreground text-background transition-colors duration-fast hover:opacity-80",
          className
        )}
      >
        <Square size={12} strokeWidth={2.5} fill="currentColor" aria-hidden="true" />
      </motion.button>
    );
  }

  return (
    <motion.button
      type="button"
      onClick={onSend}
      disabled={!canSend}
      aria-label="Send message"
      title="Send message"
      whileTap={canSend ? { scale: 0.92 } : {}}
      className={cn(
        "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-colors duration-fast",
        canSend
          ? "bg-primary text-primary-foreground hover:opacity-90"
          : "bg-muted text-muted-foreground cursor-not-allowed",
        className
      )}
    >
      <ArrowUp size={15} strokeWidth={2.2} aria-hidden="true" />
    </motion.button>
  );
}
