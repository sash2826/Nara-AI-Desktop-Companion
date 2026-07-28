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
