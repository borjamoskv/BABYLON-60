use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use futures_util::{StreamExt, SinkExt};
use serde_json::Value;
use tokio::sync::mpsc::Sender;
use std::sync::{Arc, Mutex};
use crate::dashboard::Babylon60State;

const DISCORD_GATEWAY: &str = "wss://gateway.discord.gg/?v=10&encoding=json";

pub async fn run_discord_monitor(
    token: String,
    signal_tx: Sender<String>,
    state: Arc<Mutex<Babylon60State>>,
) -> Result<(), Box<dyn std::error::Error>> {

    let (ws_stream, _) = connect_async(DISCORD_GATEWAY).await?;
    let (mut write, mut read) = ws_stream.split();

    println!(">>> [DISCORD] Conectado al Gateway de Discord.");

    // Autenticación (Identify)
    let identify_payload = serde_json::json!({
        "op": 2,
        "d": {
            "token": token,
            "intents": 32768, // GUILD_MESSAGES
            "properties": {
                "os": "macos",
                "browser": "ouroboros",
                "device": "ouroboros"
            }
        }
    });

    write.send(Message::Text(identify_payload.to_string())).await?;

    while let Some(msg) = read.next().await {
        if let Ok(Message::Text(text)) = msg {
            let v: Value = serde_json::from_str(&text)?;

            // Evento MESSAGE_CREATE
            if v["t"] == "MESSAGE_CREATE" {
                let content = v["d"]["content"].as_str().unwrap_or_default();

                // Búsqueda de CA (0x...)
                if content.contains("0x") {
                    // Extraer CA (Heurística simple: buscar segmento de 42 chars)
                    if let Some(ca) = extract_ca_discord(content) {
                        {
                            let mut s = state.lock().unwrap();
                            s.signals_detected += 1;
                            s.log.push(format!("[DISCORD🎯] Señal detectada"));
                        }
                        println!(">>> [DISCORD] CA DETECTADO: {}", ca);
                        let _ = signal_tx.send(ca).await;
                    }
                }
            }

            // Manejo de Heartbeat (simplificado)
            if v["op"] == 10 {
                let interval = v["d"]["heartbeat_interval"].as_u64().unwrap();
                println!(">>> [DISCORD] Heartbeat interval: {}ms", interval);
                // En C5-REAL: lanzar un loop de heartbeat paralelo
            }
        }
    }

    Ok(())
}

fn extract_ca_discord(text: &str) -> Option<String> {
    // Reutilizar lógica de telegram_ingestor o implementar localmente
    let bytes = text.as_bytes();
    for i in 0..bytes.len().saturating_sub(41) {
        if bytes[i] == b'0' && bytes[i+1] == b'x' {
            let slice = &text[i..i+42];
            if slice.chars().skip(2).all(|c| c.is_ascii_hexdigit()) {
                return Some(slice.to_string());
            }
        }
    }
    None
}
