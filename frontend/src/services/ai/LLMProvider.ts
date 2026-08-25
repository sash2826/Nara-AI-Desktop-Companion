/**
 * Provider-agnostic LLM interface.
 *
 * LLMProvider represents the contract for conversational language model
 * communication only. It is intentionally scoped to LLMs to distinguish it
 * from future capability-specific interfaces such as:
 *   - EmbeddingProvider  (BGE-M3, text-embedding-ada-002)
 *   - OCRProvider        (PaddleOCR)
 *   - SpeechProvider     (Speech-to-Text / Text-to-Speech)
 *   - VisionProvider     (multimodal image understanding)
 *
 * The desktop application communicates exclusively through this interface.
 * It has no knowledge of which underlying model or vendor is active.
 *
 * In production, APIMProvider implements this interface and routes all
 * requests through Azure API Management. The underlying model (GPT, Claude,
 * Gemini, Mistral, Llama, etc.) is an APIM configuration detail invisible
 * to the desktop application.
 *
 * In development and testing, MockProvider implements this interface and
 * returns deterministic keyword-matched responses with no network calls.
 */

/** A single message in a multi-turn conversation, including tool roles. */
export interface ChatMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string | null;
  tool_calls?: Array<{
    id: string;
    type: "function";
    function: { name: string; arguments: string };
  }>;
  tool_call_id?: string;
}

/** OpenAI-compatible function tool definition. */
export interface ToolDefinition {
  type: "function";
  function: {
    name: string;
    description: string;
    parameters: {
      type: "object";
      properties: Record<string, { type: string; description: string }>;
      required?: string[];
    };
  };
}

/** A fully parsed tool call returned when the model invokes a function. */
export interface ParsedToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface LLMRequestOptions {
  /** Caller-supplied signal for cooperative cancellation. */
  signal?: AbortSignal;

  /**
   * Prior conversation turns for multi-turn context.
   * Providers that support conversation history (e.g. APIMProvider) will
   * include these in the request. Providers that do not (e.g. MockProvider)
   * may ignore this field.
   */
  history?: ChatMessage[];

  /**
   * Optional system message prepended before history and the user prompt.
   * Used by the Context Engine to inject workspace signals (active folder,
   * recent documents) into each request. Providers that do not support
   * system messages may ignore this field.
   */
  systemMessage?: string;

  /**
   * OpenAI-compatible tool definitions to pass with the request.
   * When provided the model may respond with tool calls instead of content.
   */
  tools?: ToolDefinition[];
}

export interface LLMStreamChunk {
  /** Incremental content fragment. */
  content: string;
  /** True on the final chunk — the response is complete. */
  done: boolean;
  /**
   * Set on the final chunk when the model responded with tool calls instead
   * of content (finish_reason === "tool_calls"). The content field will be
   * empty in this case.
   */
  toolCalls?: ParsedToolCall[];
}

export interface LLMProvider {
  /**
   * Returns the complete response for the given prompt.
   * Suitable for non-streaming use cases: summaries, classifications,
   * structured extraction, and single-turn Q&A.
   */
  generateResponse(prompt: string, options?: LLMRequestOptions): Promise<string>;

  /**
   * Returns an async iterable that yields response chunks as they arrive.
   * Consumers render partial output progressively as each chunk is received.
   * Consumers must break early or exhaust the iterable to free resources.
   */
  streamResponse(prompt: string, options?: LLMRequestOptions): AsyncIterable<LLMStreamChunk>;

  /**
   * Terminates any in-flight generation immediately.
   * Safe to call when no request is active.
   */
  cancel(): void;
}
