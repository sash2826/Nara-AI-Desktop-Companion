use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter, Listener, Manager, State, WebviewUrl, WebviewWindowBuilder};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};

#[cfg(target_os = "windows")]
use winreg::{enums::HKEY_CURRENT_USER, RegKey};

// ─── App state ────────────────────────────────────────────────────────────────

/// Shared application state injected into every Tauri command.
pub struct AppState {
    /// Port on which the Python sidecar is listening.
    /// Set once after the sidecar prints `READY:{port}:{token}` to stdout.
    pub sidecar_port: Mutex<Option<u16>>,
    /// IPC shared secret transmitted in the `X-EAC-Token` header.
    /// Set once from the `READY:{port}:{token}` stdout line.
    pub ipc_token: Mutex<Option<String>>,
    /// Handle to the Python child process for lifecycle management.
    pub sidecar_process: Mutex<Option<Child>>,
}

impl AppState {
    fn new() -> Self {
        Self {
            sidecar_port: Mutex::new(None),
            ipc_token: Mutex::new(None),
            sidecar_process: Mutex::new(None),
        }
    }
}

// ─── IPC types ────────────────────────────────────────────────────────────────

#[derive(Serialize, Deserialize, Debug)]
pub struct HealthResponse {
    pub status: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct EmbedRequest {
    pub text: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct EmbedResponse {
    pub embedding: Vec<f64>,
    pub dim: u32,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SaveMessageRequest {
    pub message_id: String,
    pub conversation_id: String,
    pub role: String,
    pub content: String,
    pub status: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct MessageResponse {
    pub id: String,
    pub conversation_id: String,
    pub role: String,
    pub content: String,
    pub status: String,
    pub created_at: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ConversationResponse {
    pub id: String,
    pub messages: Vec<MessageResponse>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ConversationSummaryResponse {
    pub id: String,
    pub created_at: String,
    pub message_count: u32,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ConversationMemoryResponse {
    pub conversation_id: String,
    pub turn_count: u32,
    pub summary: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct IpcError {
    pub message: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct IndexWorkspaceRequest {
    pub workspace_path: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct IndexWorkspaceResponse {
    pub task_id: String,
    pub status: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct IndexingStatusResponse {
    pub task_id: String,
    pub status: String,
    pub files_found: u32,
    pub files_indexed: u32,
    pub files_skipped: u32,
    pub errors: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SemanticSearchRequest {
    pub query: String,
    pub top_k: u32,
    pub workspace_path: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SearchResultItem {
    pub chunk_id: String,
    pub document_id: String,
    pub document_path: String,
    pub chunk_index: u32,
    pub content: String,
    pub score: f64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SemanticSearchResponse {
    pub results: Vec<SearchResultItem>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct KeywordSearchRequest {
    pub query: String,
    pub top_k: u32,
    pub workspace_path: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct KeywordSearchResponse {
    pub results: Vec<SearchResultItem>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct HybridSearchRequest {
    pub query: String,
    pub top_k: u32,
    pub workspace_path: Option<String>,
    pub semantic_weight: f64,
    pub keyword_weight: f64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct HybridSearchResultItem {
    pub chunk_id: String,
    pub document_id: String,
    pub document_path: String,
    pub chunk_index: u32,
    pub content: String,
    pub rrf_score: f64,
    pub keyword_rank: Option<u32>,
    pub semantic_rank: Option<u32>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct HybridSearchResponse {
    pub results: Vec<HybridSearchResultItem>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct GraphEntityResponse {
    pub id: String,
    pub name: String,
    pub entity_type: String,
    pub source_document_id: String,
    pub properties: serde_json::Value,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct GraphRelationshipResponse {
    pub source_id: String,
    pub target_id: String,
    pub relationship_type: String,
    pub properties: serde_json::Value,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct GraphContextResponse {
    pub entity: GraphEntityResponse,
    pub related_entities: Vec<GraphEntityResponse>,
    pub relationships: Vec<GraphRelationshipResponse>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct GraphHealthResponse {
    pub connected: bool,
    pub provider: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CreateBackupRequest {
    pub notes: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct BackupResultResponse {
    pub backup_id: String,
    pub backup_path: String,
    pub created_at: String,
    pub sqlite_size_bytes: u64,
    pub qdrant_collections: Vec<String>,
    pub status: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct BackupSummaryResponse {
    pub backup_id: String,
    pub backup_path: String,
    pub created_at: String,
    pub status: String,
    pub sqlite_size_bytes: u64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct WatchedFolderResponse {
    pub id: String,
    pub path: String,
    pub auto_index: bool,
    pub added_at: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct WatcherStatusResponse {
    pub running: bool,
    pub watched_count: u32,
    pub folders: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct AddFolderRequest {
    pub path: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct IndexedDocumentResponse {
    pub id: String,
    pub workspace_path: String,
    pub file_path: String,
    pub char_count: u32,
    pub chunk_count: u32,
    pub indexed_at: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct IndexingErrorRecord {
    pub id: String,
    pub workspace_path: String,
    pub file_path: String,
    pub error_message: String,
    pub failed_at: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct RecentFileResponse {
    pub id: String,
    pub file_path: String,
    pub workspace_path: String,
    pub chunk_count: u32,
    pub char_count: u32,
    pub indexed_at: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct DashboardStatsResponse {
    pub document_count: u32,
    pub chunk_count: u32,
    pub total_chars: u64,
    pub conversation_count: u32,
    pub watched_folder_count: u32,
    pub indexing_error_count: u32,
    pub recent_files: Vec<RecentFileResponse>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SuggestionsRequest {
    pub recent_file_paths: Vec<String>,
    pub max_suggestions: u32,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SuggestionsResponse {
    pub suggestions: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct GraphVisNodeResponse {
    pub id: String,
    pub label: String,
    pub entity_type: String,
    pub confidence: f64,
    pub source_document_path: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct GraphVisEdgeResponse {
    pub source: String,
    pub source_name: String,
    pub target: String,
    pub target_name: String,
    pub relation_type: String,
    pub confidence: f64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct GraphVisualizationResponse {
    pub nodes: Vec<GraphVisNodeResponse>,
    pub edges: Vec<GraphVisEdgeResponse>,
}

// ─── Helper: base URL ─────────────────────────────────────────────────────────

fn sidecar_base(state: &AppState) -> Result<String, String> {
    let port = state
        .sidecar_port
        .lock()
        .map_err(|_| "Failed to acquire sidecar port lock".to_string())?;
    let port = port.ok_or_else(|| "Python sidecar is not yet ready".to_string())?;
    Ok(format!("http://127.0.0.1:{}", port))
}

fn ipc_token(state: &AppState) -> Option<String> {
    state.ipc_token.lock().ok()?.clone()
}

/// Build a reqwest Client pre-configured with the IPC shared secret header.
///
/// When no token is set (dev mode or legacy sidecar), the client still works
/// but unauthenticated — the middleware on the Python side only enforces the
/// token when `EAC_IPC_SECRET` is set.
fn ipc_client(state: &AppState) -> reqwest::Client {
    let mut builder = reqwest::Client::builder();
    if let Some(token) = ipc_token(state) {
        let mut headers = reqwest::header::HeaderMap::new();
        if let Ok(val) = reqwest::header::HeaderValue::from_str(&token) {
            headers.insert("X-EAC-Token", val);
        }
        builder = builder.default_headers(headers);
    }
    builder.build().unwrap_or_default()
}

// ─── Tauri commands ───────────────────────────────────────────────────────────

/// Returns `{ "status": "ok" }` when the Python sidecar is reachable.
#[tauri::command]
async fn health_check(state: State<'_, Arc<AppState>>) -> Result<HealthResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/health", base);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("Health check request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "Health check returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<HealthResponse>()
        .await
        .map_err(|e| format!("Failed to parse health response: {}", e))
}

/// Generates a BGE-M3 embedding vector for the given text.
///
/// Proxies to `POST /embeddings` on the Python sidecar. Returns a 1024-dimensional
/// float vector. Rejects with an error string if the sidecar is not yet ready.
#[tauri::command]
async fn generate_embedding(
    text: String,
    state: State<'_, Arc<AppState>>,
) -> Result<EmbedResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/embeddings", base);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&EmbedRequest { text })
        .send()
        .await
        .map_err(|e| format!("Embedding request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "Embedding endpoint returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<EmbedResponse>()
        .await
        .map_err(|e| format!("Failed to parse embedding response: {}", e))
}

/// Persists a message to SQLite via the Python sidecar.
///
/// Creates the parent conversation row automatically if it does not exist.
#[tauri::command]
async fn save_message(
    message_id: String,
    conversation_id: String,
    role: String,
    content: String,
    status: String,
    state: State<'_, Arc<AppState>>,
) -> Result<MessageResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/conversations/{}/messages", base, conversation_id);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&SaveMessageRequest {
            message_id,
            conversation_id,
            role,
            content,
            status,
        })
        .send()
        .await
        .map_err(|e| format!("save_message request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "save_message returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<MessageResponse>()
        .await
        .map_err(|e| format!("Failed to parse save_message response: {}", e))
}

/// Returns all conversations, most recent first, with their message counts.
#[tauri::command]
async fn list_conversations(
    state: State<'_, Arc<AppState>>,
) -> Result<Vec<ConversationSummaryResponse>, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/conversations", base);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("list_conversations request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "list_conversations returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<Vec<ConversationSummaryResponse>>()
        .await
        .map_err(|e| format!("Failed to parse list_conversations response: {}", e))
}

/// Loads all messages for a conversation from SQLite, oldest first.
#[tauri::command]
async fn load_conversation(
    conversation_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<ConversationResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/conversations/{}", base, conversation_id);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("load_conversation request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "load_conversation returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<ConversationResponse>()
        .await
        .map_err(|e| format!("Failed to parse load_conversation response: {}", e))
}

/// Starts indexing a workspace directory in the background.
///
/// Returns immediately with a task_id. Poll `get_indexing_status` for progress.
#[tauri::command]
async fn index_workspace(
    workspace_path: String,
    state: State<'_, Arc<AppState>>,
) -> Result<IndexWorkspaceResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/indexing/start", base);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&IndexWorkspaceRequest { workspace_path })
        .send()
        .await
        .map_err(|e| format!("index_workspace request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "index_workspace returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<IndexWorkspaceResponse>()
        .await
        .map_err(|e| format!("Failed to parse index_workspace response: {}", e))
}

/// Returns the current status of an indexing task.
#[tauri::command]
async fn get_indexing_status(
    task_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<IndexingStatusResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/indexing/status/{}", base, task_id);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("get_indexing_status request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "get_indexing_status returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<IndexingStatusResponse>()
        .await
        .map_err(|e| format!("Failed to parse indexing status response: {}", e))
}

/// Performs a semantic similarity search over indexed document chunks.
#[tauri::command]
async fn search_semantic(
    query: String,
    top_k: u32,
    workspace_path: Option<String>,
    state: State<'_, Arc<AppState>>,
) -> Result<SemanticSearchResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/search/semantic", base);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&SemanticSearchRequest {
            query,
            top_k,
            workspace_path,
        })
        .send()
        .await
        .map_err(|e| format!("search_semantic request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "search_semantic returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<SemanticSearchResponse>()
        .await
        .map_err(|e| format!("Failed to parse search_semantic response: {}", e))
}

/// Performs a full-text keyword search over indexed document chunks using FTS5.
#[tauri::command]
async fn search_keyword(
    query: String,
    top_k: u32,
    workspace_path: Option<String>,
    state: State<'_, Arc<AppState>>,
) -> Result<KeywordSearchResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/search/keyword", base);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&KeywordSearchRequest {
            query,
            top_k,
            workspace_path,
        })
        .send()
        .await
        .map_err(|e| format!("search_keyword request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "search_keyword returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<KeywordSearchResponse>()
        .await
        .map_err(|e| format!("Failed to parse search_keyword response: {}", e))
}

/// Retrieves a named entity and its neighbourhood from the knowledge graph.
#[tauri::command]
async fn get_graph_entity(
    entity_name: String,
    depth: u32,
    state: State<'_, Arc<AppState>>,
) -> Result<GraphContextResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!(
        "{}/graph/entity/{}?depth={}",
        base,
        urlencoding::encode(&entity_name),
        depth
    );

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("get_graph_entity request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "get_graph_entity returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<GraphContextResponse>()
        .await
        .map_err(|e| format!("Failed to parse graph entity response: {}", e))
}

/// Returns the health status of the graph provider.
#[tauri::command]
async fn graph_health(state: State<'_, Arc<AppState>>) -> Result<GraphHealthResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/graph/health", base);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("graph_health request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "graph_health returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<GraphHealthResponse>()
        .await
        .map_err(|e| format!("Failed to parse graph health response: {}", e))
}

/// Runs keyword + semantic search concurrently and merges results via RRF.
#[tauri::command]
async fn search_hybrid(
    query: String,
    top_k: u32,
    workspace_path: Option<String>,
    semantic_weight: f64,
    keyword_weight: f64,
    state: State<'_, Arc<AppState>>,
) -> Result<HybridSearchResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/search/hybrid", base);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&HybridSearchRequest {
            query,
            top_k,
            workspace_path,
            semantic_weight,
            keyword_weight,
        })
        .send()
        .await
        .map_err(|e| format!("search_hybrid request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "search_hybrid returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<HybridSearchResponse>()
        .await
        .map_err(|e| format!("Failed to parse search_hybrid response: {}", e))
}

/// Creates a timestamped backup of SQLite and Qdrant metadata.
#[tauri::command]
async fn create_backup(
    notes: String,
    state: State<'_, Arc<AppState>>,
) -> Result<BackupResultResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/backup/create", base);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&CreateBackupRequest { notes })
        .send()
        .await
        .map_err(|e| format!("create_backup request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "create_backup returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<BackupResultResponse>()
        .await
        .map_err(|e| format!("Failed to parse create_backup response: {}", e))
}

/// Returns all backups ordered most recent first.
#[tauri::command]
async fn list_backups(
    state: State<'_, Arc<AppState>>,
) -> Result<Vec<BackupSummaryResponse>, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/backup/list", base);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("list_backups request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "list_backups returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<Vec<BackupSummaryResponse>>()
        .await
        .map_err(|e| format!("Failed to parse list_backups response: {}", e))
}

/// Registers a folder for automatic background indexing.
#[tauri::command]
async fn add_watched_folder(
    path: String,
    state: State<'_, Arc<AppState>>,
) -> Result<WatchedFolderResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/watcher/folders", base);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&AddFolderRequest { path })
        .send()
        .await
        .map_err(|e| format!("add_watched_folder request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "add_watched_folder returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<WatchedFolderResponse>()
        .await
        .map_err(|e| format!("Failed to parse add_watched_folder response: {}", e))
}

/// Removes a watched folder by its ID.
#[tauri::command]
async fn remove_watched_folder(
    folder_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/watcher/folders/{}", base, folder_id);

    let client = ipc_client(&state);
    let response = client
        .delete(&url)
        .send()
        .await
        .map_err(|e| format!("remove_watched_folder request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "remove_watched_folder returned HTTP {}",
            response.status().as_u16()
        ));
    }

    Ok(())
}

/// Lists all registered watched folders.
#[tauri::command]
async fn list_watched_folders(
    state: State<'_, Arc<AppState>>,
) -> Result<Vec<WatchedFolderResponse>, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/watcher/folders", base);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("list_watched_folders request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "list_watched_folders returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<Vec<WatchedFolderResponse>>()
        .await
        .map_err(|e| format!("Failed to parse list_watched_folders response: {}", e))
}

/// Returns the current state of the file watcher service.
#[tauri::command]
async fn get_watcher_status(
    state: State<'_, Arc<AppState>>,
) -> Result<WatcherStatusResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/watcher/status", base);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("get_watcher_status request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "get_watcher_status returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<WatcherStatusResponse>()
        .await
        .map_err(|e| format!("Failed to parse get_watcher_status response: {}", e))
}

/// Lists all indexed documents, optionally filtered by workspace path.
#[tauri::command]
async fn list_documents(
    workspace_path: Option<String>,
    limit: Option<u32>,
    offset: Option<u32>,
    state: State<'_, Arc<AppState>>,
) -> Result<Vec<IndexedDocumentResponse>, String> {
    let base = sidecar_base(&state)?;
    let mut url = format!("{}/documents", base);

    let mut params: Vec<String> = Vec::new();
    if let Some(wp) = workspace_path {
        params.push(format!("workspace_path={}", urlencoding::encode(&wp)));
    }
    if let Some(l) = limit {
        params.push(format!("limit={}", l));
    }
    if let Some(o) = offset {
        params.push(format!("offset={}", o));
    }
    if !params.is_empty() {
        url = format!("{}?{}", url, params.join("&"));
    }

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("list_documents request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "list_documents returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<Vec<IndexedDocumentResponse>>()
        .await
        .map_err(|e| format!("Failed to parse list_documents response: {}", e))
}

/// Removes a document and all its chunks from SQLite, Qdrant, and the knowledge graph.
#[tauri::command]
async fn delete_document(
    document_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/documents/{}", base, document_id);

    let client = ipc_client(&state);
    let response = client
        .delete(&url)
        .send()
        .await
        .map_err(|e| format!("delete_document request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "delete_document returned HTTP {}",
            response.status().as_u16()
        ));
    }

    Ok(())
}

/// Removes multiple documents in a single backend call.
#[tauri::command]
async fn bulk_delete_documents(
    document_ids: Vec<String>,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/documents/bulk", base);

    let body = serde_json::json!({ "document_ids": document_ids });
    let client = ipc_client(&state);
    let response = client
        .delete(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("bulk_delete_documents request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "bulk_delete_documents returned HTTP {}",
            response.status().as_u16()
        ));
    }

    Ok(())
}

/// Cancels a running or queued indexing task.
#[tauri::command]
async fn cancel_indexing(
    task_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/indexing/cancel/{}", base, task_id);

    let client = ipc_client(&state);
    let response = client
        .delete(&url)
        .send()
        .await
        .map_err(|e| format!("cancel_indexing request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "cancel_indexing returned HTTP {}",
            response.status().as_u16()
        ));
    }

    Ok(())
}

/// Returns all persisted per-file indexing errors.
#[tauri::command]
async fn list_indexing_errors(
    state: State<'_, Arc<AppState>>,
) -> Result<Vec<IndexingErrorRecord>, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/indexing/errors", base);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("list_indexing_errors request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "list_indexing_errors returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<Vec<IndexingErrorRecord>>()
        .await
        .map_err(|e| format!("Failed to parse indexing errors response: {}", e))
}

/// Clears all persisted indexing errors.
#[tauri::command]
async fn clear_indexing_errors(
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/indexing/errors", base);

    let client = ipc_client(&state);
    let response = client
        .delete(&url)
        .send()
        .await
        .map_err(|e| format!("clear_indexing_errors request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "clear_indexing_errors returned HTTP {}",
            response.status().as_u16()
        ));
    }

    Ok(())
}

/// Returns the turn count and compressed conversation summary.
///
/// Called on conversation load so the frontend can inject stored memory
/// into the system message without re-reading the full message history.
#[tauri::command]
async fn get_conversation_memory(
    conversation_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<ConversationMemoryResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/conversations/{}/memory", base, conversation_id);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("get_conversation_memory request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "get_conversation_memory returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<ConversationMemoryResponse>()
        .await
        .map_err(|e| format!("Failed to parse conversation memory response: {}", e))
}

/// Opens a file or folder in the OS default application.
///
/// Uses the tauri-plugin-opener which is already registered in the app builder.
/// On Windows this is equivalent to ShellExecute with "open".
#[tauri::command]
async fn open_file(path: String) -> Result<(), String> {
    tauri_plugin_opener::open_path(path, None::<&str>)
        .map_err(|e| format!("Failed to open file: {}", e))
}

/// Returns aggregated workspace statistics for the home dashboard.
#[tauri::command]
async fn get_stats(state: State<'_, Arc<AppState>>) -> Result<DashboardStatsResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/stats", base);

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("get_stats request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "get_stats returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<DashboardStatsResponse>()
        .await
        .map_err(|e| format!("Failed to parse get_stats response: {}", e))
}

/// Returns AI-generated search query suggestions based on recent file names.
#[tauri::command]
async fn get_suggested_queries(
    recent_file_paths: Vec<String>,
    max_suggestions: u32,
    state: State<'_, Arc<AppState>>,
) -> Result<SuggestionsResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/stats/suggestions", base);

    let client = ipc_client(&state);
    let response = client
        .post(&url)
        .json(&SuggestionsRequest {
            recent_file_paths,
            max_suggestions,
        })
        .send()
        .await
        .map_err(|e| format!("get_suggested_queries request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "get_suggested_queries returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<SuggestionsResponse>()
        .await
        .map_err(|e| format!("Failed to parse get_suggested_queries response: {}", e))
}

/// Returns nodes and edges for the knowledge graph visualization page.
///
/// Proxies to `GET /graph/visualize` on the Python sidecar.
/// Returns empty nodes/edges arrays when Neo4j is offline or the graph is empty.
#[tauri::command]
async fn get_graph_visualization(
    entity: Option<String>,
    depth: Option<u32>,
    state: State<'_, Arc<AppState>>,
) -> Result<GraphVisualizationResponse, String> {
    let base = sidecar_base(&state)?;
    let mut url = format!("{}/graph/visualize", base);

    let mut params: Vec<String> = Vec::new();
    if let Some(e) = entity {
        params.push(format!("entity={}", urlencoding::encode(&e)));
    }
    if let Some(d) = depth {
        params.push(format!("depth={}", d));
    }
    if !params.is_empty() {
        url = format!("{}?{}", url, params.join("&"));
    }

    let response = ipc_client(&state).get(&url).send()
        .await
        .map_err(|e| format!("get_graph_visualization request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!(
            "get_graph_visualization returned HTTP {}",
            response.status().as_u16()
        ));
    }

    response
        .json::<GraphVisualizationResponse>()
        .await
        .map_err(|e| format!("Failed to parse graph visualization response: {}", e))
}

// ─── Orb window commands ──────────────────────────────────────────────────────

/// Returns the current screen-space position of the orb window.
/// Used by OrbShell to compute drag offsets correctly.
#[tauri::command]
async fn get_orb_position(app: AppHandle) -> Result<serde_json::Value, String> {
    let window = app
        .get_webview_window("orb")
        .ok_or_else(|| "Orb window not found".to_string())?;
    let pos = window
        .outer_position()
        .map_err(|e| format!("Failed to get orb position: {}", e))?;
    Ok(serde_json::json!({ "x": pos.x, "y": pos.y }))
}

/// Moves the orb window to the given screen-space coordinates.
#[tauri::command]
async fn set_orb_position(app: AppHandle, x: i32, y: i32) -> Result<(), String> {
    let window = app
        .get_webview_window("orb")
        .ok_or_else(|| "Orb window not found".to_string())?;
    window
        .set_position(tauri::PhysicalPosition::new(x, y))
        .map_err(|e| format!("Failed to set orb position: {}", e))
}

/// Shows the main EAC window and brings it to the foreground.
#[tauri::command]
async fn focus_main_window(app: AppHandle) -> Result<(), String> {
    let window = app
        .get_webview_window("main")
        .ok_or_else(|| "Main window not found".to_string())?;
    window.show().map_err(|e| format!("Failed to show main window: {}", e))?;
    window
        .set_focus()
        .map_err(|e| format!("Failed to focus main window: {}", e))
}

/// Returns the number of pending file placement recommendations.
/// Returns 0 when the sidecar is not yet ready.
#[tauri::command]
async fn get_pending_recommendation_count(
    state: State<'_, Arc<AppState>>,
) -> Result<u32, String> {
    let base = match sidecar_base(&state) {
        Ok(b) => b,
        Err(_) => return Ok(0),
    };
    let url = format!("{}/organisation/recommendations/pending/count", base);
    match ipc_client(&state).get(&url).send().await {
        Ok(resp) if resp.status().is_success() => {
            let body: serde_json::Value =
                resp.json().await.map_err(|e| e.to_string())?;
            Ok(body["count"].as_u64().unwrap_or(0) as u32)
        }
        _ => Ok(0),
    }
}

/// Accepts a file placement recommendation and triggers the physical move.
#[tauri::command]
async fn accept_recommendation(
    recommendation_id: String,
    folder: String,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/organisation/recommendations/{}/accept", base, recommendation_id);
    let body = serde_json::json!({ "folder": folder });
    let resp = ipc_client(&state)
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    if !resp.status().is_success() {
        return Err(format!("accept_recommendation returned HTTP {}", resp.status().as_u16()));
    }
    Ok(())
}

/// Dismisses a file placement recommendation without moving the file.
#[tauri::command]
async fn dismiss_recommendation(
    recommendation_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    let base = sidecar_base(&state)?;
    let url = format!(
        "{}/organisation/recommendations/{}/dismiss",
        base, recommendation_id
    );
    let resp = ipc_client(&state)
        .post(&url)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    if !resp.status().is_success() {
        return Err(format!(
            "dismiss_recommendation returned HTTP {}",
            resp.status().as_u16()
        ));
    }
    Ok(())
}

/// Returns all pending file placement recommendations.
#[tauri::command]
async fn list_pending_recommendations(
    state: State<'_, Arc<AppState>>,
) -> Result<serde_json::Value, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/organisation/recommendations/pending", base);
    let resp = ipc_client(&state)
        .get(&url)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    if !resp.status().is_success() {
        return Err(format!(
            "list_pending_recommendations returned HTTP {}",
            resp.status().as_u16()
        ));
    }
    resp.json::<serde_json::Value>()
        .await
        .map_err(|e| e.to_string())
}

/// Sends a single-turn query to the LLM through the backend and returns the
/// response text. Used by the orb inline query overlay.
#[tauri::command]
async fn orb_query(query: String, state: State<'_, Arc<AppState>>) -> Result<String, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/orb/query", base);
    let body = serde_json::json!({ "query": query });
    let resp = ipc_client(&state)
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    if !resp.status().is_success() {
        return Err(format!("orb_query returned HTTP {}", resp.status().as_u16()));
    }
    let parsed: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
    Ok(parsed["response"].as_str().unwrap_or("").to_string())
}

// ─── Plugin commands ──────────────────────────────────────────────────────────

#[derive(Serialize, Deserialize, Debug)]
pub struct PluginRecord {
    pub id: String,
    pub display_name: String,
    pub version: String,
    pub description: String,
    pub author: String,
    pub permissions: Vec<String>,
    pub enabled: bool,
    pub installed_at: String,
}

/// Returns all registered plugins with their current enabled state.
#[tauri::command]
async fn list_plugins(state: State<'_, Arc<AppState>>) -> Result<Vec<PluginRecord>, String> {
    let port = {
        let guard = state.sidecar_port.lock().map_err(|e| e.to_string())?;
        guard.ok_or_else(|| "Sidecar not ready".to_string())?
    };
    let url = format!("http://127.0.0.1:{}/plugins", port);
    ipc_client(&state)
        .get(&url)
        .send()
        .await
        .map_err(|e| e.to_string())?
        .json::<Vec<PluginRecord>>()
        .await
        .map_err(|e| e.to_string())
}

/// Enables a plugin by ID. Returns the updated plugin record.
#[tauri::command]
async fn enable_plugin(
    plugin_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<PluginRecord, String> {
    let port = {
        let guard = state.sidecar_port.lock().map_err(|e| e.to_string())?;
        guard.ok_or_else(|| "Sidecar not ready".to_string())?
    };
    let url = format!("http://127.0.0.1:{}/plugins/{}/enable", port, plugin_id);
    ipc_client(&state)
        .post(&url)
        .send()
        .await
        .map_err(|e| e.to_string())?
        .json::<PluginRecord>()
        .await
        .map_err(|e| e.to_string())
}

/// Disables a plugin by ID. Returns the updated plugin record.
#[tauri::command]
async fn disable_plugin(
    plugin_id: String,
    state: State<'_, Arc<AppState>>,
) -> Result<PluginRecord, String> {
    let port = {
        let guard = state.sidecar_port.lock().map_err(|e| e.to_string())?;
        guard.ok_or_else(|| "Sidecar not ready".to_string())?
    };
    let url = format!("http://127.0.0.1:{}/plugins/{}/disable", port, plugin_id);
    ipc_client(&state)
        .post(&url)
        .send()
        .await
        .map_err(|e| e.to_string())?
        .json::<PluginRecord>()
        .await
        .map_err(|e| e.to_string())
}

// ─── OS Keychain commands ─────────────────────────────────────────────────────

/// Stores a credential in the OS keychain (Windows Credential Manager on Windows).
///
/// `service` is the top-level name (e.g. "eac") and `key` is the credential name
/// within that service (e.g. "apim-key"). The value is the secret to store.
#[tauri::command]
async fn store_credential(service: String, key: String, value: String) -> Result<(), String> {
    keyring::Entry::new(&service, &key)
        .map_err(|e| e.to_string())?
        .set_password(&value)
        .map_err(|e| e.to_string())
}

/// Loads a credential from the OS keychain. Returns `None` when the entry does not exist.
#[tauri::command]
async fn load_credential(service: String, key: String) -> Result<Option<String>, String> {
    match keyring::Entry::new(&service, &key)
        .map_err(|e| e.to_string())?
        .get_password()
    {
        Ok(val) => Ok(Some(val)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(e) => Err(e.to_string()),
    }
}

/// Deletes a credential from the OS keychain. Silently succeeds if the entry does not exist.
#[tauri::command]
async fn delete_credential(service: String, key: String) -> Result<(), String> {
    match keyring::Entry::new(&service, &key)
        .map_err(|e| e.to_string())?
        .delete_credential()
    {
        Ok(()) => Ok(()),
        Err(keyring::Error::NoEntry) => Ok(()),
        Err(e) => Err(e.to_string()),
    }
}

// ─── Windows startup registration ────────────────────────────────────────────

/// Registers the EAC orb in the Windows startup registry so it launches on login.
/// Safe to call on every start — the key is always overwritten with the current exe path.
/// No-op on non-Windows platforms.
#[cfg(target_os = "windows")]
fn register_windows_startup() {
    let exe = match std::env::current_exe() {
        Ok(p) => p,
        Err(e) => {
            eprintln!("[startup] could not determine exe path: {}", e);
            return;
        }
    };
    let exe_str = match exe.to_str() {
        Some(s) => s.to_string(),
        None => {
            eprintln!("[startup] exe path is not valid UTF-8");
            return;
        }
    };

    match RegKey::predef(HKEY_CURRENT_USER)
        .open_subkey_with_flags(
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            winreg::enums::KEY_WRITE,
        ) {
        Ok(key) => {
            match key.set_value("EnterpriseAICompanion", &exe_str) {
                Ok(()) => println!("[startup] registered in HKCU\\...\\Run"),
                Err(e) => eprintln!("[startup] failed to set registry value: {}", e),
            }
        }
        Err(e) => eprintln!("[startup] failed to open registry key: {}", e),
    }
}

#[cfg(not(target_os = "windows"))]
fn register_windows_startup() {
    // No-op on macOS/Linux — startup handled via platform-specific mechanisms
}

// ─── Orb window creation ──────────────────────────────────────────────────────

/// Creates the standalone always-on-top orb WebviewWindow.
///
/// Window properties:
///   - label: "orb"
///   - always_on_top, decorations: false, transparent, skip_taskbar
///   - 80 wide × 340 tall (orb 56px + overlay expansion headroom 284px)
///   - Positioned bottom-right of the primary monitor, scale-factor corrected
fn create_orb_window(app: &tauri::App) {
    let primary_monitor = app
        .primary_monitor()
        .ok()
        .flatten();

    // `monitor.size()` is in physical pixels; `monitor.position()` is in physical pixels.
    // `WebviewWindowBuilder::position()` takes logical pixels (physical / scale_factor).
    // Without this correction the orb ends up off-screen on HiDPI displays.
    let (start_x, start_y) = if let Some(monitor) = primary_monitor {
        let size = monitor.size();
        let pos = monitor.position();
        let scale = monitor.scale_factor();
        // Orb window is 80×340 logical pixels; inset 24px from right, 56px from bottom.
        let logical_w = (size.width as f64 / scale) as i32;
        let logical_h = (size.height as f64 / scale) as i32;
        let logical_x = (pos.x as f64 / scale) as i32;
        let logical_y = (pos.y as f64 / scale) as i32;
        // Window is 400 wide × 380 tall. Right edge flush with screen right (24px inset).
        // Orb sphere sits in the bottom-right corner; overlay expands leftward inside the window.
        (
            logical_x + logical_w - 400 - 24,
            logical_y + logical_h - 380 - 48,
        )
    } else {
        (840, 620)
    };

    match WebviewWindowBuilder::new(app, "orb", WebviewUrl::App("index.html".into()))
        .title("EAC Orb")
        .inner_size(400.0, 380.0)
        .resizable(false)
        .always_on_top(true)
        .decorations(false)
        .transparent(true)
        .shadow(false)
        .skip_taskbar(true)
        .position(start_x as f64, start_y as f64)
        .build()
    {
        Ok(_) => println!("[orb] window created at ({}, {})", start_x, start_y),
        Err(e) => eprintln!("[orb] failed to create window: {}", e),
    }
}

// ─── Global shortcut ──────────────────────────────────────────────────────────

/// Registers Ctrl+K as a system-wide shortcut.
///
/// When the shortcut fires, a `toggle-glass-prompt` event is emitted to all
/// windows. The frontend listens for this event and toggles the Glass Prompt,
/// regardless of whether the Tauri window currently has focus.
/// Registers the global toggle shortcut (Ctrl+Shift+Space).
///
/// Ctrl+K is owned exclusively by enterprise apps (Teams, Slack) via Win32
/// RegisterHotKey, which is process-exclusive. Ctrl+Shift+Space has no known
/// conflicts with standard enterprise tooling.
fn register_global_shortcut(app: &tauri::App) {
    let shortcut = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::Space);
    let handle = app.handle().clone();

    match app.global_shortcut().on_shortcut(shortcut, move |_app, _shortcut, event| {
        if event.state == ShortcutState::Pressed {
            let _ = handle.emit("toggle-glass-prompt", ());
        }
    }) {
        Ok(()) => println!("[global-shortcut] registered Ctrl+Shift+Space"),
        Err(e) => eprintln!("[global-shortcut] registration failed: {}", e),
    }
}

// ─── Sidecar lifecycle ────────────────────────────────────────────────────────

/// Spawns `python -m enterprise_ai_companion`, waits for `READY:{port}`,
/// stores the port in AppState, and emits `sidecar-ready` to the frontend.
fn start_sidecar(app_handle: AppHandle, state: Arc<AppState>) {
    std::thread::spawn(move || {
        // Locate the backend directory relative to the workspace root.
        // In dev the working directory is the Tauri source; in production the
        // backend is expected to be a bundled sidecar binary (future phase).
        let backend_dir = {
            let exe = std::env::current_exe().unwrap_or_default();
            // Walk up from <repo>/frontend/src-tauri/target/... to <repo>/backend
            let mut candidate = exe.clone();
            let mut found = None;
            for _ in 0..10 {
                candidate = match candidate.parent() {
                    Some(p) => p.to_path_buf(),
                    None => break,
                };
                let backend = candidate.join("backend");
                if backend.exists() {
                    found = Some(backend);
                    break;
                }
            }
            found.unwrap_or_else(|| std::path::PathBuf::from("../../backend"))
        };

        let venv_python = backend_dir.join(".venv/Scripts/python.exe");
        let python_cmd = if venv_python.exists() {
            venv_python.to_str().unwrap_or("python").to_string()
        } else {
            "python".to_string()
        };

        println!("[sidecar] starting: {} -m enterprise_ai_companion", python_cmd);

        let mut child = match Command::new(&python_cmd)
            .args(["-m", "enterprise_ai_companion"])
            .current_dir(&backend_dir)
            .env("HF_HUB_DISABLE_XET", "1")
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
        {
            Ok(c) => c,
            Err(e) => {
                eprintln!("[sidecar] failed to spawn Python process: {}", e);
                return;
            }
        };

        // Read stdout line-by-line looking for `READY:{port}`.
        if let Some(stdout) = child.stdout.take() {
            let reader = BufReader::new(stdout);
            for line in reader.lines() {
                let line = match line {
                    Ok(l) => l,
                    Err(_) => break,
                };

                if let Some(rest) = line.trim().strip_prefix("READY:") {
                    // Protocol: READY:{port} (legacy) or READY:{port}:{token}
                    let mut parts = rest.splitn(2, ':');
                    let port_str = parts.next().unwrap_or("");
                    let token_str = parts.next();

                    if let Ok(port) = port_str.parse::<u16>() {
                        println!("[sidecar] ready on port {}", port);

                        if let Ok(mut guard) = state.sidecar_port.lock() {
                            *guard = Some(port);
                        }
                        if let Some(token) = token_str {
                            let token = token.trim().to_string();
                            if !token.is_empty() {
                                if let Ok(mut guard) = state.ipc_token.lock() {
                                    *guard = Some(token);
                                }
                            }
                        }

                        // Notify the frontend that the sidecar is ready.
                        let _ = app_handle.emit("sidecar-ready", port);
                        break;
                    }
                }
            }
        }

        // Store the child handle for clean shutdown.
        if let Ok(mut guard) = state.sidecar_process.lock() {
            *guard = Some(child);
        }
    });
}

// ─── App entry point ──────────────────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = Arc::new(AppState::new());
    let state_for_setup = Arc::clone(&app_state);

    tauri::Builder::default()
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_opener::init())
        .manage(app_state)
        .setup(move |app| {
            register_global_shortcut(app);
            register_windows_startup();
            create_orb_window(app);

            let handle = app.handle().clone();
            start_sidecar(handle.clone(), state_for_setup);

            // When the sidecar becomes ready, emit initial pending count to the orb window.
            let handle_for_ready = handle.clone();
            handle.listen("sidecar-ready", move |_event| {
                let h = handle_for_ready.clone();
                tauri::async_runtime::spawn(async move {
                    // Brief delay to let the sidecar finish startup
                    tokio::time::sleep(std::time::Duration::from_secs(2)).await;
                    if let Some(orb) = h.get_webview_window("orb") {
                        let _ = orb.emit("orb-pending-count", 0u32);
                    }
                });
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            health_check,
            generate_embedding,
            save_message,
            load_conversation,
            list_conversations,
            get_conversation_memory,
            index_workspace,
            get_indexing_status,
            search_semantic,
            search_keyword,
            search_hybrid,
            get_graph_entity,
            graph_health,
            create_backup,
            list_backups,
            add_watched_folder,
            remove_watched_folder,
            list_watched_folders,
            get_watcher_status,
            list_documents,
            delete_document,
            bulk_delete_documents,
            cancel_indexing,
            list_indexing_errors,
            clear_indexing_errors,
            open_file,
            get_stats,
            get_suggested_queries,
            get_graph_visualization,
            list_plugins,
            enable_plugin,
            disable_plugin,
            store_credential,
            load_credential,
            delete_credential,
            get_orb_position,
            set_orb_position,
            focus_main_window,
            get_pending_recommendation_count,
            accept_recommendation,
            dismiss_recommendation,
            list_pending_recommendations,
            orb_query
        ])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                match window.label() {
                    "main" => {
                        // Closing the main window hides it — the orb stays alive
                        // and the sidecar keeps running. The user can re-open the
                        // main window by double-clicking the orb.
                        api.prevent_close();
                        let _ = window.hide();
                    }
                    "orb" => {
                        // Closing the orb is a full application quit.
                        // Kill the sidecar then exit.
                        let state: State<Arc<AppState>> = window.state();
                        let child_opt = state
                            .sidecar_process
                            .lock()
                            .ok()
                            .and_then(|mut g| g.take());
                        if let Some(mut child) = child_opt {
                            let _ = child.kill();
                            println!("[sidecar] process killed on orb close (full quit)");
                        }
                        window.app_handle().exit(0);
                    }
                    _ => {}
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
