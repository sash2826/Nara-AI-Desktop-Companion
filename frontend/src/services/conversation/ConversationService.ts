import type { LLMProvider } from "@/services/ai/LLMProvider";
import type { APIMChatMessage } from "@/services/ai/APIMProvider";
import type { ContextSnapshot } from "@/services/context/ContextEngine";

export type { ContextSnapshot } from "@/services/context/ContextEngine";

/**
 * A prior conversation turn passed to the provider for multi-turn context.
 * Mirrors APIMChatMessage so ConversationService stays decoupled from
 * APIM-specific types at the call site — the cast happens here.
 */
export interface ConversationTurn {
  role: "user" | "assistant";
  content: string;
}

/**
 * ConversationService owns all conversation business logic.
 *
 * This class is completely framework-independent:
 * - No React imports.
 * - No Zustand imports.
 * - No JSX.
 * - No DOM APIs.
 *
 * It communicates results back to the caller through the ConversationCallbacks
 * interface, which the React layer (useConversation) implements using Zustand
 * store mutations. This inversion keeps the service decoupled from the UI.
 *
 * The service receives its LLMProvider through constructor injection.
 * Swapping providers (Mock ↔ APIM) requires only passing a different
 * implementation — this class never changes.
 */

export interface ConversationCallbacks {
  /** Called once before the provider begins generating a response. */
  onTypingStart(): void;

  /** Called when the provider produces the first chunk. */
  onTypingEnd(): void;

  /** Called when streaming begins. messageId identifies the message slot. */
  onStreamStart(messageId: string): void;

  /** Called for each incremental chunk of content. */
  onStreamChunk(messageId: string, accumulatedContent: string): void;

  /** Called when the full response has been delivered. */
  onStreamComplete(messageId: string): void;

  /** Called if the stream is cancelled before completion. */
  onStreamCancelled(messageId: string): void;

  /**
   * Called when the service needs a new message slot for the assistant response.
   * The callback must create the message and return its ID so the service can
   * reference it in subsequent chunk/complete/cancelled events.
   */
  onAssistantMessageCreate(): string;
}

export class ConversationService {
  private readonly provider: LLMProvider;
  private abortController: AbortController | null = null;

  constructor(provider: LLMProvider) {
    this.provider = provider;
  }

  /**
   * Sends a user prompt and streams the provider response.
   * Cancels any in-flight request before starting a new one.
   *
   * `history` is the ordered list of prior turns in the current conversation.
   * It is forwarded to the provider so APIM receives full multi-turn context.
   * MockProvider ignores it (keyword matching is prompt-only).
   *
   * `context` is injected as a system message so the model is aware of the
   * user's active workspace folder and recently accessed documents.
   */
  async send(
    prompt: string,
    callbacks: ConversationCallbacks,
    history?: ConversationTurn[],
    context?: ContextSnapshot
  ): Promise<void> {
    // Cancel any previous request before starting a new one.
    this.cancel();

    this.abortController = new AbortController();
    const { signal } = this.abortController;

    callbacks.onTypingStart();

    const assistantMessageId = callbacks.onAssistantMessageCreate();
    let accumulated = "";
    let streamStarted = false;

    try {
      const apimHistory = history?.map<APIMChatMessage>((t) => ({
        role: t.role,
        content: t.content,
      }));

      const systemMessage = this.buildSystemMessage(context);
      const stream = this.provider.streamResponse(prompt, {
        signal,
        history: apimHistory,
        systemMessage,
      });

      for await (const chunk of stream) {
        if (signal.aborted) {
          break;
        }

        if (!streamStarted) {
          // First chunk: transition from typing to streaming.
          callbacks.onTypingEnd();
          callbacks.onStreamStart(assistantMessageId);
          streamStarted = true;
        }

        if (!chunk.done) {
          accumulated += chunk.content;
          callbacks.onStreamChunk(assistantMessageId, accumulated);
        }
      }

      // Ensure typing indicator is cleared even if no chunks arrived.
      if (!streamStarted) {
        callbacks.onTypingEnd();
        callbacks.onStreamStart(assistantMessageId);
      }

      if (signal.aborted) {
        callbacks.onStreamCancelled(assistantMessageId);
      } else {
        callbacks.onStreamComplete(assistantMessageId);
      }
    } catch (err) {
      console.error("[AI] request failed:", err instanceof Error ? err.message : err);
      // Ensure typing/streaming state is always cleared on error.
      if (!streamStarted) callbacks.onTypingEnd();
      callbacks.onStreamCancelled(assistantMessageId);
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Builds an optional system message from a context snapshot.
   * Returns undefined when the snapshot carries no meaningful signals so
   * the provider sends no system message rather than an empty one.
   */
  private buildSystemMessage(context?: ContextSnapshot): string | undefined {
    if (!context) return undefined;

    const parts: string[] = [];
    if (context.activeProjectFolder) {
      parts.push(`Active folder: ${context.activeProjectFolder}`);
    }
    if (context.recentDocuments.length > 0) {
      parts.push(`Recent files: ${context.recentDocuments.join(", ")}`);
    }
    if (context.explicitContext) {
      parts.push(context.explicitContext);
    }

    return parts.length > 0 ? parts.join(". ") + "." : undefined;
  }

  /**
   * Cancels the active stream. Safe to call when no stream is in progress.
   */
  cancel(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.provider.cancel();
  }
}
