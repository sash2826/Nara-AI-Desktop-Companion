import { useCallback, useRef } from "react";
import { useConversationStore } from "@/store/conversationStore";
import { getMockResponse } from "@/components/assistant/MOCK_RESPONSES";

const TYPING_DELAY_MS = 600;
const STREAM_INTERVAL_MS = 18;

/**
 * Encapsulates mock conversation logic: typing indicator → streaming response.
 * When real AI services are connected, only this hook needs to change.
 */
export function useConversation() {
  const store = useConversationStore();
  // Token allows in-flight stream to be cancelled when a new message arrives.
  const cancelRef = useRef<boolean>(false);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || store.isStreaming || store.isTyping) return;

      // Cancel any in-progress stream.
      cancelRef.current = true;

      store.clearInput();
      store.addMessage("user", trimmed, "complete");

      // Show typing indicator.
      store.setTyping(true);
      cancelRef.current = false;

      await delay(TYPING_DELAY_MS);

      if (cancelRef.current) return;

      store.setTyping(false);

      const fullResponse = getMockResponse(trimmed);
      const assistantId = store.addMessage("assistant", "", "streaming");
      store.setStreaming(true, assistantId);

      // Simulate token-by-token streaming.
      let accumulated = "";
      for (const char of fullResponse) {
        if (cancelRef.current) break;
        accumulated += char;
        store.updateMessageContent(assistantId, accumulated);
        await delay(STREAM_INTERVAL_MS);
      }

      if (!cancelRef.current) {
        store.updateMessageStatus(assistantId, "complete");
        store.setStreaming(false);
      }
    },
    [store]
  );

  return {
    messages: store.messages,
    isTyping: store.isTyping,
    isStreaming: store.isStreaming,
    inputValue: store.inputValue,
    setInputValue: store.setInputValue,
    clearMessages: store.clearMessages,
    sendMessage,
  };
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
