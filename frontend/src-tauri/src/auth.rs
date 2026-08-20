use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine as _};
use chrono::{DateTime, Duration, Utc};
use keyring::Entry;
use rand::RngCore;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::io::{BufRead, BufReader, BufWriter, Write};
use std::net::TcpListener;
use std::sync::Arc;
use tauri::{AppHandle, Emitter, Manager, State};

use crate::auth_config;
use crate::AppState;

// ─── Types ────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AzureTokenData {
    pub access_token: String,
    pub refresh_token: Option<String>,
    pub expires_at: DateTime<Utc>,
}

impl AzureTokenData {
    pub fn is_expired(&self) -> bool {
        Utc::now() >= self.expires_at
    }

    pub fn expires_within_secs(&self, secs: i64) -> bool {
        Utc::now() + Duration::seconds(secs) >= self.expires_at
    }
}

#[derive(Deserialize)]
struct TokenResponse {
    access_token: String,
    refresh_token: Option<String>,
    expires_in: Option<u64>,
    error: Option<String>,
    error_description: Option<String>,
}

#[derive(Serialize, Clone)]
pub struct AuthStateEvent {
    pub is_authenticated: bool,
    pub user_display_name: Option<String>,
}

// ─── Keychain helpers ──────────────────────────────────────────────────────────

const KEYCHAIN_SERVICE: &str = "eac-auth";

fn kc_store(key: &str, value: &str) -> Result<(), String> {
    Entry::new(KEYCHAIN_SERVICE, key)
        .and_then(|e| e.set_password(value))
        .map_err(|e| e.to_string())
}

fn kc_load(key: &str) -> Option<String> {
    match Entry::new(KEYCHAIN_SERVICE, key).and_then(|e| e.get_password()) {
        Ok(v) => Some(v),
        _ => None,
    }
}

fn kc_delete(key: &str) {
    if let Ok(entry) = Entry::new(KEYCHAIN_SERVICE, key) {
        let _ = entry.delete_credential();
    }
}

// ─── Save / load token ────────────────────────────────────────────────────────

pub fn save_token(token: &AzureTokenData) -> Result<(), String> {
    kc_store("access-token", &token.access_token)?;
    if let Some(rt) = &token.refresh_token {
        kc_store("refresh-token", rt)?;
    }
    kc_store("expires-at", &token.expires_at.to_rfc3339())?;
    Ok(())
}

pub fn load_token_from_keychain() -> Option<AzureTokenData> {
    let access_token = kc_load("access-token")?;
    let expires_at_str = kc_load("expires-at")?;
    let expires_at = DateTime::parse_from_rfc3339(&expires_at_str)
        .ok()?
        .with_timezone(&Utc);
    let refresh_token = kc_load("refresh-token");
    Some(AzureTokenData { access_token, refresh_token, expires_at })
}

pub fn clear_keychain() {
    kc_delete("access-token");
    kc_delete("refresh-token");
    kc_delete("expires-at");
}

// ─── Token exchange ───────────────────────────────────────────────────────────

async fn exchange_code(
    code: &str,
    redirect_uri: &str,
    code_verifier: &str,
) -> Result<AzureTokenData, String> {
    post_token(&[
        ("grant_type", "authorization_code"),
        ("client_id", auth_config::CLIENT_ID),
        ("scope", auth_config::SCOPE),
        ("code", code),
        ("redirect_uri", redirect_uri),
        ("code_verifier", code_verifier),
    ])
    .await
}

pub async fn do_refresh(refresh_token: &str) -> Result<AzureTokenData, String> {
    post_token(&[
        ("grant_type", "refresh_token"),
        ("client_id", auth_config::CLIENT_ID),
        ("scope", auth_config::SCOPE),
        ("refresh_token", refresh_token),
    ])
    .await
    .map(|mut t| {
        if t.refresh_token.is_none() {
            t.refresh_token = Some(refresh_token.to_string());
        }
        t
    })
}

