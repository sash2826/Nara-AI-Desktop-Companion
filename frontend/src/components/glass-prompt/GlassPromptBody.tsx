import { useEffect, useCallback, useRef } from "react";
import { SendButton } from "@/components/assistant/SendButton";
import { MessageList } from "@/components/assistant/MessageList";
import { PromptInput } from "@/components/assistant/PromptInput";
import { useConversation } from "@/hooks/useConversation";
import { useOrbController } from "@/hooks/useOrbController";
import { OrbState } from "@/services/orb/OrbState";
import { cn } from "@/lib/utils";

/**
 * Inner content of the Glass Prompt.
 *
 * Wires the conversation UI to ConversationService via useConversation, and
 * drives the OrbStateMachine through the full conversation arc:
 *   Active → Processing → Streaming → Success → Active  (happy path)
 *   Active → Processing → Error → Active                (error path)
 *
 * The orb returns to Active (not Idle) after each turn because the Glass
 * Prompt stays open. It returns to Idle only when the prompt closes, which
 * is handled by OrbLayer's isOpen effect.
 */
export function GlassPromptBody({ className }: { className?: string }) {
  const { messages, isTyping, isStreaming, inputValue, setInputValue, sendMessage, clearMessages } =
    useConversation();
  const controller = useOrbController();

  // Track previous values to detect transitions
  const prevTyping = useRef(false);
  const prevStreaming = useRef(false);

  useEffect(() => {
    const wasTyping = prevTyping.current;
    const wasStreaming = prevStreaming.current;

    // Active → Processing: typing started
    if (!wasTyping && isTyping) {
      controller.onProcessingStart();
    }

    // Processing → Streaming: first chunk arrived
    if (!wasStreaming && isStreaming) {
      controller.onStreamingStart();
    }

    // Streaming → Success: stream completed
    if (wasStreaming && !isStreaming && !isTyping) {
      const state = controller.getState().orbState;
      if (state === OrbState.Streaming) {
        controller.onStreamingComplete();
        // Brief success state, then return to Active for the next message
        setTimeout(() => {
          controller.onReturnToActive();
        }, 800);
      }
    }

    prevTyping.current = isTyping;
    prevStreaming.current = isStreaming;
  }, [isTyping, isStreaming, controller]);

  const handleSend = useCallback(() => {
    void sendMessage(inputValue);
  }, [inputValue, sendMessage]);

  const handleStop = useCallback(() => {
    clearMessages();
  }, [clearMessages]);

  return (
    <div className={cn("flex flex-col max-h-[70vh]", className)}>
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-white/10 px-5 py-3 shrink-0">
        <span className="text-xs font-medium text-muted-foreground tracking-wide uppercase select-none">
          AI Companion
        </span>
      </div>

      {/* Message list — shown once the conversation has started */}
      {messages.length > 0 && (
        <div className="flex-1 overflow-hidden px-4 pt-2 min-h-0">
          <MessageList messages={messages} isTyping={isTyping} />
        </div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2 px-4 py-4 shrink-0">
        <PromptInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSend}
          disabled={isStreaming || isTyping}
          className="flex-1"
        />
        <SendButton
          canSend={!!inputValue.trim() && !isStreaming && !isTyping}
          isStreaming={isStreaming}
          onSend={handleSend}
          onStop={handleStop}
        />
      </div>

      {/* Footer hint */}
      <div className="flex items-center justify-end px-4 pb-3 shrink-0">
        <span className="text-[11px] text-muted-foreground/50 select-none">
          <kbd className="font-mono">Ctrl+Shift+Space</kbd> to toggle &nbsp;·&nbsp;{" "}
          <kbd className="font-mono">Esc</kbd> to close
        </span>
      </div>
    </div>
  );
}
