import { useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RefreshCw, Square } from "lucide-react";
import { PromptInput } from "./PromptInput";
import { SendButton } from "./SendButton";
import { AttachmentButton } from "./AttachmentButton";
import { QuickActions } from "./QuickActions";
import { useSettingsStore } from "@/store/settingsStore";
import { cn } from "@/lib/utils";

interface PromptComposerProps {
  value: string;
  isStreaming: boolean;
  isTyping: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  onClear: () => void;
  hasMessages: boolean;
  suggestions?: string[];
  onReshuffle?: () => void;
  className?: string;
}

export function PromptComposer({
  value,
  isStreaming,
  isTyping,
  onChange,
  onSend,
  onStop,
  onClear,
  hasMessages,
  suggestions,
  onReshuffle,
  className,
}: PromptComposerProps) {
  const isBusy = isStreaming || isTyping;
  const canSend = value.trim().length > 0 && !isBusy;
  const model = useSettingsStore((s) => s.settings.aiProvider.model);

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
      <div className="mx-auto w-full max-w-3xl">
        {/* Suggestion chips — hidden while busy */}
        <AnimatePresence>
          {!isBusy && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.15 }}
            >
              <QuickActions
                onSelect={handleQuickAction}
                disabled={isBusy}
                suggestions={suggestions}
                onReshuffle={onReshuffle}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Input pill */}
        <div className="px-4 pb-2 pt-1">
          <div
            className={cn(
              "flex items-end gap-2 rounded-[1.75rem] border border-border bg-muted/40 px-2.5 py-1.5",
              "transition-colors duration-fast focus-within:border-ring focus-within:bg-background"
            )}
          >
            {/* Left side: attachment + clear */}
            <div className="mb-0.5 flex items-center gap-1">
              <AttachmentButton />

              <AnimatePresence>
                {hasMessages && !isBusy && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.15 }}
                    type="button"
                    onClick={onClear}
                    aria-label="Clear conversation"
                    title="Clear conversation"
                    className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-full",
                      "text-muted-foreground/60 transition-colors duration-fast",
                      "hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <RefreshCw size={13} strokeWidth={1.8} />
                  </motion.button>
                )}
              </AnimatePresence>
            </div>

            <PromptInput
              value={value}
              onChange={onChange}
              onSend={onSend}
              disabled={isBusy}
              bare
              className="flex-1"
            />

            {/* Right side: stop (when busy) or send (when idle) */}
            <div className="mb-0.5">
              <AnimatePresence mode="wait">
                {isBusy ? (
                  <motion.button
                    key="stop"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.12 }}
                    type="button"
                    onClick={onStop}
                    aria-label="Stop generation"
                    title="Stop generation"
                    className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-full",
                      "bg-foreground text-background transition-colors duration-fast",
                      "hover:bg-foreground/80"
                    )}
                  >
                    <Square size={11} strokeWidth={0} fill="currentColor" />
                  </motion.button>
                ) : (
                  <motion.div
                    key="send"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.12 }}
                  >
                    <SendButton canSend={canSend} isStreaming={false} onSend={onSend} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Model name + disclaimer */}
        <p className="pb-2 text-center text-2xs text-muted-foreground/50">
          {model && <span className="font-medium text-muted-foreground/70">{model}</span>}
          {model && " · "}
          Nara can make mistakes — verify important information.
        </p>
      </div>
    </div>
  );
}