async fn post_token(params: &[(&str, &str)]) -> Result<AzureTokenData, String> {
    let token_url = format!(
        "https://login.microsoftonline.com/{}/oauth2/v2.0/token",
        auth_config::TENANT_ID
    );
    let client = reqwest::Client::new();
    let resp = client
        .post(&token_url)
        .form(params)
        .send()
        .await
        .map_err(|e| format!("Token request failed: {e}"))?;

    let body: TokenResponse = resp
        .json()
        .await
        .map_err(|e| format!("Token response parse failed: {e}"))?;

    if let Some(err) = body.error {
        return Err(format!("{err}: {}", body.error_description.unwrap_or_default()));
    }

    let expires_in = body.expires_in.unwrap_or(3600);
    let expires_at = Utc::now() + Duration::seconds(expires_in as i64);
    Ok(AzureTokenData {
        access_token: body.access_token,
        refresh_token: body.refresh_token,
        expires_at,
    })
}

// ─── Background refresh task ───────────────────────────────────────────────────

/// Spawn a background task that silently refreshes the access token before expiry.
pub fn spawn_refresh_task(app: AppHandle) {
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(300)).await;

            let state = app.state::<Arc<AppState>>();
            let (needs_refresh, refresh_token) = {
                let guard = state.azure_token.lock().unwrap();
                match guard.as_ref() {
                    Some(t) if t.expires_within_secs(600) => (true, t.refresh_token.clone()),
                    _ => (false, None),
                }
            };

            if !needs_refresh {
                continue;
            }

            let Some(rt) = refresh_token else {
                eprintln!("[auth] No refresh token — user must re-login");
                *state.azure_token.lock().unwrap() = None;
                clear_keychain();
                let _ = app.emit(
                    "auth-state-changed",
                    AuthStateEvent { is_authenticated: false, user_display_name: None },
                );
                break;
            };

            match do_refresh(&rt).await {
                Ok(new_token) => {
                    if let Err(e) = save_token(&new_token) {
                        eprintln!("[auth] Keychain save failed after refresh: {e}");
                    }
                    *state.azure_token.lock().unwrap() = Some(new_token);
                    let _ = app.emit(
                        "auth-state-changed",
                        AuthStateEvent { is_authenticated: true, user_display_name: None },
                    );
                }
                Err(e) => {
                    eprintln!("[auth] Token refresh failed: {e}");
                }
            }
        }
    });
}

// ─── Tauri commands ────────────────────────────────────────────────────────────

/// Check whether a valid session exists in the keychain.
/// Restores the token into AppState (so the app reopens without a login prompt).
/// Returns true unconditionally when Azure AD is not yet configured (PLACEHOLDER values)
/// so the app remains usable during development before the App Registration is provisioned.
#[tauri::command]
pub async fn auth_check(
    app: AppHandle,
    state: State<'_, Arc<AppState>>,
) -> Result<bool, String> {
    if !auth_config::is_configured() {
        return Ok(true);
    }

    let Some(token) = load_token_from_keychain() else {
        return Ok(false);
    };

    if !token.is_expired() {
        *state.azure_token.lock().unwrap() = Some(token);
        spawn_refresh_task(app);
        return Ok(true);
    }

    // Expired — attempt silent refresh if we have a refresh token.
    if let Some(rt) = token.refresh_token {
        match do_refresh(&rt).await {
            Ok(new_token) => {
                save_token(&new_token)?;
                *state.azure_token.lock().unwrap() = Some(new_token);
                spawn_refresh_task(app);
                return Ok(true);
            }
            Err(e) => {
                eprintln!("[auth] Silent refresh failed: {e}");
            }
        }
    }

    clear_keychain();
    *state.azure_token.lock().unwrap() = None;
    Ok(false)
}

