//! C5-REAL CodeActions and Biometric Causal Gate Execution Engine.

use crate::protocol::{CodeAction, Command};
use sha2::{Digest, Sha256};
use std::process::Stdio;
use tokio::process::Command as AsyncCommand;

pub struct ActionEngine;

impl ActionEngine {
    /// Generates context-aware CodeActions for the current document.
    pub fn get_code_actions(uri: &str) -> Vec<CodeAction> {
        vec![
            CodeAction {
                title: "🛡️ [C5-REAL] Sellar Transacción Causal con TouchID (EU AI Act)".to_string(),
                kind: Some("quickfix".to_string()),
                command: Some(Command {
                    title: "Firmar con TouchID".to_string(),
                    command: "c5.biometricSignOff".to_string(),
                    arguments: Some(vec![serde_json::json!({
                        "uri": uri,
                        "action": "MUTATION_COMMIT",
                        "description": "Atestación de firma biométrica para cambio de estado en Ring-0"
                    })]),
                }),
                is_preferred: Some(true),
            },
            CodeAction {
                title: "⚡ [C5-REAL] Auditar Integridad BFT Ledger (WAL Hash)".to_string(),
                kind: Some("source".to_string()),
                command: Some(Command {
                    title: "Auditar BFT".to_string(),
                    command: "c5.auditLedger".to_string(),
                    arguments: None,
                }),
                is_preferred: Some(false),
            },
        ]
    }

    /// Executes a C5-REAL command, triggering biometric gates when requested.
    pub async fn execute_command(command_name: &str, args: Option<Vec<serde_json::Value>>) -> Result<serde_json::Value, String> {
        match command_name {
            "c5.biometricSignOff" => {
                let action = args
                    .as_ref()
                    .and_then(|a| a.first())
                    .and_then(|v| v.get("action"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("GENERIC_MUTATION");

                let description = args
                    .as_ref()
                    .and_then(|a| a.first())
                    .and_then(|v| v.get("description"))
                    .and_then(|v| v.as_str())
                    .unwrap_or("Modificación de código soberano");

                // Generate SHA-256 causal hash
                let now = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_secs_f64();
                let pre_hash = format!("LSP_CAUSAL_GATE|{}|{:.6}", action, now);
                let mut hasher = Sha256::new();
                hasher.update(pre_hash.as_bytes());
                let causal_hash = hex::encode(hasher.finalize());

                // Locate the Swift biometric gate script
                let root_dir = std::env::current_dir().unwrap_or_default();
                let script_path = root_dir.join("01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift");

                if !script_path.exists() {
                    return Err(format!("Gate script no encontrado en: {}", script_path.display()));
                }

                // Invoke the Swift LocalAuthentication daemon
                let output = AsyncCommand::new("swift")
                    .arg(&script_path)
                    .arg("--message")
                    .arg(format!("{} - {}", action, description))
                    .arg("--causal-hash")
                    .arg(&causal_hash)
                    .stdout(Stdio::piped())
                    .stderr(Stdio::piped())
                    .output()
                    .await
                    .map_err(|e| format!("Fallo al invocar gate biométrico: {}", e))?;

                if output.status.success() {
                    let out_str = String::from_utf8_lossy(&output.stdout).trim().to_string();
                    Ok(serde_json::json!({
                        "status": "APPROVED",
                        "receipt": out_str,
                        "causal_hash": causal_hash,
                        "timestamp": now
                    }))
                } else {
                    let err_str = String::from_utf8_lossy(&output.stderr).trim().to_string();
                    Err(format!("Biometría denegada o cancelada por el humano: {}", err_str))
                }
            }
            "c5.auditLedger" => {
                // C0336: no se aprueba sin inspeccionar el ledger solicitado. Este crate no incluye
                // verificador de cadena, así que nunca devuelve HEALTHY: como mucho, NO_VERIFICADO.
                let ledger_path = args
                    .as_ref()
                    .and_then(|a| a.first())
                    .and_then(|v| v.get("ledger_path"))
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| "auditLedger: ledger_path requerido; sin ledger no hay inspección".to_string())?;
                if !std::path::Path::new(ledger_path).is_file() {
                    return Err(format!("auditLedger: ledger ausente: {}", ledger_path));
                }
                Ok(serde_json::json!({
                    "status": "NO_VERIFICADO",
                    "ledger_path": ledger_path,
                    "reason": "verificador de cadena no disponible en cortex-lsp"
                }))
            }
            _ => Err(format!("Comando desconocido: {}", command_name)),
        }
    }
}

#[cfg(test)]
mod c0336_tests {
    use super::*;

    #[tokio::test]
    async fn audit_ledger_never_reports_healthy_without_inspecting_a_ledger() {
        // C0336: sin ledger solicitado no hay inspección: no puede aprobarse.
        let no_args = ActionEngine::execute_command("c5.auditLedger", None).await;
        assert!(no_args.as_ref().map_or(true, |v| v["status"] != "HEALTHY"), "C0336: HEALTHY sin ledger: {:?}", no_args);

        let missing = ActionEngine::execute_command(
            "c5.auditLedger",
            Some(vec![serde_json::json!({"ledger_path": "/nonexistent/c0336.db"})]),
        )
        .await;
        assert!(missing.as_ref().map_or(true, |v| v["status"] != "HEALTHY"), "C0336: HEALTHY con ledger ausente: {:?}", missing);
    }
}
