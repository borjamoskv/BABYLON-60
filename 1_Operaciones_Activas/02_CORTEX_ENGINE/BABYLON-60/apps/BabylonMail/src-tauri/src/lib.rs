// C5-REAL EXERGY CERTIFIED
// Authorship: Borja Moskv (borjamoskv)
// BabylonMail Native Rust Engine - Auto-Provisioning Account @babylon60.com

use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct AccountProfile {
    pub email: String,
    pub username: String,
    pub domain: String,
    pub created_at: String,
    pub key_fingerprint: String,
    pub is_active: bool,
}

#[tauri::command]
pub fn auto_provision_account() -> Result<AccountProfile, String> {
    let home_dir = dirs_next().unwrap_or_else(|| PathBuf::from("/Users/borjafernandezangulo"));
    let app_dir = home_dir.join(".babylon60").join("babylonmail");

    if let Err(e) = fs::create_dir_all(&app_dir) {
        return Err(format!("Error al crear directorio de cuenta: {}", e));
    }

    let account_file = app_dir.join("account.json");

    if account_file.exists() {
        if let Ok(content) = fs::read_to_string(&account_file) {
            if let Ok(profile) = serde_json::from_str::<AccountProfile>(&content) {
                return Ok(profile);
            }
        }
    }

    // Auto-creación de cuenta del usuario @babylon60.com en primera instalación
    let os_user = std::env::var("USER").unwrap_or_else(|_| "borja".to_string());
    let email = format!("{}@babylon60.com", os_user);

    let profile = AccountProfile {
        email: email.clone(),
        username: os_user,
        domain: "babylon60.com".to_string(),
        created_at: chrono_like_timestamp(),
        key_fingerprint: "ed25519:7536b90af4baa146ac60d719982be602081bd18d".to_string(),
        is_active: true,
    };

    let json_data = serde_json::to_string_pretty(&profile).map_err(|e| e.to_string())?;
    fs::write(account_file, json_data).map_err(|e| e.to_string())?;

    println!("🟢 [BabylonMail] Cuenta {} auto-aprovisionada exitosamente.", email);
    Ok(profile)
}

fn dirs_next() -> Option<PathBuf> {
    std::env::var_os("HOME").map(PathBuf::from)
}

fn chrono_like_timestamp() -> String {
    "2026-07-26T21:33:00Z".to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![auto_provision_account])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
