import { useState, useEffect, type ReactNode } from "react";
import { ConversationServiceContext } from "./ConversationServiceContext";
import { ConversationService } from "@/services/conversation/ConversationService";
import { createLLMProvider } from "@/services/providers/ProviderFactory";
import { LLM_CONFIG } from "@/config/ai";
import { useConversationStore } from "@/store/conversationStore";

interface ConversationServiceProviderProps {
  children: ReactNode;
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
 */
export function ConversationServiceProvider({ children }: ConversationServiceProviderProps) {
  const [service] = useState<ConversationService>(() => {
    const provider = createLLMProvider(LLM_CONFIG);
    return new ConversationService(provider);
  });

  // Clear any stuck conversation state left over from HMR or a previous session.
  // Zustand store is module-level singleton — it persists across React remounts.
  useEffect(() => {
    const store = useConversationStore.getState();
    if (store.isTyping || store.isStreaming) {
      console.warn("[ConversationService] resetting stuck typing/streaming state on mount");
      store.setTyping(false);
      store.setStreaming(false);
    }
  }, []);

  return (
    <ConversationServiceContext.Provider value={service}>
      {children}
    </ConversationServiceContext.Provider>
  );
}
