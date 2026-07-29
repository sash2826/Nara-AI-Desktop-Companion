/**
 * useEmbedding hook tests.
 *
 * IPCClient is mocked — no Tauri runtime required.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useEmbedding } from "@/hooks/useEmbedding";

// ─── Mock IPCClient ───────────────────────────────────────────────────────────

const mockGenerateEmbedding = vi.fn();

vi.mock("@/services/ipc/IPCClient", () => ({
  IPCClient: {
    generateEmbedding: (...args: unknown[]) => mockGenerateEmbedding(...args),
  },
}));

// ─── Tests ────────────────────────────────────────────────────────────────────

const FAKE_VECTOR = Array.from({ length: 1024 }, (_, i) => i * 0.001);

describe("useEmbedding", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts with null embedding, no loading, no error", () => {
    const { result } = renderHook(() => useEmbedding());
    expect(result.current.embedding).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sets isLoading true while request is in flight", async () => {
    let resolveEmbedding!: (v: number[]) => void;
    mockGenerateEmbedding.mockReturnValue(
      new Promise<number[]>((res) => {
        resolveEmbedding = res;
      })
    );

    const { result } = renderHook(() => useEmbedding());

    act(() => {
      void result.current.embed("test");
    });

    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolveEmbedding(FAKE_VECTOR);
    });

    expect(result.current.isLoading).toBe(false);
  });

  it("stores the embedding on success", async () => {
    mockGenerateEmbedding.mockResolvedValueOnce(FAKE_VECTOR);

    const { result } = renderHook(() => useEmbedding());

    await act(async () => {
      await result.current.embed("hello");
    });

    expect(result.current.embedding).toEqual(FAKE_VECTOR);
    expect(result.current.error).toBeNull();
  });

  it("returns the vector from embed()", async () => {
    mockGenerateEmbedding.mockResolvedValueOnce(FAKE_VECTOR);

    const { result } = renderHook(() => useEmbedding());

    let returned: number[] | undefined;
    await act(async () => {
      returned = await result.current.embed("hello");
    });

    expect(returned).toEqual(FAKE_VECTOR);
  });

  it("sets error and resets isLoading on failure", async () => {
    mockGenerateEmbedding.mockRejectedValueOnce("Python sidecar is not yet ready");

    const { result } = renderHook(() => useEmbedding());

    await act(async () => {
      await result.current.embed("hello").catch(() => {});
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe("Python sidecar is not yet ready");
    expect(result.current.embedding).toBeNull();
  });

  it("clears previous error on new successful request", async () => {
    mockGenerateEmbedding.mockRejectedValueOnce("first error").mockResolvedValueOnce(FAKE_VECTOR);

    const { result } = renderHook(() => useEmbedding());

    await act(async () => {
      await result.current.embed("fail").catch(() => {});
    });
    expect(result.current.error).not.toBeNull();

    await act(async () => {
      await result.current.embed("success");
    });
    expect(result.current.error).toBeNull();
    expect(result.current.embedding).toEqual(FAKE_VECTOR);
  });
});
