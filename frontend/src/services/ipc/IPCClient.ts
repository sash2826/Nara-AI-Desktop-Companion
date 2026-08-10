/**
 * IPCClient — typed wrapper around the Tauri invoke API.
 *
 * All communication between the React frontend and the Rust/Python backend
 * flows through this client. No component or service should call `invoke`
 * directly — this is the single authoritative IPC boundary.
 *
 * Architecture:
 *   React component / hook
 *       │
 *   IPCClient.someCommand()        ← this file
 *       │
 *   invoke("some_command", payload) ← Tauri IPC
 *       │
 *   Tauri Rust command handler
 *       │
 *   HTTP POST to Python sidecar
 *       │
 *   FastAPI handler
 */

import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

// ─── Shared types ─────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: "ok";
}

export interface EmbedResponse {
  embedding: number[];
  dim: number;
}

export interface SaveMessagePayload {
  messageId: string;
  conversationId: string;
  role: "user" | "assistant";
  content: string;
  status: "complete" | "streaming" | "error";
}

export interface PersistedMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  status: "complete" | "streaming" | "error";
  created_at: string;
}

export interface PersistedConversation {
  id: string;
  messages: PersistedMessage[];
}

export interface ConversationSummary {
  id: string;
  created_at: string;
  message_count: number;
}

export interface ConversationMemory {
  conversation_id: string;
  turn_count: number;
  summary: string | null;
}

export interface IndexWorkspaceResponse {
  task_id: string;
  status: string;
}

export interface IndexingStatus {
  task_id: string;
  status: string;
  files_found: number;
  files_indexed: number;
  files_skipped: number;
  errors: string[];
}

export interface SearchResultItem {
  chunk_id: string;
  document_id: string;
  document_path: string;
  chunk_index: number;
  content: string;
  score: number;
}

export interface SemanticSearchResponse {
  results: SearchResultItem[];
}

export interface KeywordSearchResponse {
  results: SearchResultItem[];
}

export interface HybridSearchResultItem {
  chunk_id: string;
  document_id: string;
  document_path: string;
  chunk_index: number;
  content: string;
  rrf_score: number;
  keyword_rank: number | null;
  semantic_rank: number | null;
}

export interface HybridSearchResponse {
  results: HybridSearchResultItem[];
}

export interface GraphEntityItem {
  id: string;
  name: string;
  entity_type: string;
  source_document_id: string;
  properties: Record<string, unknown>;
}

export interface GraphRelationshipItem {
  source_id: string;
  target_id: string;
  relationship_type: string;
  properties: Record<string, unknown>;
}

export interface GraphContextResponse {
  entity: GraphEntityItem;
  related_entities: GraphEntityItem[];
  relationships: GraphRelationshipItem[];
}

export interface GraphHealthResponse {
  connected: boolean;
  provider: string;
}

export interface BackupResult {
  backup_id: string;
  backup_path: string;
  created_at: string;
  sqlite_size_bytes: number;
  qdrant_collections: string[];
  status: string;
}

export interface BackupSummary {
  backup_id: string;
  backup_path: string;
  created_at: string;
  status: string;
  sqlite_size_bytes: number;
}

export interface IndexedDocument {
  id: string;
  workspace_path: string;
  file_path: string;
  char_count: number;
  chunk_count: number;
  indexed_at: string;
}

export interface WatchedFolder {
  id: string;
  path: string;
  auto_index: boolean;
  added_at: string;
}

export interface WatcherStatus {
  running: boolean;
  watched_count: number;
  folders: string[];
}

export interface IndexingError {
  id: string;
  workspace_path: string;
  file_path: string;
  error_message: string;
  failed_at: string;
}

export interface RecentFile {
  id: string;
  file_path: string;
  workspace_path: string;
  chunk_count: number;
  char_count: number;
  indexed_at: string;
}

export interface DashboardStats {
  document_count: number;
  chunk_count: number;
  total_chars: number;
  conversation_count: number;
  watched_folder_count: number;
  indexing_error_count: number;
  recent_files: RecentFile[];
}

export interface SuggestionsResponse {
  suggestions: string[];
}

export interface GraphVisNode {
  id: string;
  label: string;
  entity_type: string;
  confidence: number;
  source_document_path: string | null;
}

export interface GraphVisEdge {
  source: string; // entity UUID — used for layout
  source_name: string; // human-readable label
  target: string; // entity UUID
  target_name: string; // human-readable label
  relation_type: string;
  confidence: number;
}

export interface GraphVisualization {
  nodes: GraphVisNode[];
  edges: GraphVisEdge[];
}

// ─── Sidecar readiness ────────────────────────────────────────────────────────

/**
 * Returns a promise that resolves with the sidecar port once the backend emits
 * the `sidecar-ready` event. Rejects after `timeoutMs` if the event never fires.
 *
 * Use this in application startup to gate any IPC calls on sidecar readiness.
 */
