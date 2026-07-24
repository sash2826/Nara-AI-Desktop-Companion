import type { LLMProvider, LLMRequestOptions, LLMStreamChunk } from "./LLMProvider";
import type { APIMConfig } from "@/config/ai";

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
 * - Streaming is implemented via the W3C Streams API (ReadableStream).
 * - AbortController / AbortSignal handle cooperative cancellation.
 * - All credentials arrive through APIMConfig — never hardcoded.
 */

// ─── Internal request / response types ────────────────────────────────────────

interface APIMChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

interface APIMRequestBody {
  messages: APIMChatMessage[];
  stream: boolean;
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

// ─── Provider ─────────────────────────────────────────────────────────────────

export class APIMProvider implements LLMProvider {
  private readonly config: APIMConfig;
  private abortController: AbortController | null = null;

  constructor(config: APIMConfig) {
    this.config = config;
  }

  // ─── generateResponse ──────────────────────────────────────────────────────

  async generateResponse(prompt: string, options?: LLMRequestOptions): Promise<string> {
    const controller = new AbortController();
    this.abortController = controller;

    const signal = options?.signal
      ? AbortSignal.any([options.signal, controller.signal])
      : controller.signal;

    try {
      const response = await this.fetchAPIM(this.buildRequestBody(prompt, false), signal);

      this.assertResponseOk(response);

      // ── TODO (Phase 01): Parse the APIM JSON response body.
      // The exact shape depends on the APIM policy response contract.
      // Example (OpenAI-compatible envelope):
      //   const json = await response.json();
      //   return json.choices[0].message.content as string;
      //
      // When APIM uses a custom envelope, update this parser accordingly.
      // The parser lives here — not in ConversationService — so the service
      // remains decoupled from the wire format.
      throw new APIMError("APIMProvider.generateResponse is not yet implemented.");
    } finally {
      this.abortController = null;
    }
  }

  // ─── streamResponse ────────────────────────────────────────────────────────

  async *streamResponse(
    prompt: string,
    options?: LLMRequestOptions
  ): AsyncIterable<LLMStreamChunk> {
    const controller = new AbortController();
    this.abortController = controller;

    const signal = options?.signal
      ? AbortSignal.any([options.signal, controller.signal])
      : controller.signal;

    try {
      const response = await this.fetchAPIM(this.buildRequestBody(prompt, true), signal);

      this.assertResponseOk(response);

      if (!response.body) {
        throw new APIMError("APIM returned an empty response body for a streaming request.");
      }

      // ── TODO (Phase 01): Implement Server-Sent Events parsing.
      //
      // APIM delivers streaming responses as SSE (text/event-stream).
      // Each event has the shape:
      //
      //   data: {"choices":[{"delta":{"content":"Hello"}}]}
      //   data: [DONE]
      //
      // Implementation outline:
      //
      //   const reader = response.body.getReader();
      //   const decoder = new TextDecoder();
      //   let buffer = "";
      //
      //   while (true) {
      //     const { done, value } = await reader.read();
      //     if (done || signal.aborted) break;
      //
      //     buffer += decoder.decode(value, { stream: true });
      //     const lines = buffer.split("\n");
      //     buffer = lines.pop() ?? "";
      //
      //     for (const line of lines) {
      //       if (!line.startsWith("data: ")) continue;
      //       const payload = line.slice(6).trim();
      //       if (payload === "[DONE]") return;
      //
      //       const parsed = JSON.parse(payload);
      //       const content = parsed.choices?.[0]?.delta?.content ?? "";
      //       if (content) yield { content, done: false };
      //     }
      //   }
      //
      // Adjust the SSE parser to match the envelope APIM policy emits.
      // The parser lives here — ConversationService and the hook are unaffected.

      yield { content: "", done: true };
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

  // ─── Private helpers ───────────────────────────────────────────────────────

  /**
   * Builds the request headers for APIM.
   *
   * Authentication uses an Ocp-Apim-Subscription-Key header.
   * In future phases this may be replaced by an Azure AD token obtained
   * through MSAL — that change is local to this method.
   *
   * Credentials are never hardcoded. They arrive through APIMConfig, which
   * is populated from environment variables or a secure configuration store.
   */
  private buildHeaders(): HeadersInit {
    return {
      "Content-Type": "application/json",
      // ── TODO (Phase 01): Supply the subscription key from environment config.
      // "Ocp-Apim-Subscription-Key": this.config.subscriptionKey,
      //
      // ── TODO (Phase 02): Replace with MSAL bearer token for AAD auth.
      // "Authorization": `Bearer ${await this.acquireToken()}`,
      //
      // ── TODO: Add correlation / tracing headers if required by APIM policy.
      // "X-Request-Id": generateRequestId(),
    };
  }

  /**
   * Builds the JSON request body sent to APIM.
   *
   * The shape must match the APIM policy's expected input contract.
   * If APIM normalises vendor-specific envelopes internally, this body
   * may be a simple common format regardless of the downstream model.
   */
  private buildRequestBody(prompt: string, stream: boolean): APIMRequestBody {
    return {
      messages: [{ role: "user", content: prompt }],
      stream,
    };
  }

  /**
   * Sends a POST request to the APIM LLM endpoint.
   *
   * Retry logic, timeout, and circuit breaking will be implemented in
   * Phase 01. For now the fetch is a single attempt.
   *
   * ── TODO (Phase 01): Add exponential backoff retry for 429 / 503.
   * ── TODO (Phase 01): Add request timeout via AbortSignal.timeout().
   * ── TODO (Phase 01): Add structured error logging with correlation IDs.
   */
  private async fetchAPIM(body: APIMRequestBody, signal: AbortSignal): Promise<Response> {
    // ── TODO (Phase 01): Populate this.config.endpoint from environment config.
    // The endpoint URL is never hardcoded. It arrives through APIMConfig.
    const endpoint = this.config.endpoint;

    return fetch(endpoint, {
      method: "POST",
      headers: this.buildHeaders(),
      body: JSON.stringify(body),
      signal,
    });
  }

  /**
   * Maps APIM HTTP error responses to typed APIMError instances.
   *
   * ── TODO (Phase 01): Parse APIM error envelopes for richer messages.
   * APIM returns structured error bodies (application/json) on 4xx/5xx.
   * Extract the APIM-Request-ID header for correlation with APIM logs.
   */
  private assertResponseOk(response: Response): void {
    if (!response.ok) {
      const apimRequestId = response.headers.get("apim-request-id") ?? undefined;
      throw new APIMError(
        `APIM request failed with status ${response.status}: ${response.statusText}`,
        response.status,
        apimRequestId
      );
    }
  }
}
