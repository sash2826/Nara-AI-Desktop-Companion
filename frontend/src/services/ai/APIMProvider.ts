import type { LLMProvider, LLMRequestOptions, LLMStreamChunk } from "./LLMProvider";
import type { APIMConfig } from "@/config/ai";

/**
 * In development (Vite dev server), requests are proxied through /apim-proxy
 * to bypass CORS. In production (Tauri bundle), requests go directly to the
 * configured endpoint.
 */
const IS_DEV = import.meta.env.DEV;

/**
 * Production LLMProvider implementation for Azure API Management (APIM).
 *
 * All LLM requests in production flow through APIM. The desktop application
 * has no knowledge of which underlying model is active. Model selection,
 * routing, rate limiting, authentication, and observability are APIM concerns.
 *
 * Switching the underlying model (GPT → Claude → Gemini → Mistral → Llama)
 * requires only APIM policy configuration. No desktop code changes.
 *
 * ─────────────────────────────────────────
 *  Desktop App → APIM → [Model of choice]
 * ─────────────────────────────────────────
 *
 * Architecture notes:
 * - The Fetch API is used directly. No vendor SDKs are imported.
 * - Streaming is implemented via the W3C Streams API (ReadableStream + SSE).
 * - AbortController / AbortSignal handle cooperative cancellation.
 * - All credentials arrive through APIMConfig — never hardcoded.
 * - Retryable errors (429, 503) use exponential backoff up to maxRetries.
 */

// ─── Internal request / response types ────────────────────────────────────────

export interface APIMChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

interface APIMRequestBody {
  model: string;
  messages: APIMChatMessage[];
  stream: boolean;
}

// OpenAI-compatible non-streaming response envelope.
interface APIMChatCompletion {
  choices: Array<{
    message: { content: string };
  }>;
}

// OpenAI-compatible streaming delta envelope.
interface APIMStreamDelta {
  choices: Array<{
    delta: { content?: string };
    finish_reason: string | null;
  }>;
}

// ─── Error types ──────────────────────────────────────────────────────────────

export class APIMError extends Error {
  constructor(
    message: string,
    public readonly statusCode?: number,
    public readonly apimRequestId?: string
  ) {
    super(message);
    this.name = "APIMError";
  }
}

// ─── Retry constants ──────────────────────────────────────────────────────────

const RETRYABLE_STATUS_CODES = new Set([429, 503]);
const BASE_BACKOFF_MS = 500;

// ─── Provider ─────────────────────────────────────────────────────────────────

export class APIMProvider implements LLMProvider {
  private readonly config: APIMConfig;
  private abortController: AbortController | null = null;

  constructor(config: APIMConfig) {
    this.config = config;
  }

  // ─── generateResponse ──────────────────────────────────────────────────────

  async generateResponse(
    prompt: string,
    options?: LLMRequestOptions & { history?: APIMChatMessage[] }
  ): Promise<string> {
    const controller = new AbortController();
    this.abortController = controller;

    const signal = options?.signal
      ? AbortSignal.any([options.signal, controller.signal])
      : controller.signal;

    try {
      const messages = this.buildMessages(prompt, options?.history, options?.systemMessage);
      const response = await this.fetchWithRetry(
        { model: this.config.model, messages, stream: false },
        signal
      );

      const rawText = await response.text();
      if (!rawText.trim()) {
        throw new APIMError("APIM returned an empty response body.");
      }
      let json: APIMChatCompletion;
      try {
        json = JSON.parse(rawText) as APIMChatCompletion;
      } catch {
        throw new APIMError(`APIM response is not valid JSON: ${rawText.slice(0, 200)}`);
      }
      const content = json.choices?.[0]?.message?.content;

      if (typeof content !== "string") {
        throw new APIMError("APIM response missing expected content field.");
      }

      return content;
    } finally {
      this.abortController = null;
    }
  }

  // ─── streamResponse ────────────────────────────────────────────────────────

