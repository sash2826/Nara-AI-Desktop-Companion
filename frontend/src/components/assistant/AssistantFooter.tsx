import { PromptComposer } from "./PromptComposer";
import { cn } from "@/lib/utils";

interface AssistantFooterProps {
  inputValue: string;
  isStreaming: boolean;
  isTyping: boolean;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  onClear: () => void;
  hasMessages: boolean;
  suggestions?: string[];
  className?: string;
}

export function AssistantFooter({
  inputValue,
  isStreaming,
  isTyping,
  onInputChange,
  onSend,
  onStop,
  onClear,
  hasMessages,
  suggestions,
  className,
}: AssistantFooterProps) {
  return (
    <footer className={cn("flex flex-shrink-0 flex-col", className)} aria-label="Assistant footer">
      <PromptComposer
        value={inputValue}
        isStreaming={isStreaming}
        isTyping={isTyping}
        onChange={onInputChange}
        onSend={onSend}
        onStop={onStop}
        onClear={onClear}
        hasMessages={hasMessages}
        suggestions={suggestions}
      />
    </footer>
  );
}