/// Authorization Code + PKCE login flow.
#[tauri::command]
pub async fn auth_login(
    app: AppHandle,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    if !auth_config::is_configured() {
        return Err(
            "Azure AD is not configured yet. Copy src-tauri/.env.example → src-tauri/.env \
             and fill in VITE_AZURE_TENANT_ID, VITE_AZURE_CLIENT_ID, VITE_AZURE_SCOPE, \
             then rebuild."
                .to_string(),
        );
    }

    // PKCE: code_verifier = 32 random bytes → lowercase hex.
    let mut verifier_bytes = [0u8; 32];
    rand::thread_rng().fill_bytes(&mut verifier_bytes);
    let code_verifier: String = verifier_bytes.iter().map(|b| format!("{b:02x}")).collect();

    // code_challenge = BASE64URL(SHA256(code_verifier)), no padding.
    let hash = Sha256::digest(code_verifier.as_bytes());
    let code_challenge = URL_SAFE_NO_PAD.encode(hash);

    // Random state parameter (CSRF guard).
    let mut state_bytes = [0u8; 16];
    rand::thread_rng().fill_bytes(&mut state_bytes);
    let oauth_state = URL_SAFE_NO_PAD.encode(state_bytes);

    // Bind a random free port.
    let listener = TcpListener::bind("127.0.0.1:0")
        .map_err(|e| format!("Failed to bind callback listener: {e}"))?;
    let port = listener.local_addr().map_err(|e| e.to_string())?.port();
    let redirect_uri = format!("http://localhost:{port}");

    // Build the authorization URL.
    let auth_url = format!(
        "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize\
         ?client_id={client_id}\
         &response_type=code\
         &redirect_uri={redirect}\
         &scope={scope}\
         &code_challenge={challenge}\
         &code_challenge_method=S256\
         &response_mode=query\
         &state={state}",
        tenant = auth_config::TENANT_ID,
        client_id = auth_config::CLIENT_ID,
        redirect = urlencoding::encode(&redirect_uri),
        scope = urlencoding::encode(auth_config::SCOPE),
        challenge = code_challenge,
        state = oauth_state,
    );

    tauri_plugin_opener::open_url(&auth_url, None::<&str>)
        .map_err(|e| format!("Failed to open browser: {e}"))?;

    // Accept the OAuth callback (blocking I/O — offloaded to a thread).
    let (code, returned_state) = tokio::task::spawn_blocking(move || {
        let (mut stream, _) = listener
            .accept()
            .map_err(|e| format!("Callback accept failed: {e}"))?;

        let mut reader = BufReader::new(&stream);
        let mut request_line = String::new();
        reader
            .read_line(&mut request_line)
            .map_err(|e| format!("Read failed: {e}"))?;

        let path = request_line
            .split_whitespace()
            .nth(1)
            .unwrap_or("")
            .to_string();

        // Respond to the browser.
        let body = b"<html><body><h2>Login successful</h2>\
                     <p>You can close this tab and return to Nara.</p></body></html>";
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\
             Content-Length: {}\r\nConnection: close\r\n\r\n",
            body.len()
        );
        {
            let mut writer = BufWriter::new(&mut stream);
            let _ = writer.write_all(response.as_bytes());
            let _ = writer.write_all(body);
        }

        // Parse query string.
        let query = path.split('?').nth(1).unwrap_or("");
        let mut code = None;
        let mut returned_state = None;
        for param in query.split('&') {
            if let Some(v) = param.strip_prefix("code=") {
                code = Some(urlencoding::decode(v).unwrap_or_default().into_owned());
            } else if let Some(v) = param.strip_prefix("state=") {
                returned_state =
                    Some(urlencoding::decode(v).unwrap_or_default().into_owned());
            }
        }

        let code = code.ok_or_else(|| "No authorization code in callback".to_string())?;
        Ok::<(String, Option<String>), String>((code, returned_state))
    })
    .await
    .map_err(|e| format!("Callback task panicked: {e}"))??;

    // Verify CSRF state.
    if returned_state.as_deref() != Some(oauth_state.as_str()) {
        return Err("OAuth state mismatch — possible CSRF".to_string());
    }

    // Exchange the code for tokens.
    let token = exchange_code(&code, &redirect_uri, &code_verifier).await?;
    save_token(&token)?;
    *state.azure_token.lock().unwrap() = Some(token);

    spawn_refresh_task(app.clone());

    app.emit(
        "auth-state-changed",
        AuthStateEvent { is_authenticated: true, user_display_name: None },
    )
    .map_err(|e| e.to_string())?;

    Ok(())
}

/// Sign out: clear keychain and reset auth state.
#[tauri::command]
pub async fn auth_logout(
    app: AppHandle,
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    clear_keychain();
    *state.azure_token.lock().unwrap() = None;

    app.emit(
        "auth-state-changed",
        AuthStateEvent { is_authenticated: false, user_display_name: None },
    )
    .map_err(|e| e.to_string())?;

    Ok(())
}

/// Return the current access token string (if valid), or None.
#[tauri::command]
pub async fn auth_get_token(
    state: State<'_, Arc<AppState>>,
) -> Result<Option<String>, String> {
    let guard = state.azure_token.lock().unwrap();
    Ok(match guard.as_ref() {
        Some(t) if !t.is_expired() => Some(t.access_token.clone()),
        _ => None,
    })
}
