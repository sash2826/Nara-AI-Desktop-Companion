import type { RetrievalBroker, RetrievalQuery, RetrievalResult } from "../RetrievalBroker";

/**
 * Retrieves document fragments from the user's authenticated OneDrive via
 * the Microsoft Graph Search API.
 *
 * Phase 00 stub — returns empty results. Activated in Phase 01 when OAuth
 * token management and Graph API integration are implemented.
 */
export class OneDriveConnector implements RetrievalBroker {
  async retrieve(_query: RetrievalQuery): Promise<RetrievalResult> {
    return { fragments: [] };
  }
}
