import { MoreHorizontal, RefreshCw } from "lucide-react";
import { AssistantAvatar } from "./AssistantAvatar";
import { AssistantStatus } from "./AssistantStatus";
import { cn } from "@/lib/utils";

interface AssistantHeaderProps {
  isTyping: boolean;
  isStreaming: boolean;
  onClearConversation: () => void;
  className?: string;
}

function resolveStatus(isTyping: boolean, isStreaming: boolean) {
  if (isTyping) return "thinking";
  if (isStreaming) return "streaming";
  return "online";
}

export function AssistantHeader({
  isTyping,
  isStreaming,
  onClearConversation,
  className,
}: AssistantHeaderProps) {
  const status = resolveStatus(isTyping, isStreaming);

  return (
    <header
      className={cn(
        "flex flex-shrink-0 items-center gap-3 border-b border-border px-4 py-3",
        className
      )}
      aria-label="Assistant header"
    >
      <AssistantAvatar size="md" isActive={status === "online"} />

      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <span className="text-sm font-semibold text-foreground">AI Companion</span>
        <div className="flex items-center gap-2">
          <AssistantStatus status={status} />
          {/* AI provider placeholder */}
          <span className="text-2xs text-muted-foreground/60">· GPT (placeholder)</span>
        </div>
      </div>

      {/* Conversation actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={onClearConversation}
          aria-label="Clear conversation"
          title="Clear conversation"
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md transition-colors duration-fast",
            "text-muted-foreground hover:bg-muted hover:text-foreground"
          )}
        >
          <RefreshCw size={14} strokeWidth={1.8} />
        </button>
        <button
          aria-label="More options"
          title="More options"
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md transition-colors duration-fast",
            "text-muted-foreground hover:bg-muted hover:text-foreground"
          )}
        >
          <MoreHorizontal size={14} strokeWidth={1.8} />
        </button>
      </div>
    </header>
  );
}
