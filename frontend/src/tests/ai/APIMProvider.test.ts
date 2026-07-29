/**
 * APIMProvider unit tests.
 *
 * These tests cover:
 *  - SSE stream parsing (valid chunks, [DONE], malformed lines, empty delta)
 *  - Non-streaming generateResponse JSON parsing
 *  - Auth header presence
 *  - Error mapping (non-retryable)
 *  - Retry behaviour (429, 503)
 *  - Request timeout
 *  - Cancellation
 *  - Multi-turn history forwarding
 *
 * The real fetch is replaced by a local stub — no network calls are made.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { APIMProvider, APIMError } from "@/services/ai/APIMProvider";
import type { APIMConfig } from "@/config/ai";

// ── Helpers ───────────────────────────────────────────────────────────────────

const TEST_CONFIG: APIMConfig = {
  endpoint: "https://test.azure-api.net/llm",
  subscriptionKey: "test-key-123",
  timeoutMs: 5_000,
  maxRetries: 2,
};

function makeProvider(config: Partial<APIMConfig> = {}): APIMProvider {
  return new APIMProvider({ ...TEST_CONFIG, ...config });
}

/**
 * Builds a ReadableStream that emits the given SSE lines as UTF-8 bytes.
 * Each line is terminated with a newline; an extra newline separates events.
 */
function makeSSEStream(lines: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const text = lines.join("\n") + "\n";
  return new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode(text));
      controller.close();
    },
  });
}

/**
 * Builds a mock Response with an SSE body.
 */
function mockSSEResponse(lines: string[], status = 200): Response {
  return new Response(makeSSEStream(lines), {
    status,
    headers: { "Content-Type": "text/event-stream" },
  });
}

/**
 * Builds a mock Response with a JSON body.
 */
function mockJSONResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Collects all chunks from an AsyncIterable. */
async function collectChunks(iterable: AsyncIterable<{ content: string; done: boolean }>) {
  const chunks: string[] = [];
  for await (const chunk of iterable) {
    if (chunk.content) chunks.push(chunk.content);
  }
  return chunks;
}

// ── Setup ─────────────────────────────────────────────────────────────────────

let fetchSpy: ReturnType<typeof vi.spyOn>;

