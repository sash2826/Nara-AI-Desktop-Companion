import { useState, useEffect, type ReactNode } from "react";
import { ConversationServiceContext } from "./ConversationServiceContext";
import { ConversationIdContext } from "./ConversationIdContext";
import { ContextEngineContext } from "./ContextEngineContext";
import { ConversationService } from "@/services/conversation/ConversationService";
import { WorkspaceContextEngine } from "@/services/context/WorkspaceContextEngine";
import { createLLMProvider } from "@/services/providers/ProviderFactory";
import { LLM_CONFIG } from "@/config/ai";
import { useConversationStore } from "@/store/conversationStore";
import { IPCClient } from "@/services/ipc/IPCClient";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

interface ConversationServiceProviderProps {
  children: ReactNode;
}

/** Generates a simple time-based conversation ID for the current session. */
function makeConversationId(): string {
  return `conv-${Date.now()}`;
}

/**
 * Creates and provides a single ConversationService instance to the React tree.
 *
 * Service lifetime is tied to this component's mount/unmount cycle — no hidden
 * global state. Switching between development (mock) and production (apim)
 * requires only changing LLM_CONFIG.provider. No React component, hook, or
 * service implementation needs modification.
 *
 * useState with a lazy initializer creates the service exactly once per mount.
 * On mount, any stuck isTyping/isStreaming state from a previous session is
 * cleared so the guard in useConversation does not block the first message.
 *
 * WorkspaceContextEngine is co-located here so the same engine instance is
 * shared across all consumers (useConversation, future retrieval hooks, etc.).
 * Phase 03 will extend this with full workspace event subscription.
 *
 * A stable conversationId is generated once per session and exposed via
 * ConversationIdContext so useConversation can persist messages without
 * needing its own ID generation logic.
 */
export function ConversationServiceProvider({ children }: ConversationServiceProviderProps) {
  const [service] = useState<ConversationService>(() => {
    const provider = createLLMProvider(LLM_CONFIG);
    return new ConversationService(provider);
  });

  const [contextEngine] = useState(() => new WorkspaceContextEngine());
  const [conversationId] = useState(() => makeConversationId());

  // Clear any stuck conversation state left over from HMR or a previous session.
  useEffect(() => {
    const store = useConversationStore.getState();
    if (store.isTyping || store.isStreaming) {
      console.warn("[ConversationService] resetting stuck typing/streaming state on mount");
      store.setTyping(false);
      store.setStreaming(false);
    }
  }, []);

  // On mount in Tauri: hydrate the store from the most recent persisted conversation.
  // Fire-and-forget — a failure here does not block the UI.
  useEffect(() => {
    if (!IS_TAURI) return;

    IPCClient.loadConversation(conversationId)
      .then((persisted) => {
        if (persisted.messages.length === 0) return;

        const store = useConversationStore.getState();
        // Only hydrate if the store has only the welcome message (i.e. fresh session).
        if (store.messages.length > 1) return;

        for (const msg of persisted.messages) {
          store.addMessage(msg.role, msg.content, "complete");
        }
      })
      .catch((err: unknown) => {
        console.warn("[ConversationService] failed to hydrate from persistence:", err);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ConversationIdContext.Provider value={conversationId}>
      <ContextEngineContext.Provider value={contextEngine}>
        <ConversationServiceContext.Provider value={service}>
          {children}
        </ConversationServiceContext.Provider>
      </ContextEngineContext.Provider>
    </ConversationIdContext.Provider>
  );
}