export function waitForSidecar(timeoutMs = 30_000): Promise<number> {
  return new Promise<number>((resolve, reject) => {
    // Capture the listen promise so we can call unlisten regardless of whether
    // the cleanup runs before or after the listen() promise resolves.
    const listenPromise = listen<number>("sidecar-ready", (event) => {
      clearTimeout(timer);
      listenPromise.then((fn) => fn()).catch(() => {});
      resolve(event.payload);
    });

    const timer = setTimeout(() => {
      listenPromise.then((fn) => fn()).catch(() => {});
      reject(new Error("Sidecar did not become ready within the timeout period."));
    }, timeoutMs);

    listenPromise.catch((err: unknown) => {
      clearTimeout(timer);
      reject(err);
    });
  });
}

// ─── IPCClient ────────────────────────────────────────────────────────────────

/**
 * Calls the `health_check` Tauri command.
 *
 * Returns `{ status: "ok" }` when the Python sidecar is reachable.
 * Throws a string error message if the sidecar is not ready or unreachable.
 */
async function healthCheck(): Promise<HealthResponse> {
  return invoke<HealthResponse>("health_check");
}

/**
 * Calls the `generate_embedding` Tauri command.
 *
 * Returns a 1024-dimensional BGE-M3 embedding vector for the given text.
 * Throws a string error message if the sidecar is not ready or the text is empty.
 */
async function generateEmbedding(text: string): Promise<number[]> {
  const response = await invoke<EmbedResponse>("generate_embedding", { text });
  return response.embedding;
}

/**
 * Calls the `save_message` Tauri command.
 *
 * Persists a message to SQLite via the Python sidecar, creating the parent
 * conversation row automatically if it does not exist.
 */
async function saveMessage(payload: SaveMessagePayload): Promise<PersistedMessage> {
  return invoke<PersistedMessage>("save_message", {
    messageId: payload.messageId,
    conversationId: payload.conversationId,
    role: payload.role,
    content: payload.content,
    status: payload.status,
  });
}

/**
 * Calls the `load_conversation` Tauri command.
 *
 * Returns all messages for the conversation, oldest first.
 * Returns an empty messages array when the conversation does not yet exist.
 */
async function loadConversation(conversationId: string): Promise<PersistedConversation> {
  return invoke<PersistedConversation>("load_conversation", { conversationId });
}

/**
 * Returns the turn count and compressed summary for a conversation.
 *
 * Used on conversation load to inject prior-session memory into the system
 * message without re-reading the full message history.
 */
async function getConversationMemory(conversationId: string): Promise<ConversationMemory> {
  return invoke<ConversationMemory>("get_conversation_memory", { conversationId });
}

/**
 * Calls the `list_conversations` Tauri command.
 *
 * Returns all conversations ordered by most recent first.
 * Used on startup to resume the last active conversation.
 */
async function listConversations(): Promise<ConversationSummary[]> {
  return invoke<ConversationSummary[]>("list_conversations");
}

/**
 * Starts indexing a workspace directory in the background.
 * Returns a task_id to poll with `getIndexingStatus`.
 */
async function indexWorkspace(workspacePath: string): Promise<IndexWorkspaceResponse> {
  return invoke<IndexWorkspaceResponse>("index_workspace", { workspacePath });
}

/**
 * Returns the current status of an indexing task.
 */
async function getIndexingStatus(taskId: string): Promise<IndexingStatus> {
  return invoke<IndexingStatus>("get_indexing_status", { taskId });
}

/**
 * Performs a semantic search over indexed document chunks.
 * Returns scored fragments ordered by similarity.
 */
async function searchSemantic(
  query: string,
  topK: number = 5,
  workspacePath?: string
): Promise<SemanticSearchResponse> {
  return invoke<SemanticSearchResponse>("search_semantic", {
    query,
    topK,
    workspacePath: workspacePath ?? null,
  });
}

/**
 * Performs a full-text keyword search over indexed document chunks.
 * Returns scored fragments ordered by BM25 relevance.
 */
async function searchKeyword(
  query: string,
  topK: number = 10,
  workspacePath?: string
): Promise<KeywordSearchResponse> {
  return invoke<KeywordSearchResponse>("search_keyword", {
    query,
    topK,
    workspacePath: workspacePath ?? null,
  });
}

/**
 * Runs keyword + semantic search concurrently and merges results via RRF.
 *
 * @param semanticWeight Multiplier for the semantic provider's RRF contribution (default 1.0).
 * @param keywordWeight  Multiplier for the keyword provider's RRF contribution (default 1.0).
 */
async function searchHybrid(
  query: string,
  topK: number = 10,
  workspacePath?: string,
  semanticWeight: number = 1.0,
  keywordWeight: number = 1.0
): Promise<HybridSearchResponse> {
  return invoke<HybridSearchResponse>("search_hybrid", {
    query,
    topK,
    workspacePath: workspacePath ?? null,
    semanticWeight,
    keywordWeight,
  });
}

/**
 * Retrieves a named entity and its neighbourhood from the knowledge graph.
 *
 * @param entityName Exact entity name to look up.
 * @param depth Neighbourhood traversal depth (1–3, default 1).
 */
