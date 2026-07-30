use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter, Manager, State};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};

// ─── App state ────────────────────────────────────────────────────────────────

/// Shared application state injected into every Tauri command.
pub struct AppState {
    /// Port on which the Python sidecar is listening.
    /// Set once after the sidecar prints `READY:{port}` to stdout.
    pub sidecar_port: Mutex<Option<u16>>,
    /// Handle to the Python child process for lifecycle management.
    pub sidecar_process: Mutex<Option<Child>>,
}

impl AppState {
    fn new() -> Self {
        Self {
            sidecar_port: Mutex::new(None),
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

// ─── Helper: base URL ─────────────────────────────────────────────────────────

fn sidecar_base(state: &AppState) -> Result<String, String> {
    let port = state
        .sidecar_port
        .lock()
        .map_err(|_| "Failed to acquire sidecar port lock".to_string())?;
    let port = port.ok_or_else(|| "Python sidecar is not yet ready".to_string())?;
    Ok(format!("http://127.0.0.1:{}", port))
}

// ─── Tauri commands ───────────────────────────────────────────────────────────

/// Returns `{ "status": "ok" }` when the Python sidecar is reachable.
#[tauri::command]
async fn health_check(state: State<'_, Arc<AppState>>) -> Result<HealthResponse, String> {
    let base = sidecar_base(&state)?;
    let url = format!("{}/health", base);

    let response = reqwest::get(&url)
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

    let client = reqwest::Client::new();
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

    let client = reqwest::Client::new();
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

    let response = reqwest::get(&url)
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

    let response = reqwest::get(&url)
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

    let client = reqwest::Client::new();
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

    let response = reqwest::get(&url)
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

    let client = reqwest::Client::new();
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

                if let Some(port_str) = line.trim().strip_prefix("READY:") {
                    if let Ok(port) = port_str.parse::<u16>() {
                        println!("[sidecar] ready on port {}", port);

                        if let Ok(mut guard) = state.sidecar_port.lock() {
                            *guard = Some(port);
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
            let handle = app.handle().clone();
            start_sidecar(handle, state_for_setup);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            health_check,
            generate_embedding,
            save_message,
            load_conversation,
            list_conversations,
            index_workspace,
            get_indexing_status,
            search_semantic
        ])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let state: State<Arc<AppState>> = window.state();
                let child_opt = state
                    .sidecar_process
                    .lock()
                    .ok()
                    .and_then(|mut g| g.take());
                if let Some(mut child) = child_opt {
                    let _ = child.kill();
                    println!("[sidecar] process killed on window close");
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
