/// Azure AD (Entra ID) configuration baked in at compile time from src-tauri/.env.
/// Copy src-tauri/.env.example → src-tauri/.env and fill in real values after the
/// App Registration is provisioned via the SNOW process.
pub const TENANT_ID: &str = env!("VITE_AZURE_TENANT_ID");
pub const CLIENT_ID: &str = env!("VITE_AZURE_CLIENT_ID");
/// Space-separated scope string, e.g. "api://<client-id>/.default openid profile".
pub const SCOPE: &str = env!("VITE_AZURE_SCOPE");

/// Returns true if this build has real Azure AD config (not the PLACEHOLDER sentinel).
pub fn is_configured() -> bool {
    TENANT_ID != "PLACEHOLDER" && CLIENT_ID != "PLACEHOLDER" && SCOPE != "PLACEHOLDER"
}
