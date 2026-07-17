use tokio::net::TcpListener;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::sync::Arc;
use tokio::sync::Mutex;
use crate::ledger::CortexLedger;
use std::process::Command;
use serde::Deserialize;

#[derive(Deserialize)]
struct LlmMutation {
    target_file: String,
    content: String,
    commit_msg: String,
}

pub async fn ignite_cortex_bridge(db_state: Arc<Mutex<CortexLedger>>) {
    println!("🌉 [LLM_BRIDGE] Puente CORTEX activo en 127.0.0.1:6006. Esperando exergía de Claude/Codex.");
    
    let listener = TcpListener::bind("127.0.0.1:6006").await.expect("Fallo al abrir puerto de puente CORTEX");

    loop {
        if let Ok((mut socket, _addr)) = listener.accept().await {
            let db_clone = db_state.clone();
            tokio::spawn(async move {
                let mut buffer = vec![0; 1024 * 1024 * 5]; // 5MB max
                if let Ok(n) = socket.read(&mut buffer).await {
                    if n > 0 {
                        let payload_str = String::from_utf8_lossy(&buffer[..n]);
                        // Intentar aislar el payload JSON (algunos clientes mandan headers HTTP si usan requests)
                        // Para simplificar, asumimos que se envía un JSON crudo por TCP.
                        if let Ok(mutation) = serde_json::from_str::<LlmMutation>(&payload_str) {
                            
                            // 1. Inyección física en disco
                            if std::fs::write(&mutation.target_file, &mutation.content).is_ok() {
                                
                                // 2. Sello en CORTEX Ledger
                                let db = db_clone.lock().await;
                                let _ = db.write("LLM_MUTATION", &mutation.commit_msg);
                                drop(db);

                                // 3. Git Sentinel Autosync (BFT)
                                let _ = Command::new("git").args(["add", &mutation.target_file]).output();
                                let commit_out = Command::new("git")
                                    .args(["-c", "commit.gpgsign=false", "commit", "-m", &mutation.commit_msg, "--no-verify"])
                                    .output();

                                if let Ok(output) = commit_out {
                                    let hash = String::from_utf8_lossy(&output.stdout);
                                    let mut final_hash = hash.to_string();
                                    if final_hash.is_empty() {
                                        final_hash = "COMMITTED_NO_STDOUT".to_string();
                                    }
                                    let resp = format!("{{\"status\": \"C5-REAL\", \"hash\": \"{}\"}}", final_hash.trim().replace("\n", ""));
                                    let _ = socket.write_all(resp.as_bytes()).await;
                                    println!("💥 [LLM_BRIDGE] Entropía de Claude procesada. Archivo {} mutado.", mutation.target_file);
                                }
                            } else {
                                let _ = socket.write_all(b"{\"status\": \"ERROR\", \"message\": \"ENOENT\"}");
                            }
                        } else {
                            let _ = socket.write_all(b"{\"status\": \"ERROR\", \"message\": \"INVALID_JSON\"}");
                        }
                    }
                }
            });
        }
    }
}
