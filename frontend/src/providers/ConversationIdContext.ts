import { createContext } from "react";

export interface ConversationIdContextValue {
  /**
   * The active conversation ID.
   *
   * Null only during the brief startup window while the provider is resolving
   * the most-recent conversation from SQLite. Components and hooks must guard
   * IPC calls with `if (conversationId)`.
   */
  conversationId: string | null;
  /**
   * Replace the active conversation ID with a freshly generated one.
   *
   * Call this when the user clears the conversation so that the next session
   * does not restore the cleared history.
   */
  renew: () => void;
}

/**
 * Provides the active conversation ID and a way to start a new conversation.
 *
 * On startup the provider resolves the most recent persisted conversation ID
 * from SQLite (Tauri only). `renew()` generates a new ID, causing the next
 * messages to be written to a new SQLite row — used when the user clears the
 * conversation so history from prior sessions is not restored on restart.
 */
export const ConversationIdContext = createContext<ConversationIdContextValue>({
  conversationId: null,
  renew: () => {},
});
