import { createContext } from "react";
import type { ContextEngine } from "@/services/context/ContextEngine";

/**
 * Provides the active ContextEngine instance to the React tree.
 * ConversationServiceProvider supplies WorkspaceContextEngine in production.
 * Tests may supply NullContextEngine or a custom stub.
 */
export const ContextEngineContext = createContext<ContextEngine | null>(null);
