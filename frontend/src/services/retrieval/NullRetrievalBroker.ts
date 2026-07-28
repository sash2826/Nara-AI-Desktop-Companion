import type { RetrievalBroker, RetrievalQuery, RetrievalResult } from "./RetrievalBroker";

/**
 * Phase 00 implementation of RetrievalBroker.
 *
 * Returns an empty result set for every query. Live connectors are
 * activated in Phase 01 when Qdrant and OneDrive integration are introduced.
 */
export class NullRetrievalBroker implements RetrievalBroker {
  async retrieve(_query: RetrievalQuery): Promise<RetrievalResult> {
    return { fragments: [] };
  }
}
