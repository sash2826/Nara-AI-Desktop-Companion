import { createContext } from "react";

/**
 * Provides the stable session conversation ID to the React tree.
 * Generated once per ConversationServiceProvider mount; persists for the
 * lifetime of the application session.
 */
export const ConversationIdContext = createContext<string | null>(null);
