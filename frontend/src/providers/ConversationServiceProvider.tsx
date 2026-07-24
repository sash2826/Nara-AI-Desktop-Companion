import { useState, type ReactNode } from "react";
import { ConversationServiceContext } from "./ConversationServiceContext";
import { ConversationService } from "@/services/conversation/ConversationService";
import { createAIProvider } from "@/services/providers/ProviderFactory";
import { AI_CONFIG } from "@/config/ai";

interface ConversationServiceProviderProps {
  children: ReactNode;
}

/**
 * Creates and provides a single ConversationService instance to the React tree.
 *
 * Service lifetime is tied to this component's mount/unmount cycle, not the
 * module (no hidden global state). Swapping the AI provider requires only
 * changing AI_CONFIG.provider — no React component or hook changes.
 *
 * useState with a lazy initializer creates the service exactly once per mount.
 * Unlike useRef, this pattern is safe under the react-hooks/refs rule because
 * state (not a ref) is read during render.
 */
export function ConversationServiceProvider({ children }: ConversationServiceProviderProps) {
  const [service] = useState<ConversationService>(() => {
    const provider = createAIProvider(AI_CONFIG);
    return new ConversationService(provider);
  });

  return (
    <ConversationServiceContext.Provider value={service}>
      {children}
    </ConversationServiceContext.Provider>
  );
}
