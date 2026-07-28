import type { RetrievalBroker, RetrievalQuery, RetrievalResult } from "../RetrievalBroker";

/**
 * Retrieves document fragments from the local vector index (Qdrant).
 *
 * Phase 00 stub — returns empty results. Activated in Phase 01 when the
 * local indexing pipeline and Qdrant integration are implemented.
 */
export class LocalFileConnector implements RetrievalBroker {
  async retrieve(_query: RetrievalQuery): Promise<RetrievalResult> {
    return { fragments: [] };
  }
}
