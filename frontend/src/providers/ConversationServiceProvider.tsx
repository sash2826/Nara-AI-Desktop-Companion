import { useState, useEffect, useCallback, type ReactNode } from "react";
import { ConversationServiceContext } from "./ConversationServiceContext";
import { ConversationIdContext, type ConversationIdContextValue } from "./ConversationIdContext";
import { ContextEngineContext } from "./ContextEngineContext";
import { ConversationService } from "@/services/conversation/ConversationService";
import { WorkspaceContextEngine } from "@/services/context/WorkspaceContextEngine";
import { createLLMProvider } from "@/services/providers/ProviderFactory";
import { APIMProvider } from "@/services/ai/APIMProvider";
import { LLM_CONFIG } from "@/config/ai";
import { useConversationStore } from "@/store/conversationStore";
import { useSettingsStore } from "@/store/settingsStore";
import { IPCClient } from "@/services/ipc/IPCClient";

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

interface ConversationServiceProviderProps {
  children: ReactNode;
}

function makeConversationId(): string {
  return `conv-${Date.now()}`;
}

/**
 * Creates and provides a single ConversationService instance to the React tree.
 *
 * Service lifetime is tied to this component's mount/unmount cycle — no hidden
 * global state. Switching between development (mock) and production (apim)
 * requires only changing LLM_CONFIG.provider.
 *
 * Conversation ID resolution (Tauri only):
 *   1. On mount, call listConversations() to find the most recent conversation.
 *   2. Use its ID so the session continues where it left off.
 *   3. Fall back to a freshly generated ID when no conversations exist yet.
 *   4. renew() replaces the ID with a new one — called by clearMessages() so
 *      the cleared history is not restored on the next app launch.
 *
 * In the browser (non-Tauri), a new ID is generated synchronously and renew()
 * is a no-op since there is no persistence layer.
 */
export function ConversationServiceProvider({ children }: ConversationServiceProviderProps) {
  const [llmProvider] = useState(() => createLLMProvider(LLM_CONFIG));
  const [service] = useState<ConversationService>(() => new ConversationService(llmProvider));
  const apiKeyVersion = useSettingsStore((s) => s.apiKeyVersion);

  const [contextEngine] = useState(() => new WorkspaceContextEngine());

  // null = resolving from SQLite; string = resolved (or newly generated).
  const [conversationId, setConversationId] = useState<string | null>(
    IS_TAURI ? null : makeConversationId()
  );

  const renew = useCallback(() => {
    setConversationId(makeConversationId());
  }, []);

  const conversationIdContextValue: ConversationIdContextValue = {
    conversationId,
    renew,
  };

  // Load the APIM subscription key from the OS keychain and inject it into the
  // provider. Must run before the first LLM call — fire-and-forget failures are
  // safe because requests will 401 without a key rather than using a stale one.
  useEffect(() => {
    if (!IS_TAURI || !(llmProvider instanceof APIMProvider)) return;

    IPCClient.loadCredential("eac", "apim-key")
      .then((key) => {
        if (key) (llmProvider as APIMProvider).setSubscriptionKey(key);
      })
      .catch((err: unknown) => {
        console.warn("[ConversationService] failed to load APIM key from keychain:", err);
      });
  }, [llmProvider, apiKeyVersion]);

  // Clear any stuck conversation state left over from HMR or a previous session.
  useEffect(() => {
    const store = useConversationStore.getState();
    if (store.isTyping || store.isStreaming) {
      console.warn("[ConversationService] resetting stuck typing/streaming state on mount");
      store.setTyping(false);
      store.setStreaming(false);
    }
  }, []);

  // On mount in Tauri: resolve the most recent conversation ID from SQLite,
  // then hydrate the store with its messages. Fire-and-forget — failures do
  // not block the UI; the user just starts a fresh conversation.
  useEffect(() => {
    if (!IS_TAURI) return;

    IPCClient.listConversations()
      .then((summaries) => {
        const resolvedId = summaries.length > 0 ? summaries[0].id : makeConversationId();
        setConversationId(resolvedId);

        return IPCClient.loadConversation(resolvedId).then((persisted) => {
          if (persisted.messages.length === 0) return;

          const store = useConversationStore.getState();
          if (store.messages.length > 1) return;

          for (const msg of persisted.messages) {
            store.addMessage(msg.role, msg.content, "complete");
          }
        });
      })
      .catch((err: unknown) => {
        console.warn("[ConversationService] failed to resolve conversation from persistence:", err);
        // Fall back to a fresh conversation so the app remains usable.
        setConversationId(makeConversationId());
      });
  }, []);

  return (
    <ConversationIdContext.Provider value={conversationIdContextValue}>
      <ContextEngineContext.Provider value={contextEngine}>
        <ConversationServiceContext.Provider value={service}>
          {children}
        </ConversationServiceContext.Provider>
      </ContextEngineContext.Provider>
    </ConversationIdContext.Provider>
  );
}
