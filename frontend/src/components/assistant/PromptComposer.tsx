import { useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PromptInput } from "./PromptInput";
import { SendButton } from "./SendButton";
import { QuickActions } from "./QuickActions";
import { cn } from "@/lib/utils";

interface PromptComposerProps {
  value: string;
  isStreaming: boolean;
  isTyping: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
  className?: string;
}

export function PromptComposer({
  value,
  isStreaming,
  isTyping,
  onChange,
  onSend,
  className,
}: PromptComposerProps) {
  const isBusy = isStreaming || isTyping;
  const canSend = value.trim().length > 0 && !isBusy;

  const handleQuickAction = useCallback(
    (prompt: string) => {
      onChange(prompt);
    },
    [onChange]
  );

  return (
    <div
      className={cn("flex flex-shrink-0 flex-col gap-0", className)}
      role="region"
      aria-label="Message composer"
    >
      {/* Quick action chips — hidden while busy */}
      <AnimatePresence>
        {!isBusy && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.15 }}
          >
            <QuickActions onSelect={handleQuickAction} disabled={isBusy} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input row */}
      <div className="flex items-end gap-2 border-t border-border px-4 py-3">
        <PromptInput
          value={value}
          onChange={onChange}
          onSend={onSend}
          disabled={isBusy}
          className="flex-1"
        />

        <SendButton canSend={canSend} isStreaming={isStreaming} onSend={onSend} />
      </div>

      {/* Keyboard hint */}
      <p className="pb-2 text-center text-2xs text-muted-foreground/50">
        <kbd className="font-mono">Enter</kbd> to send ·{" "}
        <kbd className="font-mono">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
