import { createContext } from "react";
import type { ConversationService } from "@/services/conversation/ConversationService";

/**
 * Isolated context type file — no JSX, no components.
 * Required to satisfy react-refresh/only-export-components.
 *
 * Consumers call useConversationService() rather than reading this directly.
 */
export const ConversationServiceContext = createContext<ConversationService | null>(null);
