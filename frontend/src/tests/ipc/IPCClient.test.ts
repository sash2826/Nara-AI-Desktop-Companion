/**
 * IPCClient unit tests.
 *
 * Covers:
 *  - healthCheck: successful response
 *  - healthCheck: invoke error propagation
 *  - waitForSidecar: resolves when sidecar-ready fires
 *  - waitForSidecar: rejects on timeout
 *
 * @tauri-apps/api/core and @tauri-apps/api/event are mocked — no Tauri
 * runtime is required.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ─── Module mocks ─────────────────────────────────────────────────────────────

const mockInvoke = vi.fn();
const mockListen = vi.fn();

vi.mock("@tauri-apps/api/core", () => ({
  invoke: (...args: unknown[]) => mockInvoke(...args),
}));

vi.mock("@tauri-apps/api/event", () => ({
  listen: (...args: unknown[]) => mockListen(...args),
}));

// Import after mocks are registered.
import { IPCClient, waitForSidecar } from "@/services/ipc/IPCClient";

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("IPCClient.healthCheck", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("resolves with status ok when invoke succeeds", async () => {
    mockInvoke.mockResolvedValueOnce({ status: "ok" });

    const result = await IPCClient.healthCheck();

    expect(result).toEqual({ status: "ok" });
    expect(mockInvoke).toHaveBeenCalledWith("health_check");
  });

  it("propagates errors thrown by invoke", async () => {
    mockInvoke.mockRejectedValueOnce("Python sidecar is not yet ready");

    await expect(IPCClient.healthCheck()).rejects.toMatch("Python sidecar is not yet ready");
  });
});

describe("IPCClient.saveMessage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("invokes save_message with the correct payload", async () => {
    const fakeResponse = {
      id: "msg-1",
      conversation_id: "conv-1",
      role: "user",
      content: "hello",
      status: "complete",
      created_at: "2026-07-29T12:00:00Z",
    };
    mockInvoke.mockResolvedValueOnce(fakeResponse);

    const result = await IPCClient.saveMessage({
      messageId: "msg-1",
      conversationId: "conv-1",
      role: "user",
      content: "hello",
      status: "complete",
    });

    expect(mockInvoke).toHaveBeenCalledWith("save_message", {
      messageId: "msg-1",
      conversationId: "conv-1",
      role: "user",
      content: "hello",
      status: "complete",
    });
    expect(result.id).toBe("msg-1");
  });

  it("propagates errors from invoke", async () => {
    mockInvoke.mockRejectedValueOnce("sidecar not ready");
    await expect(
      IPCClient.saveMessage({
        messageId: "m",
        conversationId: "c",
        role: "user",
        content: "x",
        status: "complete",
      })
    ).rejects.toMatch("sidecar not ready");
  });
});

describe("IPCClient.loadConversation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("invokes load_conversation and returns the response", async () => {
    const fakeResponse = { id: "conv-1", messages: [] };
    mockInvoke.mockResolvedValueOnce(fakeResponse);

    const result = await IPCClient.loadConversation("conv-1");

    expect(mockInvoke).toHaveBeenCalledWith("load_conversation", {
      conversationId: "conv-1",
    });
    expect(result).toEqual(fakeResponse);
  });

  it("propagates errors from invoke", async () => {
    mockInvoke.mockRejectedValueOnce("sidecar not ready");
    await expect(IPCClient.loadConversation("conv-1")).rejects.toMatch("sidecar not ready");
  });
});

describe("IPCClient.generateEmbedding", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("resolves with the embedding array when invoke succeeds", async () => {
    const fakeVector = Array.from({ length: 1024 }, (_, i) => i * 0.001);
    mockInvoke.mockResolvedValueOnce({ embedding: fakeVector, dim: 1024 });

    const result = await IPCClient.generateEmbedding("hello world");

    expect(result).toEqual(fakeVector);
    expect(result).toHaveLength(1024);
    expect(mockInvoke).toHaveBeenCalledWith("generate_embedding", { text: "hello world" });
  });

  it("propagates errors thrown by invoke", async () => {
    mockInvoke.mockRejectedValueOnce("Python sidecar is not yet ready");

    await expect(IPCClient.generateEmbedding("test")).rejects.toMatch(
      "Python sidecar is not yet ready"
    );
  });
});

describe("IPCClient.listConversations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("invokes list_conversations and returns summaries", async () => {
    const fakeSummaries = [
      { id: "conv-2", created_at: "2026-07-29T12:01:00Z", message_count: 5 },
      { id: "conv-1", created_at: "2026-07-28T09:00:00Z", message_count: 3 },
    ];
    mockInvoke.mockResolvedValueOnce(fakeSummaries);

    const result = await IPCClient.listConversations();

    expect(mockInvoke).toHaveBeenCalledWith("list_conversations");
    expect(result).toHaveLength(2);
    expect(result[0].id).toBe("conv-2");
    expect(result[0].message_count).toBe(5);
  });

  it("returns an empty array when no conversations exist", async () => {
    mockInvoke.mockResolvedValueOnce([]);

    const result = await IPCClient.listConversations();

    expect(result).toEqual([]);
  });

  it("propagates errors from invoke", async () => {
    mockInvoke.mockRejectedValueOnce("sidecar not ready");
    await expect(IPCClient.listConversations()).rejects.toMatch("sidecar not ready");
  });
});

describe("waitForSidecar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("resolves with the port when sidecar-ready fires", async () => {
    const unlisten = vi.fn();
    mockListen.mockImplementation((_event: string, handler: (e: { payload: number }) => void) => {
      // Fire the event in the next microtask so listen() has time to return.
      Promise.resolve().then(() => handler({ payload: 8765 }));
      return Promise.resolve(unlisten);
    });

    const port = await waitForSidecar(5_000);

    expect(port).toBe(8765);
    expect(mockListen).toHaveBeenCalledWith("sidecar-ready", expect.any(Function));
    // unlisten is called via the resolved listenPromise — allow microtasks to settle.
    await Promise.resolve();
    expect(unlisten).toHaveBeenCalled();
  });

  it("rejects with a timeout error when the event never fires", async () => {
    const unlisten = vi.fn();
    // listen never calls the handler.
    mockListen.mockResolvedValue(unlisten);

    const promise = waitForSidecar(1_000);

    // Advance past the timeout.
    vi.advanceTimersByTime(1_100);

    await expect(promise).rejects.toThrow("Sidecar did not become ready");
    // unlisten is called via the resolved listenPromise — allow microtasks to settle.
    await Promise.resolve();
    expect(unlisten).toHaveBeenCalled();
  });
});