async function getGraphEntity(
  entityName: string,
  depth: number = 1
): Promise<GraphContextResponse> {
  return invoke<GraphContextResponse>("get_graph_entity", { entityName, depth });
}

/**
 * Returns the health status of the graph provider backend.
 */
async function graphHealth(): Promise<GraphHealthResponse> {
  return invoke<GraphHealthResponse>("graph_health");
}

/**
 * Creates a timestamped backup of SQLite and Qdrant collection metadata.
 */
async function createBackup(notes: string = ""): Promise<BackupResult> {
  return invoke<BackupResult>("create_backup", { notes });
}

/**
 * Returns all backups ordered most recent first.
 */
async function listBackups(): Promise<BackupSummary[]> {
  return invoke<BackupSummary[]>("list_backups");
}

/**
 * Returns all indexed documents, ordered most recently indexed first.
 * Optionally filtered by workspace path.
 */
async function listDocuments(
  workspacePath?: string,
  limit: number = 500,
  offset: number = 0
): Promise<IndexedDocument[]> {
  return invoke<IndexedDocument[]>("list_documents", {
    workspacePath: workspacePath ?? null,
    limit,
    offset,
  });
}

/**
 * Registers a folder for automatic background indexing.
 */
async function addWatchedFolder(path: string): Promise<WatchedFolder> {
  return invoke<WatchedFolder>("add_watched_folder", { path });
}

/**
 * Unregisters a watched folder by its ID.
 */
async function removeWatchedFolder(folderId: string): Promise<void> {
  return invoke<void>("remove_watched_folder", { folderId });
}

/**
 * Returns all registered watched folders.
 */
async function listWatchedFolders(): Promise<WatchedFolder[]> {
  return invoke<WatchedFolder[]>("list_watched_folders");
}

/**
 * Returns the current state of the file watcher service.
 */
async function getWatcherStatus(): Promise<WatcherStatus> {
  return invoke<WatcherStatus>("get_watcher_status");
}

/**
 * Removes a document and all its chunks from SQLite, Qdrant, and the knowledge graph.
 */
async function deleteDocument(documentId: string): Promise<void> {
  return invoke<void>("delete_document", { documentId });
}

/**
 * Removes multiple documents and all their chunks in a single backend call.
 */
async function bulkDeleteDocuments(documentIds: string[]): Promise<void> {
  return invoke<void>("bulk_delete_documents", { documentIds });
}

/**
 * Cancels a running or queued indexing task.
 */
async function cancelIndexing(taskId: string): Promise<void> {
  return invoke<void>("cancel_indexing", { taskId });
}

/**
 * Returns all persisted per-file indexing errors, most recent first.
 */
async function listIndexingErrors(): Promise<IndexingError[]> {
  return invoke<IndexingError[]>("list_indexing_errors");
}

/**
 * Deletes all persisted indexing errors.
 */
async function clearIndexingErrors(): Promise<void> {
  return invoke<void>("clear_indexing_errors");
}

/**
 * Opens a file or folder in the OS default application.
 * On Windows this is equivalent to double-clicking the file in Explorer.
 */
async function openFile(path: string): Promise<void> {
  return invoke<void>("open_file", { path });
}

/**
 * Returns aggregated workspace statistics for the home dashboard.
 */
async function getStats(): Promise<DashboardStats> {
  return invoke<DashboardStats>("get_stats");
}

/**
 * Returns nodes and edges for the knowledge graph visualization.
 *
 * When `entityName` is provided the subgraph is centred on that entity.
 * When omitted the provider returns an overview of the most-connected nodes.
 * Always returns `{ nodes: [], edges: [] }` when Neo4j is offline.
 */
async function getGraphVisualization(
  entityName?: string,
  depth: number = 2
): Promise<GraphVisualization> {
  return invoke<GraphVisualization>("get_graph_visualization", {
    entity: entityName ?? null,
    depth,
  });
}

/**
 * Returns AI-generated search query suggestions based on recently indexed file paths.
 * The client is responsible for caching the result (1-hour TTL recommended).
 */
async function getSuggestedQueries(
  recentFilePaths: string[],
  maxSuggestions: number = 5
): Promise<string[]> {
  const response = await invoke<SuggestionsResponse>("get_suggested_queries", {
    recentFilePaths,
    maxSuggestions,
  });
  return response.suggestions;
}

export const IPCClient = {
  healthCheck,
  generateEmbedding,
  saveMessage,
  loadConversation,
  listConversations,
  getConversationMemory,
  indexWorkspace,
  getIndexingStatus,
  listDocuments,
  searchSemantic,
  searchKeyword,
  searchHybrid,
  getGraphEntity,
  graphHealth,
  createBackup,
  listBackups,
  addWatchedFolder,
  removeWatchedFolder,
  listWatchedFolders,
  getWatcherStatus,
  deleteDocument,
  bulkDeleteDocuments,
  cancelIndexing,
  listIndexingErrors,
  clearIndexingErrors,
  openFile,
  getStats,
  getSuggestedQueries,
  getGraphVisualization,
} as const;