  async *streamResponse(
    prompt: string,
    options?: LLMRequestOptions & { history?: APIMChatMessage[] }
  ): AsyncIterable<LLMStreamChunk> {
    const controller = new AbortController();
    this.abortController = controller;

    const signal = options?.signal
      ? AbortSignal.any([options.signal, controller.signal])
      : controller.signal;

    try {
      const messages = this.buildMessages(prompt, options?.history, options?.systemMessage);

      // In dev the proxy buffers the full upstream body before responding, so
      // SSE streaming is unavailable. Request non-streaming JSON and simulate
      // word-by-word locally so the UI animation still works.
      // In production (Tauri bundle) the request goes directly to APIM and
      // true SSE streaming is used.
      const useStreaming = !IS_DEV;

      const response = await this.fetchWithRetry(
        { model: this.config.model, messages, stream: useStreaming },
        signal
      );

      // Always read via text() first — response.json() fails when the proxy
      // forwards chunked-encoding headers that the browser cannot decode.
      const rawText = await response.text();

      if (!rawText.trim()) {
        throw new APIMError("APIM returned an empty response body.");
      }

      // Detect SSE vs JSON.
      // SSE bodies contain "data:" lines — they may be preceded by "event:" or
      // comment lines, so we check for a "data:" line anywhere in the text
      // rather than requiring it at the very start.
      if (/^data:/m.test(rawText)) {
        yield* this.parseSSEText(rawText, signal);
        return;
      }

      // Plain JSON response (stream:false or APIM ignoring stream flag)
      let json: APIMChatCompletion;
      try {
        json = JSON.parse(rawText) as APIMChatCompletion;
      } catch {
        throw new APIMError(`APIM response is not valid JSON: ${rawText.slice(0, 200)}`);
      }
      const content = json.choices?.[0]?.message?.content;
      if (typeof content !== "string") {
        throw new APIMError("APIM response missing expected content field.");
      }
      yield* this.simulateStream(content, signal);
    } finally {
      this.abortController = null;
    }
  }

  // ─── cancel ────────────────────────────────────────────────────────────────

  cancel(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Yields a pre-fetched string word-by-word to simulate streaming in dev.
   * Used when the Vite proxy buffers the response before delivery.
   */
  private async *simulateStream(
    content: string,
    signal: AbortSignal
  ): AsyncIterable<LLMStreamChunk> {
    const words = content.split(" ");
    for (let i = 0; i < words.length; i++) {
      if (signal.aborted) return;
      const chunk = i === 0 ? words[i] : " " + words[i];
      yield { content: chunk, done: false };
      await new Promise<void>((resolve) => setTimeout(resolve, 18));
    }
  }

  /**
   * Parses a complete SSE response string chunk-by-chunk.
   *
   * Yields a microtask between each SSE event so that an AbortSignal fired
   * mid-parse (e.g. from the Stop button) is honoured promptly rather than
   * being processed only after the entire string has been consumed.
   */
  private async *parseSSEText(text: string, signal?: AbortSignal): AsyncIterable<LLMStreamChunk> {
    const lines = text.split("\n");
    for (const line of lines) {
      if (signal?.aborted) return;

      const trimmed = line.trimEnd();
      if (!trimmed.startsWith("data: ")) continue;

      const payload = trimmed.slice(6).trim();
      if (payload === "[DONE]") return;
      if (!payload) continue;

      let parsed: APIMStreamDelta;
      try {
        parsed = JSON.parse(payload) as APIMStreamDelta;
      } catch {
        continue;
      }

      const content = parsed.choices?.[0]?.delta?.content;
      if (content) {
        yield { content, done: false };
        // Yield to the event loop so abort signals and UI updates land between chunks.
        await new Promise<void>((resolve) => setTimeout(resolve, 0));
      }
    }
  }

  // ─── Retry logic ──────────────────────────────────────────────────────────

  /**
   * Sends a POST request to APIM with exponential backoff retry.
   *
   * Retryable: 429 (rate limit), 503 (service unavailable).
   * Non-retryable: 400, 401, 403, 404, 422, 5xx (except 503).
   *
   * Backoff: BASE_BACKOFF_MS × 2^attempt (500 ms, 1 s, 2 s, …)
   * capped at maxRetries from APIMConfig.
   */
  private async fetchWithRetry(body: APIMRequestBody, signal: AbortSignal): Promise<Response> {
    let lastError: APIMError | null = null;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      if (attempt > 0) {
        const delayMs = BASE_BACKOFF_MS * Math.pow(2, attempt - 1);
        await this.sleep(delayMs, signal);
      }

      const response = await this.fetchAPIM(body, signal);

      if (response.ok) return response;

      if (RETRYABLE_STATUS_CODES.has(response.status) && attempt < this.config.maxRetries) {
        lastError = await this.buildError(response);
        continue;
      }

      // Non-retryable or retries exhausted — throw immediately.
      throw await this.buildError(response);
    }

    throw lastError ?? new APIMError("APIM request failed after retries.");
  }

