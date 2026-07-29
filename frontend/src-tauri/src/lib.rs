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
pub struct IpcError {
    pub message: String,
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

// ─── Global shortcut ──────────────────────────────────────────────────────────

/// Registers Ctrl+K as a system-wide shortcut.
///
/// When the shortcut fires, a `toggle-glass-prompt` event is emitted to all
/// windows. The frontend listens for this event and toggles the Glass Prompt,
/// regardless of whether the Tauri window currently has focus.
fn register_global_shortcut(app: &tauri::App) {
    let shortcut = Shortcut::new(Some(Modifiers::CONTROL), Code::KeyK);
    let handle = app.handle().clone();

    app.global_shortcut()
        .on_shortcut(shortcut, move |_app, _shortcut, event| {
            if event.state == ShortcutState::Pressed {
                let _ = handle.emit("toggle-glass-prompt", ());
            }
        })
        .unwrap_or_else(|e| {
            eprintln!("[global-shortcut] failed to register Ctrl+K: {}", e);
        });
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
        .invoke_handler(tauri::generate_handler![health_check])
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