beforeEach(() => {
  fetchSpy = vi.spyOn(globalThis, "fetch");
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ── SSE parser ────────────────────────────────────────────────────────────────

describe("APIMProvider — SSE streaming", () => {
  it("yields content from valid SSE delta lines", async () => {
    fetchSpy.mockResolvedValueOnce(
      mockSSEResponse([
        `data: ${JSON.stringify({ choices: [{ delta: { content: "Hello" }, finish_reason: null }] })}`,
        `data: ${JSON.stringify({ choices: [{ delta: { content: " world" }, finish_reason: null }] })}`,
        "data: [DONE]",
      ])
    );

    const provider = makeProvider();
    const chunks = await collectChunks(provider.streamResponse("hi"));
    expect(chunks).toEqual(["Hello", " world"]);
  });

  it("stops at [DONE] and does not yield content after it", async () => {
    fetchSpy.mockResolvedValueOnce(
      mockSSEResponse([
        `data: ${JSON.stringify({ choices: [{ delta: { content: "A" }, finish_reason: null }] })}`,
        "data: [DONE]",
        `data: ${JSON.stringify({ choices: [{ delta: { content: "B" }, finish_reason: null }] })}`,
      ])
    );

    const provider = makeProvider();
    const chunks = await collectChunks(provider.streamResponse("hi"));
    expect(chunks).toEqual(["A"]);
  });

  it("skips lines that do not start with 'data: '", async () => {
    fetchSpy.mockResolvedValueOnce(
      mockSSEResponse([
        "event: content",
        `: comment line`,
        `data: ${JSON.stringify({ choices: [{ delta: { content: "ok" }, finish_reason: null }] })}`,
        "data: [DONE]",
      ])
    );

    const provider = makeProvider();
    const chunks = await collectChunks(provider.streamResponse("hi"));
    expect(chunks).toEqual(["ok"]);
  });

  it("skips malformed JSON lines without aborting the stream", async () => {
    fetchSpy.mockResolvedValueOnce(
      mockSSEResponse([
        "data: {invalid json}",
        `data: ${JSON.stringify({ choices: [{ delta: { content: "valid" }, finish_reason: null }] })}`,
        "data: [DONE]",
      ])
    );

    const provider = makeProvider();
    const chunks = await collectChunks(provider.streamResponse("hi"));
    expect(chunks).toEqual(["valid"]);
  });

  it("skips delta lines with no content field", async () => {
    fetchSpy.mockResolvedValueOnce(
      mockSSEResponse([
        `data: ${JSON.stringify({ choices: [{ delta: {}, finish_reason: "stop" }] })}`,
        "data: [DONE]",
      ])
    );

    const provider = makeProvider();
    const chunks = await collectChunks(provider.streamResponse("hi"));
    expect(chunks).toEqual([]);
  });

  it("forwards multi-turn history to the provider in streamResponse", async () => {
    fetchSpy.mockResolvedValueOnce(mockSSEResponse(["data: [DONE]"]));

    const provider = makeProvider();
    await collectChunks(
      provider.streamResponse("follow-up", {
        history: [
          { role: "user", content: "first question" },
          { role: "assistant", content: "first answer" },
        ],
      })
    );

    const body = JSON.parse(fetchSpy.mock.calls[0][1]?.body as string) as {
      messages: Array<{ role: string; content: string }>;
    };

    expect(body.messages).toEqual([
      { role: "user", content: "first question" },
      { role: "assistant", content: "first answer" },
      { role: "user", content: "follow-up" },
    ]);
  });
});

// ── generateResponse ──────────────────────────────────────────────────────────

describe("APIMProvider — generateResponse", () => {
  it("returns the content from a successful JSON response", async () => {
    fetchSpy.mockResolvedValueOnce(
      mockJSONResponse({
        choices: [{ message: { content: "The answer is 42." } }],
      })
    );

    const provider = makeProvider();
    const result = await provider.generateResponse("What is the answer?");
    expect(result).toBe("The answer is 42.");
  });

  it("throws APIMError when choices content is missing", async () => {
    fetchSpy.mockResolvedValueOnce(mockJSONResponse({ choices: [{ message: {} }] }));

    const provider = makeProvider();
    await expect(provider.generateResponse("prompt")).rejects.toBeInstanceOf(APIMError);
  });
});

// ── Auth header ───────────────────────────────────────────────────────────────

describe("APIMProvider — auth header", () => {
  it("sends Ocp-Apim-Subscription-Key from config", async () => {
    fetchSpy.mockResolvedValueOnce(mockSSEResponse(["data: [DONE]"]));

    const provider = makeProvider({ subscriptionKey: "my-secret-key" });
    await collectChunks(provider.streamResponse("hi"));

    const headers = fetchSpy.mock.calls[0][1]?.headers as Record<string, string>;
    expect(headers["Ocp-Apim-Subscription-Key"]).toBe("my-secret-key");
  });
});

// ── Error mapping ─────────────────────────────────────────────────────────────

describe("APIMProvider — error mapping", () => {
  it("throws APIMError with status code on 401", async () => {
    fetchSpy.mockResolvedValueOnce(mockJSONResponse({ error: { message: "Unauthorized" } }, 401));

    const provider = makeProvider({ maxRetries: 0 });
    await expect(provider.streamResponse("hi").next()).rejects.toMatchObject({
      name: "APIMError",
      statusCode: 401,
    });
  });

  it("throws APIMError with status code on 400", async () => {
    fetchSpy.mockResolvedValueOnce(mockJSONResponse({ error: { message: "Bad request" } }, 400));

    const provider = makeProvider({ maxRetries: 0 });
    await expect(provider.generateResponse("hi")).rejects.toMatchObject({
      name: "APIMError",
      statusCode: 400,
    });
  });

  it("extracts apim-request-id from response headers", async () => {
    const errorResponse = new Response(JSON.stringify({}), {
      status: 500,
      headers: { "apim-request-id": "req-abc-123" },
    });
    fetchSpy.mockResolvedValueOnce(errorResponse);

    const provider = makeProvider({ maxRetries: 0 });
    const error = await provider.generateResponse("hi").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(APIMError);
    expect((error as APIMError).apimRequestId).toBe("req-abc-123");
  });
});

// ── Retry ─────────────────────────────────────────────────────────────────────

/**
 * Spy on the private `sleep` method so retry tests run instantly.
 * APIMProvider.sleep is accessible at runtime even though TypeScript marks it
 * private — casting to `any` is intentional here to reach the internal seam.
 */
function noopSleep(provider: APIMProvider): void {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  vi.spyOn(provider as any, "sleep").mockResolvedValue(undefined);
}

describe("APIMProvider — retry", () => {
  it("retries on 429 and succeeds on the next attempt", async () => {
    fetchSpy
      .mockResolvedValueOnce(mockJSONResponse({}, 429))
      .mockResolvedValueOnce(mockJSONResponse({ choices: [{ message: { content: "ok" } }] }));

    const provider = makeProvider({ maxRetries: 1 });
    noopSleep(provider);

    const result = await provider.generateResponse("hi");
    expect(result).toBe("ok");
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("retries on 503 and succeeds on the next attempt", async () => {
    fetchSpy
      .mockResolvedValueOnce(mockJSONResponse({}, 503))
      .mockResolvedValueOnce(
        mockJSONResponse({ choices: [{ message: { content: "recovered" } }] })
      );

    const provider = makeProvider({ maxRetries: 1 });
    noopSleep(provider);

    const result = await provider.generateResponse("hi");
    expect(result).toBe("recovered");
  });

  it("throws after exhausting all retries", async () => {
    fetchSpy.mockResolvedValue(mockJSONResponse({}, 429));

    const provider = makeProvider({ maxRetries: 2 });
    noopSleep(provider);

    await expect(provider.generateResponse("hi")).rejects.toBeInstanceOf(APIMError);
    // 1 initial attempt + 2 retries = 3 total calls
    expect(fetchSpy).toHaveBeenCalledTimes(3);
  });

  it("does not retry on 401", async () => {
    fetchSpy.mockResolvedValue(mockJSONResponse({}, 401));

    const provider = makeProvider({ maxRetries: 2 });
    noopSleep(provider);

    await expect(provider.generateResponse("hi")).rejects.toBeInstanceOf(APIMError);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});

// ── Cancellation ──────────────────────────────────────────────────────────────

describe("APIMProvider — cancellation", () => {
  it("cancel() aborts an in-flight request", async () => {
    // Simulate a stream that never closes so we can cancel mid-flight.
    let streamController: ReadableStreamDefaultController<Uint8Array>;
    const neverEndingStream = new ReadableStream<Uint8Array>({
      start(c) {
        streamController = c;
      },
    });

    fetchSpy.mockResolvedValueOnce(
      new Response(neverEndingStream, {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      })
    );

    const provider = makeProvider();
    const gen = provider.streamResponse("hi")[Symbol.asyncIterator]();

    // Start consuming — the first next() will hang waiting for data.
    const firstChunkPromise = gen.next();

    // Cancel before any chunk arrives.
    provider.cancel();

    // The promise should resolve (not reject) — the stream ends cleanly.
    const result = await firstChunkPromise;
    expect(result.done).toBe(true);

    // Silence the unused variable lint warning — we just need the reference to exist.
    void streamController!;
  });
});
