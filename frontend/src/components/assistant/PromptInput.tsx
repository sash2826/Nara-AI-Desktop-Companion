import { useRef, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { MAX_INPUT_CHARACTERS } from "@/types/conversation";

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  className?: string;
}

const MAX_TEXTAREA_HEIGHT = 180;

export function PromptInput({
  value,
  onChange,
  onSend,
  disabled = false,
  className,
}: PromptInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const remaining = MAX_INPUT_CHARACTERS - value.length;
  const isNearLimit = remaining < 200;
  const isAtLimit = remaining <= 0;

  // Auto-resize textarea height to content.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
  }, [value]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onSend();
      }
    },
    [onSend]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      onChange(e.target.value);
    },
    [onChange]
  );

  return (
    <div className={cn("relative flex flex-col", className)}>
      <motion.textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder="Ask anything about your knowledge base…"
        rows={1}
        maxLength={MAX_INPUT_CHARACTERS}
        aria-label="Message input"
        aria-describedby="char-count"
        aria-multiline="true"
        className={cn(
          "w-full resize-none rounded-xl border border-border bg-background px-4 py-3 pr-12",
          "text-sm text-foreground placeholder:text-muted-foreground",
          "transition-all duration-base",
          "focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "scrollbar-thin"
        )}
        style={{ maxHeight: MAX_TEXTAREA_HEIGHT }}
        whileFocus={{ scale: 1 }}
      />

      {/* Character counter — only visible near limit */}
      {isNearLimit && (
        <motion.span
          id="char-count"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className={cn(
            "absolute bottom-2.5 right-3 text-2xs",
            isAtLimit ? "text-destructive" : "text-muted-foreground"
          )}
          aria-live="polite"
        >
          {remaining}
        </motion.span>
      )}
    </div>
  );
}
