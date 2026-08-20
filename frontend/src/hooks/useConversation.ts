import { useCallback, useContext, useRef } from "react";
import { ConversationServiceContext } from "@/providers/ConversationServiceContext";
import { ConversationIdContext } from "@/providers/ConversationIdContext";
import { ContextEngineContext } from "@/providers/ContextEngineContext";
import { useConversationStore } from "@/store/conversationStore";
import { IPCClient } from "@/services/ipc/IPCClient";
import type { RetrievedChunk } from "@/services/context/ContextEngine";
import type { CitationMeta } from "@/types/conversation";
import type {
  ConversationCallbacks,
  ConversationTurn,
  ContextSnapshot,
} from "@/services/conversation/ConversationService";

// Retrieval configuration — mirrors backend context_assembler.py constants.
const RETRIEVAL_CANDIDATE_K = 20;
const RETRIEVAL_MAX_CHUNKS = 5;
const RETRIEVAL_MAX_CHARS = 12_000;
const RETRIEVAL_MIN_RRF_SCORE = 0.01; // min viable RRF: rank-1 semantic-only hit scores ~0.016
const RETRIEVAL_MIN_RERANK_SCORE = 0.08; // drop chunks with low blended score
// Raised from 0.01 — prevents chunks with no meaningful n-gram overlap from passing.
// The RRF position weight (0.3) can otherwise inflate scores for irrelevant chunks
// that happen to appear in search results for unrelated general-knowledge queries.
const RETRIEVAL_MIN_COSINE_SCORE = 0.08;

