use std::fs;
use std::path::Path;

fn main() {
    // Load Azure AD config from .env so auth_config.rs can use env!() at compile time.
    // The .env file is gitignored — copy .env.example and fill in real values after
    // the App Registration is created in Azure.
    let env_path = Path::new(env!("CARGO_MANIFEST_DIR")).join(".env");
    if env_path.exists() {
        let content = fs::read_to_string(&env_path).expect("Failed to read .env");
        for line in content.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            if let Some((key, val)) = line.split_once('=') {
                let key = key.trim();
                let val = val.trim();
                // Only set vars that auth_config.rs depends on.
                if matches!(key, "VITE_AZURE_TENANT_ID" | "VITE_AZURE_CLIENT_ID" | "VITE_AZURE_SCOPE") {
                    println!("cargo:rustc-env={key}={val}");
                }
            }
        }
    } else {
        // No .env — set placeholder values so the build succeeds.
        // The login button will show a configuration error at runtime.
        println!("cargo:rustc-env=VITE_AZURE_TENANT_ID=PLACEHOLDER");
        println!("cargo:rustc-env=VITE_AZURE_CLIENT_ID=PLACEHOLDER");
        println!("cargo:rustc-env=VITE_AZURE_SCOPE=PLACEHOLDER");
    }

    // Re-run if .env changes.
    println!("cargo:rerun-if-changed=.env");

    tauri_build::build()
}
