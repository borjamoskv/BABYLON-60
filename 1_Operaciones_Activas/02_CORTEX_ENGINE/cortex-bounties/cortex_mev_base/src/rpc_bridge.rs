use tokio::net::UnixListener;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tracing::{info, error};
use std::fs;
use crate::striker_4337::SovereignStriker;
use std::sync::Arc;

const SOCKET_PATH: &str = "/tmp/cortex_omega.sock";

pub async fn start_rpc_server(striker: Arc<SovereignStriker>) -> Result<(), Box<dyn std::error::Error>> {
    // Purge old socket file if it exists to prevent 'Address already in use' errors.
    let _ = fs::remove_file(SOCKET_PATH);
    
    let listener = UnixListener::bind(SOCKET_PATH)?;
    info!("🔗 OMEGA RPC Bridge Inicializado. Escuchando Sockets en: {}", SOCKET_PATH);

    loop {
        match listener.accept().await {
            Ok((mut socket, _addr)) => {
                let striker_clone = Arc::clone(&striker);
                tokio::spawn(async move {
                    let mut buf = vec![0; 4096];
                    match socket.read(&mut buf).await {
                        Ok(0) => return,
                        Ok(n) => {
                            let command_str = String::from_utf8_lossy(&buf[..n]);
                            info!("📥 [CORTEX-PYTHON] Comando recibido: {}", command_str);
                            
                            // Parsea el payload del bounty (Simulado)
                            // En C5-REAL, esto vendría estructurado como JSON.
                            let parts: Vec<&str> = command_str.trim().split('|').collect();
                            if parts.len() == 2 {
                                let target = parts[0];
                                let payload = parts[1];
                                
                                match striker_clone.execute_strike(target, payload).await {
                                    Ok(tx_hash) => {
                                        let response = format!("STRIKE_SUCCESS|{}", tx_hash);
                                        let _ = socket.write_all(response.as_bytes()).await;
                                    },
                                    Err(e) => {
                                        error!("Error ejecutando Strike: {:?}", e);
                                        let _ = socket.write_all(b"STRIKE_FAILED").await;
                                    }
                                }
                            } else {
                                let _ = socket.write_all(b"INVALID_PAYLOAD").await;
                            }
                        }
                        Err(e) => {
                            error!("Error leyendo del socket: {:?}", e);
                        }
                    }
                });
            }
            Err(e) => error!("Error aceptando conexión Unix Socket: {:?}", e),
        }
    }
}
