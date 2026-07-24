import { ContextBar } from "./ContextBar";
import { PromptComposer } from "./PromptComposer";
import { cn } from "@/lib/utils";

interface AssistantFooterProps {
  inputValue: string;
  isStreaming: boolean;
  isTyping: boolean;
  onInputChange: (value: string) => void;
  onSend: () => void;
  className?: string;
}

export function AssistantFooter({
  inputValue,
  isStreaming,
  isTyping,
  onInputChange,
  onSend,
  className,
}: AssistantFooterProps) {
  return (
    <footer className={cn("flex flex-shrink-0 flex-col", className)} aria-label="Assistant footer">
      <ContextBar />

      <PromptComposer
        value={inputValue}
        isStreaming={isStreaming}
        isTyping={isTyping}
        onChange={onInputChange}
        onSend={onSend}
      />
    </footer>
  );
}
