import type { ContextEngine, ContextSnapshot } from "./ContextEngine";

/**
 * Phase 00 implementation of ContextEngine.
 *
 * Returns an empty snapshot for every request. Each call returns a fresh
 * object so callers cannot accidentally share mutable state. Real signal
 * collection is introduced in Phase 01 when the Context Engine is connected
 * to live workspace signals.
 */
export class NullContextEngine implements ContextEngine {
  async getSnapshot(): Promise<ContextSnapshot> {
    return {
      activeProjectFolder: null,
      recentDocuments: [],
      explicitContext: null,
      retrievedContext: null,
    };
  }
}
