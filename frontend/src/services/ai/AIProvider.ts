/**
 * Provider-agnostic AI interface.
 *
 * Every concrete provider (Mock, OpenAI, Claude, Ollama, Azure OpenAI,
 * Gemini, OpenRouter) must implement this interface. Business logic
 * never references concrete providers — only this contract.
 *
 * Design notes:
 * - `generateResponse` returns a complete response in one call.
 * - `streamResponse` yields response chunks as an async iterable,
 *   allowing the caller to render partial output progressively.
 * - `cancel` terminates any in-flight generation immediately.
 */

export interface AIRequestOptions {
  /** Caller-supplied signal for cooperative cancellation. */
  signal?: AbortSignal;
}

export interface AIStreamChunk {
  /** Incremental content fragment. */
  content: string;
  /** True on the final chunk — the response is complete. */
  done: boolean;
}

export interface AIProvider {
  /**
   * Returns the complete response for the given prompt.
   * Use for non-streaming use cases (summaries, classifications, etc.).
   */
  generateResponse(prompt: string, options?: AIRequestOptions): Promise<string>;

  /**
   * Returns an async iterable that yields response chunks as they arrive.
   * Consumers must `break` or let the iterable exhaust to free resources.
   */
  streamResponse(prompt: string, options?: AIRequestOptions): AsyncIterable<AIStreamChunk>;

  /**
   * Cancels any in-flight generation. Safe to call when idle.
   */
  cancel(): void;
}
