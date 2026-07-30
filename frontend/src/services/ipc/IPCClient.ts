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

export const IPCClient = {
  healthCheck,
  generateEmbedding,
  saveMessage,
  loadConversation,
  listConversations,
  indexWorkspace,
  getIndexingStatus,
  searchSemantic,
} as const;
