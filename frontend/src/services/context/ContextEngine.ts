/**
 * A single retrieved document chunk included in the context payload.
 * Carries both content and provenance so the system message can include
 * accurate citations that the LLM is instructed to reproduce.
 */
export interface RetrievedChunk {
  chunkId: string;
  documentId: string;
  documentPath: string;
  chunkIndex: number;
  content: string;
  /** RRF score from the hybrid search pipeline (higher = more relevant). */
  rrfScore: number;
}

/**
 * Snapshot of the user's current workspace context, produced by the Context Engine
 * and consumed by the Conversation Service on each request.
 *
 * Fields that are not yet available return null or an empty array. The Conversation
 * Service must treat all fields as optional — a partial snapshot is valid.
 */
export interface ContextSnapshot {
  /** Absolute path of the folder the user is currently treating as their active project. */
  activeProjectFolder: string | null;
  /** Paths of documents the user has opened recently, most recent first. */
  recentDocuments: string[];
  /** Context the user has explicitly provided for this session (e.g. a pasted document). */
  explicitContext: string | null;
  /**
   * Typed retrieved chunks from the hybrid search pipeline.
   * Replaces the former flat `retrievedContext` string so downstream consumers
   * can access per-chunk metadata (path, score, index) for citation display.
   * Null when no index exists yet or retrieval failed.
   */
  retrievedChunks: RetrievedChunk[] | null;
  /**
   * @deprecated Use retrievedChunks. Kept for NullContextEngine compatibility
   * during the Epic 4.0 transition; will be removed in Epic 4.3.
   */
  retrievedContext: string | null;
  /**
   * Compressed summary of older conversation turns, fetched from the backend
   * on conversation load. Null until the first summarisation threshold is hit
   * (10 assistant turns). Prepended to the system message ahead of retrieved
   * context so the LLM can reference earlier conclusions.
   */
  conversationSummary: string | null;
}

/**
 * Gathers ambient workspace signals and packages them into a ContextSnapshot.
 *
 * The Context Engine is the single source of workspace awareness for the
 * Conversation Service. It observes signals (active project folder, recent
 * documents, explicit context) and exposes them through one method.
 *
 * The Conversation Service depends on this interface — never on a concrete
 * implementation. Signal collection is an internal detail of each implementation.
 */
export interface ContextEngine {
  /**
   * Returns the current workspace context snapshot.
   *
   * In Phase 00 this always resolves to an empty snapshot. Signal collection
   * begins in Phase 01.
   */
  getSnapshot(): Promise<ContextSnapshot>;
}
