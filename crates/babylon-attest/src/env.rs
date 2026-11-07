use std::path::PathBuf;
use std::fs;

/// Resolves the canonical BABYLON root directory dynamically.
/// Order of precedence:
/// 1. $BABYLON_HOME environment variable
/// 2. $HOME/.babylon
/// 3. ./.babylon (fallback)
pub fn babylon_home() -> PathBuf {
    if let Ok(val) = std::env::var("BABYLON_HOME") {
        if !val.trim().is_empty() {
            return PathBuf::from(val.trim());
        }
    }
    if let Ok(home) = std::env::var("HOME") {
        if !home.trim().is_empty() {
            return PathBuf::from(home.trim()).join(".babylon");
        }
    }
    PathBuf::from("./.babylon")
}

pub fn keys_dir() -> PathBuf {
    babylon_home().join("keys")
}

pub fn ledger_dir() -> PathBuf {
    babylon_home().join("ledger")
}

pub fn ledger_file() -> PathBuf {
    ledger_dir().join("chain.jsonl")
}

pub fn license_file() -> PathBuf {
    babylon_home().join("license.key")
}

pub fn ensure_dirs() -> std::io::Result<()> {
    fs::create_dir_all(keys_dir())?;
    fs::create_dir_all(ledger_dir())?;
    Ok(())
}
