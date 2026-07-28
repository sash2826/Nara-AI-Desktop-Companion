/**
 * A single chunk of content retrieved from an indexed source.
 *
 * `score` is normalized to [0, 1] by each connector before the broker
 * merges results. This ensures cross-connector ranking is consistent
 * regardless of the underlying relevance model.
 */
export interface DocumentFragment {
  /** The retrieved text content. */
  content: string;
  /** Absolute path or URL identifying the source document. */
  sourcePath: string;
  /** Which connector produced this fragment. */
  sourceType: "local" | "onedrive";
  /** Relevance score normalized to [0, 1]. Higher is more relevant. */
  score: number;
}

/**
 * Structured query sent from the Conversation Service to the Retrieval Broker.
 *
 * This is the primary contract between the two services. All connectors
 * receive the same query type — new query capabilities are added here,
 * not in individual connectors.
 */
export interface RetrievalQuery {
  /** Natural language search text or embedding-ready string. */
  text: string;
  /** Restrict retrieval to documents under this folder path. Null means no restriction. */
  projectFolder: string | null;
  /** Maximum number of fragments to return across all connectors. */
  maxResults: number;
}

/**
 * The ranked result set returned by the Retrieval Broker.
 */
export interface RetrievalResult {
  /** Fragments sorted by descending score. May be empty. */
  fragments: DocumentFragment[];
}

/**
 * Single interface through which the Conversation Service retrieves knowledge.
 *
 * The broker fans a RetrievalQuery across all active connectors, normalizes
 * scores, merges results, and returns a single ranked RetrievalResult.
 *
 * The Conversation Service depends on this interface — never on individual
 * connectors. Adding a new connector requires no changes to the Conversation
 * Service.
 */
export interface RetrievalBroker {
  /**
   * Execute a retrieval query across all active connectors.
   *
   * In Phase 00 this always resolves to an empty result set. Connectors
   * are activated in Phase 01.
   */
  retrieve(query: RetrievalQuery): Promise<RetrievalResult>;
}