// Queries shorter than this word count or matching common conversational patterns
// are assumed to not require document retrieval.
const RETRIEVAL_MIN_WORDS = 4;
const CONVERSATIONAL_RE =
  /^(hi|hello|hey|thanks|thank you|ok|okay|yes|no|sure|great|good|bye|goodbye|how are you|what can you do|who are you|what('s| is) (the |your )?(time|date|day|weather|temperature)|what time is it|tell me a joke|are you (there|ready|okay)|can you help)\W*$/i;

// Queries that open with a generative verb signal intent to create from the model's
// own knowledge rather than recall from indexed files.
const GENERATIVE_RE =
  /^(write|create|generate|make|build|implement|code|draft|design|produce|give me|show me|explain|describe|define|list|calculate|convert|translate|fix|refactor|optimise|optimize|summarise|summarize|format|rewrite)\b/i;

// Phrases that explicitly anchor a query to the user's indexed documents.
// When present alongside a generative verb, retrieval is still warranted.
const DOCUMENT_ANCHOR_RE =
  /\b(from (the |my |our |this )?(doc(ument)?|file|report|pdf|spec|notes?|meeting|presentation|slide)|based on (the |my |our )?|according to (the |my |our )?|as (described|mentioned|defined|outlined|stated) in|in (the |my |our )?(doc(ument)?|file|report)|\.pdf|\.docx?|\.pptx?|\.txt|\.md)\b/i;

function needsRetrieval(query: string): boolean {
  const trimmed = query.trim();
  if (CONVERSATIONAL_RE.test(trimmed)) return false;
  // Skip retrieval for generative queries only when the user is not explicitly
  // referencing their own documents (e.g. "write a program based on the spec").
  if (GENERATIVE_RE.test(trimmed) && !DOCUMENT_ANCHOR_RE.test(trimmed)) return false;
  if (trimmed.split(/\s+/).length < RETRIEVAL_MIN_WORDS) return false;
  return true;
}

// Reranker blend weights — mirrors backend reranker.py.
const RERANK_COSINE_WEIGHT = 0.7;
const RERANK_POSITION_WEIGHT = 0.3;

// ---------------------------------------------------------------------------
// Heuristic reranker — character n-gram cosine + RRF position bonus.
// Mirrors HeuristicReranker in backend/capabilities/ai/reranker.py.
// ---------------------------------------------------------------------------

function tokenise(text: string): string[] {
  return text.toLowerCase().match(/\w+/g) ?? [];
}

function ngramTf(text: string, n = 2): Map<string, number> {
  const tokens = tokenise(text);
  const ngrams: string[] = [];
  for (const token of tokens) {
    if (token.length >= n) {
      for (let i = 0; i <= token.length - n; i++) ngrams.push(token.slice(i, i + n));
    } else {
      ngrams.push(token);
    }
  }
  const counts = new Map<string, number>();
  for (const g of ngrams) counts.set(g, (counts.get(g) ?? 0) + 1);
  const total = ngrams.length || 1;
  counts.forEach((v, k) => counts.set(k, v / total));
  return counts;
}

function cosine(a: Map<string, number>, b: Map<string, number>): number {
  if (a.size === 0 || b.size === 0) return 0;
  let dot = 0;
  b.forEach((v, k) => {
    dot += (a.get(k) ?? 0) * v;
  });
  const normA = Math.sqrt([...a.values()].reduce((s, v) => s + v * v, 0));
  const normB = Math.sqrt([...b.values()].reduce((s, v) => s + v * v, 0));
  return normA * normB > 0 ? dot / (normA * normB) : 0;
}

interface RankedCandidate {
  chunk_id: string;
  document_id: string;
  document_path: string;
  chunk_index: number;
  content: string;
  rrf_score: number;
  cosine_score: number;
  rerank_score: number;
}

function heuristicRerank(
  query: string,
  candidates: Array<{
    chunk_id: string;
    document_id: string;
    document_path: string;
    chunk_index: number;
    content: string;
    rrf_score: number;
  }>
): RankedCandidate[] {
  if (candidates.length === 0) return [];
  const queryVec = ngramTf(query);
  const maxRrf = Math.max(...candidates.map((c) => c.rrf_score)) || 1;

  return candidates
    .map((c) => {
      const cosine_score = cosine(queryVec, ngramTf(c.content));
      return {
        ...c,
        cosine_score,
        rerank_score:
          RERANK_COSINE_WEIGHT * cosine_score + RERANK_POSITION_WEIGHT * (c.rrf_score / maxRrf),
      };
    })
    .sort((a, b) => b.rerank_score - a.rerank_score);
}

const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

/**
 * Thin bridge between ConversationService and the React UI.
 *
 * Responsibilities:
 * - Retrieve the ConversationService from React context.
 * - Map service callbacks to Zustand store mutations.
 * - Persist user and assistant messages to SQLite after each turn (Tauri only).
 * - Expose UI actions (sendMessage, clearMessages, setInputValue).
 *
 * This hook contains no business logic. Timing, streaming, cancellation,
 * and provider selection all live in ConversationService and LLMProvider.
 */
export function useConversation() {
  const service = useContext(ConversationServiceContext);
  const contextEngine = useContext(ContextEngineContext);
  const { conversationId, renew } = useContext(ConversationIdContext);
  const store = useConversationStore();

  if (service === null) {
    throw new Error("useConversation must be used within a ConversationServiceProvider.");
  }

  // Cache the conversation summary per conversation ID so we only fetch it
  // once per session rather than on every message send.
  const summaryCache = useRef<Map<string, string | null>>(new Map());

  const getConversationSummary = useCallback(async (convId: string): Promise<string | null> => {
    if (!IS_TAURI || !convId) return null;
    if (summaryCache.current.has(convId)) {
      return summaryCache.current.get(convId) ?? null;
    }
    try {
      const memory = await IPCClient.getConversationMemory(convId);
      summaryCache.current.set(convId, memory.summary);
      return memory.summary;
    } catch {
      summaryCache.current.set(convId, null);
      return null;
    }
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || store.isStreaming || store.isTyping) return;

      store.clearInput();

      // Capture completed turns before adding the new user message so that
      // history passed to the provider reflects only prior turns, not the
      // current one.
      const history: ConversationTurn[] = store.messages
        .filter((m) => m.status === "complete" && (m.role === "user" || m.role === "assistant"))
        .map((m) => ({ role: m.role as "user" | "assistant", content: m.content }));

      const userMessageId = store.addMessage("user", trimmed, "complete");

      // Persist the user message — fire-and-forget, never blocks the UI.
      if (IS_TAURI && conversationId) {
        IPCClient.saveMessage({
          messageId: userMessageId,
          conversationId,
          role: "user",
          content: trimmed,
          status: "complete",
        }).catch((err: unknown) => {
          console.warn("[useConversation] failed to persist user message:", err);
        });
      }

      // Snapshot workspace context before sending.
      const baseContext = contextEngine ? await contextEngine.getSnapshot() : undefined;

      // Fetch stored conversation summary (cached after first load).
      const conversationSummary = conversationId
        ? await getConversationSummary(conversationId)
        : null;

      // Retrieve document context via hybrid search (keyword + semantic, RRF-merged).
      // Uses the active workspace folder from the context engine to scope results.
      // Non-fatal — failures never block the conversation.
      let retrievedChunks: RetrievedChunk[] | null = null;
      let retrievedContext: string | null = null;

      if (IS_TAURI && needsRetrieval(trimmed)) {
        try {
          const workspacePath = baseContext?.activeProjectFolder ?? undefined;
          const searchResponse = await IPCClient.searchHybrid(
            trimmed,
            RETRIEVAL_CANDIDATE_K,
            workspacePath
          );

          if (searchResponse.results.length > 0) {
            // Step 1: Rerank the 20 candidates by query-to-chunk relevance.
            // Mirrors HeuristicReranker in backend/capabilities/ai/reranker.py.
            const reranked = heuristicRerank(trimmed, searchResponse.results);

            // Step 2: Quality filter, deduplication, and character budget.
            // Mirrors ContextAssembler._filter_and_budget() on the backend.
            const seen = new Set<string>();
            const retained: RetrievedChunk[] = [];
            let totalChars = 0;

            for (const r of reranked) {
              if (r.rrf_score < RETRIEVAL_MIN_RRF_SCORE) continue;
              if (r.cosine_score < RETRIEVAL_MIN_COSINE_SCORE) continue;
              if (r.rerank_score < RETRIEVAL_MIN_RERANK_SCORE) continue;
              const key = `${r.document_id}:${r.chunk_index}`;
              if (seen.has(key)) continue;
              if (totalChars + r.content.length > RETRIEVAL_MAX_CHARS) break;
              if (retained.length >= RETRIEVAL_MAX_CHUNKS) break;

              seen.add(key);
              totalChars += r.content.length;
              retained.push({
                chunkId: r.chunk_id,
                documentId: r.document_id,
                documentPath: r.document_path,
                chunkIndex: r.chunk_index,
                content: r.content,
                rrfScore: r.rrf_score,
              });
            }

            if (retained.length > 0) {
              retrievedChunks = retained;
              retrievedContext = retained
                .map(
                  (c, i) =>
                    `[${i + 1}] Source: ${c.documentPath} (chunk ${c.chunkIndex})\n${c.content}`
                )
                .join("\n\n---\n\n");
            }
          }
        } catch {
          // No index yet or search failed — proceed without retrieved context.
        }
      }

      // Build the full context snapshot. Always populate so the service
      // receives a complete object regardless of whether signals are present.
      const context: ContextSnapshot = baseContext
        ? { ...baseContext, retrievedChunks, retrievedContext, conversationSummary }
        : {
            activeProjectFolder: null,
            recentDocuments: [],
            explicitContext: null,
            retrievedChunks,
            retrievedContext,
            conversationSummary,
          };

      let assistantMessageId: string | null = null;
      let finalContent = "";

      const callbacks: ConversationCallbacks = {
        onTypingStart() {
          store.setTyping(true);
        },

        onTypingEnd() {
          store.setTyping(false);
        },

        onAssistantMessageCreate() {
          assistantMessageId = store.addMessage("assistant", "", "streaming");
          return assistantMessageId;
        },

        onStreamStart(messageId) {
          store.setStreaming(true, messageId);
        },

        onStreamChunk(messageId, accumulatedContent) {
          store.updateMessageContent(messageId, accumulatedContent);
          finalContent = accumulatedContent;
          // Approximate token count: split on whitespace boundaries.
          // Mirrors the heuristic displayed in the streaming indicator.
          store.updateMessageTokenCount(
            messageId,
            accumulatedContent.split(/\s+/).filter(Boolean).length
          );
        },

        onStreamComplete(messageId) {
          store.updateMessageStatus(messageId, "complete");
          store.setStreaming(false);

          // Store all retrieved chunks as citations, preserving their original
          // 1-based position so inline [N] badges in the response map correctly.
          if (retrievedChunks && retrievedChunks.length > 0) {
            const citations: CitationMeta[] = retrievedChunks.map((c) => ({
              chunkId: c.chunkId,
              documentPath: c.documentPath,
              chunkIndex: c.chunkIndex,
              rrfScore: c.rrfScore,
            }));
            store.updateMessageCitations(messageId, citations);
          }

          // Persist the completed assistant message — fire-and-forget.
          if (IS_TAURI && conversationId && assistantMessageId) {
            IPCClient.saveMessage({
              messageId: assistantMessageId,
              conversationId,
              role: "assistant",
              content: finalContent,
              status: "complete",
            }).catch((err: unknown) => {
              console.warn("[useConversation] failed to persist assistant message:", err);
            });
          }
        },

        onStreamCancelled(messageId) {
          // Preserve partial response with cancelled status so the user can
          // read what was generated before they stopped the stream.
          store.updateMessageStatus(messageId, "cancelled");
          store.setStreaming(false);
          store.setTyping(false);

          // Persist the partial response so it survives app restart.
          if (IS_TAURI && conversationId && assistantMessageId && finalContent) {
            IPCClient.saveMessage({
              messageId: assistantMessageId,
              conversationId,
              role: "assistant",
              content: finalContent,
              status: "complete",
            }).catch((err: unknown) => {
              console.warn("[useConversation] failed to persist cancelled message:", err);
            });
          }
        },
      };

      await service.send(trimmed, callbacks, history, context);
    },
    [service, contextEngine, conversationId, store, getConversationSummary]
  );

  const cancelStream = useCallback(() => {
    service.cancel();
  }, [service]);

  const clearMessages = useCallback(() => {
    service.cancel();
    store.clearMessages();
    // Invalidate summary cache so the new conversation starts without stale memory.
    summaryCache.current.clear();
    // Generate a new conversation ID so the cleared history is not restored
    // from SQLite on the next app launch.
    if (IS_TAURI) renew();
  }, [service, store, renew]);

  return {
    messages: store.messages,
    isTyping: store.isTyping,
    isStreaming: store.isStreaming,
    inputValue: store.inputValue,
    setInputValue: store.setInputValue,
    cancelStream,
    clearMessages,
    sendMessage,
  };
}
