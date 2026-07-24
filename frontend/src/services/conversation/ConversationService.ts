import type { AIProvider } from "@/services/ai/AIProvider";

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
 * The service receives its AIProvider through constructor injection.
 * Swapping providers requires only passing a different implementation.
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
  private readonly provider: AIProvider;
  private abortController: AbortController | null = null;

  constructor(provider: AIProvider) {
    this.provider = provider;
  }

  /**
   * Sends a user prompt and streams the provider response.
   * Cancels any in-flight request before starting a new one.
   */
  async send(prompt: string, callbacks: ConversationCallbacks): Promise<void> {
    // Cancel any previous request before starting a new one.
    this.cancel();

    this.abortController = new AbortController();
    const { signal } = this.abortController;

    callbacks.onTypingStart();

    const assistantMessageId = callbacks.onAssistantMessageCreate();
    let accumulated = "";
    let streamStarted = false;

    try {
      const stream = this.provider.streamResponse(prompt, { signal });

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

      if (signal.aborted) {
        callbacks.onStreamCancelled(assistantMessageId);
      } else {
        callbacks.onStreamComplete(assistantMessageId);
      }
    } catch {
      // If the provider throws on cancellation, treat as cancelled.
      callbacks.onStreamCancelled(assistantMessageId);
    } finally {
      this.abortController = null;
    }
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
