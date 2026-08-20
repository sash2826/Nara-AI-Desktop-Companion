import { MessageList } from "./MessageList";
import { EmptyChatState } from "./EmptyChatState";
import type { Message } from "@/types/conversation";

interface ConversationViewProps {
  messages: Message[];
  isTyping: boolean;
  onQuickPrompt: (text: string) => void;
}

/**
 * Wraps MessageList with layout constraints.
 * Kept as a separate component so future features (date separators,
 * jump-to-bottom button, search highlighting) have a clear insertion point.
 */
export function ConversationView({ messages, isTyping, onQuickPrompt }: ConversationViewProps) {
  const isEmpty = messages.length === 0 && !isTyping;

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      {isEmpty ? (
        <EmptyChatState onQuickPrompt={onQuickPrompt} />
      ) : (
        <MessageList messages={messages} isTyping={isTyping} />
      )}
    </div>
  );
}
