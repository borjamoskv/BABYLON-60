use grammers_client::{Client, SenderPool};
use grammers_session::storages::SqliteSession;
use std::sync::Arc;
use tokio::sync::mpsc::Sender;
use aho_corasick::AhoCorasick;

const SESSION_FILE: &str = "ouroboros.session";
// Patrón regex-free O(1): Detecta cualquier CA Ethereum (0x + 40 hex chars)
// Pre-compilado al arrancar. No hay regex en el hot path.
const CA_PATTERNS: &[&str] = &["0x"];

/// Ingestión directa MTProto — Sin REST, sin polling, sin latencia.
/// Conexión persistente DC-Level a los servidores de Telegram.
pub async fn run_telegram_ingestor(
    api_id: i32,
    _api_hash: String,
    target_groups: Vec<String>,
    signal_tx: Sender<String>,
    state: std::sync::Arc<std::sync::Mutex<crate::dashboard::Babylon60State>>,
) -> Result<(), Box<dyn std::error::Error>> {

    println!(">>> [MTProto] Conectando al DC de Telegram...");

    // SOPORTE PARA MODO SIMULACIÓN (API_ID = 0)
    if api_id == 0 {
        println!(">>> [SIMULACIÓN] Iniciando Ingestor Mock — Generando señales de prueba.");
        loop {
            tokio::time::sleep(std::time::Duration::from_secs(10)).await;
            let mock_ca = format!("0x{:040x}", rand::random::<u128>());
            {
                let mut s = state.lock().unwrap();
                s.signals_detected += 1;
                s.log.push(format!("[MOCK🎯] Nueva señal simulada: {}", &mock_ca[..10]));
            }
            let _ = signal_tx.send(mock_ca).await;
        }
    }

    let session = Arc::new(SqliteSession::open(SESSION_FILE).await?);
    let pool = SenderPool::new(Arc::clone(&session), api_id);
    let client = Client::new(pool.handle);

    tokio::spawn(pool.runner.run());

    // Si no hay sesión activa, autenticar (solo primera vez).
    if !client.is_authorized().await? {
        println!(">>> [MTProto] Autenticación requerida. Introduce tu número de telefono:");
        panic!("SESSION_REQUIRED: Ejecutar flujo de autenticación inicial primero.");
    }

    println!(">>> [MTProto] Sesión activa. Escaneando {} grupos.", target_groups.len());

    // Pre-compilación del detector CA (O(1) sobre cualquier mensaje)
    let ac = AhoCorasick::builder()
        .ascii_case_insensitive(false)
        .build(CA_PATTERNS)
        .unwrap();

    // Stream de actualizaciones en tiempo real (WebSocket-level, MTProto)
    let mut update_stream = client.stream_updates(pool.updates, Default::default()).await.map_err(|e| e.to_string())?;

    while let Ok(update_res) = tokio::time::timeout(
        std::time::Duration::from_secs(60),
        update_stream.next()
    ).await {
        match update_res {
            Ok(update) => {
                use grammers_client::update::Update;
                if let Update::NewMessage(message) = update {
                    let text = message.text();

                    // Hot path — Búsqueda O(1) sin reserva de heap
                    if ac.is_match(text) {
                        if let Some(ca) = extract_ca(text) {
                            {
                                let mut s = state.lock().unwrap();
                                s.signals_detected += 1;
                                s.log.push(format!("[SIGNAL🎯] Detectada en canal"));
                            }
                            println!(">>> [MTProto] CA DETECTADO: {}", ca);
                            let _ = signal_tx.send(ca).await;
                        }
                    }
                }
            }
            _ => break,
        }
    }

    Ok(())
}

/// Extractor de CA: O(n) sobre texto largo, O(1) en mensajes estándar de 280 chars.
fn extract_ca(text: &str) -> Option<String> {
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
