import { useCallback, useContext } from "react";
import { ConversationServiceContext } from "@/providers/ConversationServiceContext";
import { ConversationIdContext } from "@/providers/ConversationIdContext";
import { ContextEngineContext } from "@/providers/ContextEngineContext";
import { useConversationStore } from "@/store/conversationStore";
import { IPCClient } from "@/services/ipc/IPCClient";
import type {
  ConversationCallbacks,
  ConversationTurn,
} from "@/services/conversation/ConversationService";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

/**
 * Thin bridge between ConversationService and the React UI.
 *
 * Responsibilities:
 * - Retrieve the ConversationService from React context.
 * - Map service callbacks to Zustand store mutations.
 * - Persist user and assistant messages to SQLite after each turn (Tauri only).
 * - Expose UI actions (sendMessage, clearMessages, setInputValue).
 *
 * This hook contains no business logic. Timing, streaming, cancellation,
 * and provider selection all live in ConversationService and LLMProvider.
 */
export function useConversation() {
  const service = useContext(ConversationServiceContext);
  const contextEngine = useContext(ContextEngineContext);
  const { conversationId, renew } = useContext(ConversationIdContext);
  const store = useConversationStore();

  if (service === null) {
    throw new Error("useConversation must be used within a ConversationServiceProvider.");
  }

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || store.isStreaming || store.isTyping) return;

      store.clearInput();

      // Capture completed turns before adding the new user message so that
      // history passed to the provider reflects only prior turns, not the
      // current one.
      const history: ConversationTurn[] = store.messages
        .filter((m) => m.status === "complete" && (m.role === "user" || m.role === "assistant"))
        .map((m) => ({ role: m.role as "user" | "assistant", content: m.content }));

      const userMessageId = store.addMessage("user", trimmed, "complete");

      // Persist the user message — fire-and-forget, never blocks the UI.
      if (IS_TAURI && conversationId) {
        IPCClient.saveMessage({
          messageId: userMessageId,
          conversationId,
          role: "user",
          content: trimmed,
          status: "complete",
        }).catch((err: unknown) => {
          console.warn("[useConversation] failed to persist user message:", err);
        });
      }

      // Snapshot workspace context before sending.
      const baseContext = contextEngine ? await contextEngine.getSnapshot() : undefined;

      // Retrieve semantically relevant document fragments (Tauri only).
      // Non-fatal — retrieval failures never block the conversation.
      let retrievedContext: string | null = null;
      if (IS_TAURI && conversationId) {
        try {
          const searchResponse = await IPCClient.searchSemantic(trimmed, 5);
          if (searchResponse.results.length > 0) {
            retrievedContext = searchResponse.results
              .map((r) => `[${r.document_path}]\n${r.content}`)
              .join("\n\n---\n\n");
          }
        } catch {
          // No index yet or search failed — proceed without retrieved context.
        }
      }

      const context = baseContext ? { ...baseContext, retrievedContext } : undefined;

      let assistantMessageId: string | null = null;
      let finalContent = "";

      const callbacks: ConversationCallbacks = {
        onTypingStart() {
          store.setTyping(true);
        },

        onTypingEnd() {
          store.setTyping(false);
        },

        onAssistantMessageCreate() {
          assistantMessageId = store.addMessage("assistant", "", "streaming");
          return assistantMessageId;
        },

        onStreamStart(messageId) {
          store.setStreaming(true, messageId);
        },

        onStreamChunk(messageId, accumulatedContent) {
          store.updateMessageContent(messageId, accumulatedContent);
          finalContent = accumulatedContent;
        },

        onStreamComplete(messageId) {
          store.updateMessageStatus(messageId, "complete");
          store.setStreaming(false);

          // Persist the completed assistant message — fire-and-forget.
          if (IS_TAURI && conversationId && assistantMessageId) {
            IPCClient.saveMessage({
              messageId: assistantMessageId,
              conversationId,
              role: "assistant",
              content: finalContent,
              status: "complete",
            }).catch((err: unknown) => {
              console.warn("[useConversation] failed to persist assistant message:", err);
            });
          }
        },

        onStreamCancelled(messageId) {
          store.updateMessageStatus(messageId, "complete");
          store.setStreaming(false);
          store.setTyping(false);
        },
      };

      await service.send(trimmed, callbacks, history, context);
    },
    [service, contextEngine, conversationId, store]
  );

  const clearMessages = useCallback(() => {
    service.cancel();
    store.clearMessages();
    // Generate a new conversation ID so the cleared history is not restored
    // from SQLite on the next app launch.
    if (IS_TAURI) renew();
  }, [service, store, renew]);

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
