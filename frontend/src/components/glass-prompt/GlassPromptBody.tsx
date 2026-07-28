import { useRef } from "react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

/**
 * Inner content of the Glass Prompt.
 *
 * Phase 00 shell — renders a focused input field. Conversation logic
 * (message list, streaming response, ConversationService wiring) is added
 * in the live-wiring phase.
 */
export function GlassPromptBody({ className }: { className?: string }) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className={cn("flex flex-col", className)}>
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-white/10 px-5 py-3">
        <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase select-none">
          AI Companion
        </span>
      </div>

      {/* Input area */}
      <div className="px-4 py-4">
        <Input
          ref={inputRef}
          placeholder="Ask anything…"
          className={cn(
            "h-11 rounded-xl border-white/20 bg-white/50 dark:bg-white/5",
            "placeholder:text-muted-foreground/60",
            "focus-visible:ring-1 focus-visible:ring-primary/50",
            "text-base pr-12"
          )}
          autoComplete="off"
          spellCheck={false}
        />
      </div>

      {/* Footer hint */}
      <div className="flex items-center justify-end gap-3 px-4 pb-3">
        <span className="text-[11px] text-muted-foreground/50 select-none">
          Press <kbd className="font-mono">Esc</kbd> to close
        </span>
      </div>
    </div>
  );
}
