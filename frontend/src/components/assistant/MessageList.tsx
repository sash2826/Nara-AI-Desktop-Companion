import { useEffect, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";
import type { Message } from "@/types/conversation";

interface MessageListProps {
  messages: Message[];
  isTyping: boolean;
}

export function MessageList({ messages, isTyping }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new content arrives.
  useEffect(() => {
    const container = containerRef.current;
    const bottom = bottomRef.current;
    if (!container || !bottom) return;

    // Only auto-scroll when the user is near the bottom already.
    const isNearBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < 120;

    if (isNearBottom || isTyping) {
      bottom.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [messages, isTyping]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto py-3"
      role="log"
      aria-label="Conversation"
      aria-live="polite"
      aria-relevant="additions"
    >
      <div className="mx-auto w-full max-w-3xl">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {isTyping && <TypingIndicator key="typing" />}
        </AnimatePresence>

        <div ref={bottomRef} aria-hidden="true" />
      </div>
    </div>
  );
}
