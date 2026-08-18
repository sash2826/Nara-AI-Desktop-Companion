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
   * Builds a structured system message from a context snapshot.
   *
   * When retrieved chunks are present the message instructs the LLM to:
   * - Synthesise across all provided excerpts rather than echoing one.
   * - Cite every factual claim using the exact source path in the format
   *   `[path/to/file]` immediately after the claim.
   * - Distinguish clearly between knowledge-base facts and general knowledge.
   *
   * Returns undefined when the snapshot carries no meaningful signals so
   * the provider sends no system message rather than an empty one.
   */
  private buildSystemMessage(context?: ContextSnapshot): string | undefined {
    if (!context) return undefined;

    const parts: string[] = [];

    // Prepend compressed prior-session memory so the LLM can reference earlier
    // conclusions without re-reading the full message history.
    if (context.conversationSummary) {
      parts.push(
        `CONVERSATION MEMORY (compressed summary of earlier turns):\n${context.conversationSummary}`
      );
    }

    if (context.activeProjectFolder) {
      parts.push(`Active workspace folder: ${context.activeProjectFolder}`);
    }
    if (context.explicitContext) {
      parts.push(context.explicitContext);
    }

    // Prefer typed chunks (Epic 4.0+) — fall back to the legacy flat string
    // so this method stays compatible with callers that predate Epic 4.0.
    const hasChunks = context.retrievedChunks && context.retrievedChunks.length > 0;
    const hasLegacyContext = !hasChunks && Boolean(context.retrievedContext);

    if (hasChunks && context.retrievedChunks) {
      const excerptBlock = context.retrievedChunks
        .map((c, i) => {
          const filename = c.documentPath.replace(/\\/g, "/").split("/").at(-1) ?? c.documentPath;
          return `[${i + 1}] ${filename}\n${c.content}`;
        })
        .join("\n\n---\n\n");

      parts.push(
        `You are an AI assistant with access to the user's indexed knowledge base.\n` +
          `The following document excerpts were retrieved and ranked by relevance to the user's query.\n` +
          `Excerpt [1] is the most relevant; lower-numbered excerpts should be weighted accordingly,\n` +
          `but you MUST synthesise across all of them — do not ignore later excerpts.\n\n` +
          `CITATION RULES — you MUST follow ALL of these exactly:\n` +
          `1. Cite sources using their excerpt number in square brackets immediately after the claim, e.g. [1] or [2].\n` +
          `   Do NOT include file paths or folder names in your response — the UI displays sources separately.\n` +
          `2. Synthesise across ALL provided excerpts — do not rely on only the first one.\n` +
          `3. If excerpts conflict, surface the contradiction explicitly.\n` +
          `4. Clearly distinguish between information from the excerpts and your general knowledge.\n` +
          `5. If the excerpts do not contain enough information to answer, say so — do NOT fill gaps with invented details.\n\n` +
          `Retrieved excerpts (ordered by relevance, most relevant first):\n\n${excerptBlock}`
      );
    } else if (hasLegacyContext && context.retrievedContext) {
      parts.push(
        `The following document excerpts were retrieved from the user's indexed knowledge base.\n` +
          `You may ONLY cite file paths that appear verbatim in the excerpts below — do not invent any paths.\n` +
          `When answering, cite the exact file path in square brackets after each factual claim.\n\n` +
          `Retrieved excerpts:\n${context.retrievedContext}`
      );
    } else {
      // No retrieved context — allow the LLM to respond naturally.
      // For conversational messages ("hello", "hi", general questions) the model
      // should answer helpfully. For document-specific queries it can note that
      // nothing has been indexed yet without being forced into a single template.
      parts.push(
        `You are a helpful AI assistant. You also have access to the user's indexed knowledge base, ` +
          `but no relevant documents were found for this query.\n` +
          `If the user is asking a conversational or general question, answer it helpfully.\n` +
          `If the user is asking about specific documents or files, let them know nothing has been indexed yet.\n` +
          `Do NOT invent or reference any file names or paths.`
      );
    }

    return parts.length > 0 ? parts.join("\n\n") : undefined;
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
