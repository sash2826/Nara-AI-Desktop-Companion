import { MessageList } from "./MessageList";
import type { Message } from "@/types/conversation";

interface ConversationViewProps {
  messages: Message[];
  isTyping: boolean;
}

/**
 * Wraps MessageList with layout constraints.
 * Kept as a separate component so future features (date separators,
 * jump-to-bottom button, search highlighting) have a clear insertion point.
 */
export function ConversationView({ messages, isTyping }: ConversationViewProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <MessageList messages={messages} isTyping={isTyping} />
    </div>
  );
}
