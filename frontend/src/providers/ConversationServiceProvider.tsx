import { useState, type ReactNode } from "react";
import { ConversationServiceContext } from "./ConversationServiceContext";
import { ConversationService } from "@/services/conversation/ConversationService";
import { createLLMProvider } from "@/services/providers/ProviderFactory";
import { LLM_CONFIG } from "@/config/ai";

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
 * This pattern is safe under the react-hooks/refs ESLint rule because state
 * (not a ref) is read during render.
 */
export function ConversationServiceProvider({ children }: ConversationServiceProviderProps) {
  const [service] = useState<ConversationService>(() => {
    const provider = createLLMProvider(LLM_CONFIG);
    return new ConversationService(provider);
  });

  return (
    <ConversationServiceContext.Provider value={service}>
      {children}
    </ConversationServiceContext.Provider>
  );
}