  // ─── Private helpers ───────────────────────────────────────────────────────

  /**
   * Builds the ordered message array sent to APIM.
   *
   * Structure:
   *   1. Optional system message (workspace context), prepended before history.
   *   2. Optional prior turns (history), oldest first.
   *   3. Current user prompt.
   */
  private buildMessages(
    prompt: string,
    history?: APIMChatMessage[],
    systemMessage?: string
  ): APIMChatMessage[] {
    const messages: APIMChatMessage[] = [];
    if (systemMessage) {
      messages.push({ role: "system", content: systemMessage });
    }
    if (history) {
      messages.push(...history);
    }
    messages.push({ role: "user", content: prompt });
    return messages;
  }

  /**
   * Builds the request headers for APIM.
   *
   * Authentication uses an Ocp-Apim-Subscription-Key header.
   * This will be replaced by an Azure AD bearer token in Phase 02.
   */
  private buildHeaders(): HeadersInit {
    return {
      "Content-Type": "application/json",
      "api-key": this.config.subscriptionKey,
    };
  }

  /**
   * Sends a single POST request to APIM.
   *
   * In development the Vite dev server proxies /apim-proxy/* → APIM, so the
   * request appears same-origin and CORS is not triggered. In production the
   * full APIM endpoint is used directly from the Tauri process.
   */
  private async fetchAPIM(body: APIMRequestBody, signal: AbortSignal): Promise<Response> {
    const timeoutSignal = AbortSignal.timeout(this.config.timeoutMs);
    const combinedSignal = AbortSignal.any([signal, timeoutSignal]);
    const url = IS_DEV ? "/apim-proxy" : this.config.endpoint;

    return fetch(url, {
      method: "POST",
      headers: this.buildHeaders(),
      body: JSON.stringify(body),
      signal: combinedSignal,
    });
  }

  /**
   * Builds a typed APIMError from a non-OK response.
   *
   * Attempts to extract a structured error message from the APIM JSON envelope.
   * Falls back to the HTTP status text when the body is not parseable.
   */
  private async buildError(response: Response): Promise<APIMError> {
    const apimRequestId = response.headers.get("apim-request-id") ?? undefined;

    let message = `APIM request failed: ${response.status} ${response.statusText}`;
    try {
      const body = (await response.clone().json()) as {
        error?: { message?: string };
        message?: string;
      };
      const extracted = body.error?.message ?? body.message;
      if (extracted) message = extracted;
    } catch {
      // Body is not JSON — use the HTTP status text fallback above.
    }

    return new APIMError(message, response.status, apimRequestId);
  }

  /**
   * Returns a promise that resolves after `ms` milliseconds.
   * Rejects immediately if the signal is aborted during the wait.
   */
  private sleep(ms: number, signal: AbortSignal): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      if (signal.aborted) {
        reject(new DOMException("Aborted", "AbortError"));
        return;
      }
      const timer = setTimeout(resolve, ms);
      signal.addEventListener(
        "abort",
        () => {
          clearTimeout(timer);
          reject(new DOMException("Aborted", "AbortError"));
        },
        { once: true }
      );
    });
  }
}
