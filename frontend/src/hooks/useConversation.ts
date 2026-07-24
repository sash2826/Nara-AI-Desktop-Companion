import { useCallback, useContext } from "react";
import { ConversationServiceContext } from "@/providers/ConversationServiceContext";
import { useConversationStore } from "@/store/conversationStore";
import type { ConversationCallbacks } from "@/services/conversation/ConversationService";

/**
 * Thin bridge between ConversationService and the React UI.
 *
 * Responsibilities:
 * - Retrieve the ConversationService from React context.
 * - Map service callbacks to Zustand store mutations.
 * - Expose UI actions (sendMessage, clearMessages, setInputValue).
 *
 * This hook contains no business logic. Timing, streaming, cancellation,
 * and provider selection all live in ConversationService and LLMProvider.
 */
export function useConversation() {
  const service = useContext(ConversationServiceContext);
  const store = useConversationStore();

  if (service === null) {
    throw new Error("useConversation must be used within a ConversationServiceProvider.");
  }

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || store.isStreaming || store.isTyping) return;

      store.clearInput();
      store.addMessage("user", trimmed, "complete");

      const callbacks: ConversationCallbacks = {
        onTypingStart() {
          store.setTyping(true);
        },

        onTypingEnd() {
          store.setTyping(false);
        },

        onAssistantMessageCreate() {
          return store.addMessage("assistant", "", "streaming");
        },

        onStreamStart(messageId) {
          store.setStreaming(true, messageId);
        },

        onStreamChunk(messageId, accumulatedContent) {
          store.updateMessageContent(messageId, accumulatedContent);
        },

        onStreamComplete(messageId) {
          store.updateMessageStatus(messageId, "complete");
          store.setStreaming(false);
        },

        onStreamCancelled(messageId) {
          store.updateMessageStatus(messageId, "complete");
          store.setStreaming(false);
          store.setTyping(false);
        },
      };

      await service.send(trimmed, callbacks);
    },
    [service, store]
  );

  const clearMessages = useCallback(() => {
    service.cancel();
    store.clearMessages();
  }, [service, store]);

  return {
    messages: store.messages,
    isTyping: store.isTyping,
    isStreaming: store.isStreaming,
    inputValue: store.inputValue,
    setInputValue: store.setInputValue,
    clearMessages,
    sendMessage,
  };
}
