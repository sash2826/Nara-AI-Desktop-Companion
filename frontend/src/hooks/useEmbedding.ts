/**
 * useEmbedding — hook for generating BGE-M3 embeddings via the Python sidecar.
 *
 * Thin wrapper around IPCClient.generateEmbedding. Manages loading and error
 * state so components do not need to handle the async lifecycle themselves.
 *
 * In Phase 01 this is a stub consumer — the retrieval layer in Phase 02 will
 * use it to embed user queries before vector search.
 */

import { useState, useCallback } from "react";
import { IPCClient } from "@/services/ipc/IPCClient";

export interface UseEmbeddingResult {
  /** The most recently generated embedding vector, or null if none yet. */
  embedding: number[] | null;
  /** True while the embedding request is in flight. */
  isLoading: boolean;
  /** Error message from the last failed request, or null. */
  error: string | null;
  /** Generate an embedding for the given text. */
  embed: (text: string) => Promise<number[]>;
}

export function useEmbedding(): UseEmbeddingResult {
  const [embedding, setEmbedding] = useState<number[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const embed = useCallback(async (text: string): Promise<number[]> => {
    setIsLoading(true);
    setError(null);

    try {
      const vector = await IPCClient.generateEmbedding(text);
      setEmbedding(vector);
      return vector;
    } catch (err: unknown) {
      const message = typeof err === "string" ? err : "Embedding generation failed";
      setError(message);
      throw new Error(message, { cause: err });
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { embedding, isLoading, error, embed };
}
