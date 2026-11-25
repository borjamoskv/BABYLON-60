//! Servidor HTTP y WebSocket compatible con LM Studio y la API de OpenAI.

use std::sync::Arc;
use tokio::sync::Mutex;
use axum::{
    http::StatusCode,
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State,
    },
    response::{Html, IntoResponse, Json},
    routing::{get, post},
    Router,
};
use tokio::net::TcpListener;
use chrono::Utc;

use crate::types::*;
use crate::gate::BabylonCausalGate;
use crate::auth::DualPasskeyAuth;
use crate::hud::HUD_HTML;
use crate::ipc::{InferenceTelemetryBlock, TelemetrySnapshot};
use crate::uma::{UmaBufferPool, DARWIN_PAGE_SIZE};
use crate::gguf::GgufModel;

pub const CANDIDATE_PORTS: [u16; 5] = [41343, 52993, 16141, 39414, 22931];

pub struct AppState {
    pub gate: Mutex<BabylonCausalGate>,
    pub auth: DualPasskeyAuth,
    pub uma_pool: Mutex<UmaBufferPool>,
    pub telemetry: Arc<TelemetrySnapshot<InferenceTelemetryBlock>>,
    pub gguf_model: Option<GgufModel>,
}

impl AppState {
    pub fn new() -> Result<Self, String> {
        let gate = BabylonCausalGate::new();
        let uma_pool = UmaBufferPool::new(4, DARWIN_PAGE_SIZE)?;
        let telemetry = Arc::new(TelemetrySnapshot::new(InferenceTelemetryBlock::default()));
        let gguf_model = std::env::var("ERIDU_GGUF_PATH")
            .ok()
            .and_then(|p| GgufModel::load_mmap(p).ok());
        Ok(Self {
            gate: Mutex::new(gate),
            auth: DualPasskeyAuth::new(),
            uma_pool: Mutex::new(uma_pool),
            telemetry,
            gguf_model,
        })
    }
}

pub fn create_router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/", get(hud_handler))
        .route("/hud", get(hud_handler))
        .route("/lms-status", get(status_handler))
        .route("/v1/models", get(models_handler))
        .route("/v1/audit/receipts", get(receipts_handler))
        .route("/v1/chat/completions", post(chat_completions_handler))
        .route("/ws", get(ws_handler))
        .with_state(state)
}

/// Handler de la consola Web HUD de control en Anillo-0.
async fn hud_handler() -> impl IntoResponse {
    Html(HUD_HTML)
}

/// Handler de inspección del WORM Ledger (EU AI Act Arts. 12-14).
async fn receipts_handler(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let gate = state.gate.lock().await;
    Json(gate.get_recent_receipts())
}

/// Handler de sondeo de salud compatible 1:1 con `lms` CLI de LM Studio.
async fn status_handler() -> impl IntoResponse {
    Json(LmsStatusResponse {
        package: "eridu-infer".to_string(),
        version: "0.1.0-sovereign".to_string(),
    })
}

/// Listado de modelos disponibles (Tríada Jurídica en Silicio).
async fn models_handler() -> impl IntoResponse {
    let now = Utc::now().timestamp();
    let models = vec![
        ModelItem {
            id: "deepseek-r1-distill-qwen-32b".to_string(),
            object: "model".to_string(),
            created: now,
            owned_by: "babylon-60-sovereign".to_string(),
            description: "El Jurista Analítico · Razonamiento Lógico y Detección de Contradicciones".to_string(),
        },
        ModelItem {
            id: "llama-3.3-70b-instruct".to_string(),
            object: "model".to_string(),
            created: now,
            owned_by: "babylon-60-sovereign".to_string(),
            description: "El Redactor de Sala · Castellano Jurídico, Demandas y Recursos".to_string(),
        },
        ModelItem {
            id: "bge-m3-legal-embed".to_string(),
            object: "model".to_string(),
            created: now,
            owned_by: "babylon-60-sovereign".to_string(),
            description: "El Archivero Inmediato · Búsqueda Semántica en Expedientes y PDFs".to_string(),
        },
    ];

    Json(ModelListResponse {
        object: "list".to_string(),
        data: models,
    })
}

/// Handler compatible con OpenAI (`/v1/chat/completions`).
///
/// C0526: este crate no contiene motor de inferencia. Mientras no exista uno, el endpoint
/// responde 503 con un error explícito. No se sella recibo ni se cuentan tokens, porque no hay
/// inferencia que atestar, y nunca se devuelve texto prefabricado atribuido a un modelo.
async fn chat_completions_handler(
    State(_state): State<Arc<AppState>>,
    Json(req): Json<ChatCompletionRequest>,
) -> axum::response::Response {
    (
        StatusCode::SERVICE_UNAVAILABLE,
        Json(serde_json::json!({
            "error": {
                "type": "inference_unavailable",
                "message": "No hay motor de inferencia conectado; no se generó ninguna respuesta.",
                "model": req.model
            }
        })),
    )
        .into_response()
}

async fn ws_handler(
    ws: WebSocketUpgrade,
    State(_state): State<Arc<AppState>>,
) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
}

/// Respuesta a una llamada RPC del protocolo LM Studio (C0526). Este crate no tiene motor de
/// inferencia: ninguna llamada se ejecuta, así que se responde `rpcError` y nunca un éxito.
fn lms_rpc_reply(call_id: u32, endpoint: &str) -> serde_json::Value {
    serde_json::json!({
        "type": "rpcError",
        "callId": call_id,
        "error": {
            "cause": format!(
                "inference_unavailable: no hay motor de inferencia conectado; '{endpoint}' no se ejecutó"
            )
        }
    })
}

async fn handle_socket(mut socket: WebSocket) {
    while let Some(Ok(msg)) = socket.recv().await {
        if let Message::Text(text) = msg {
            // Manejador del protocolo lms_communication
            if let Ok(wire_msg) = serde_json::from_str::<LmsWireMessage>(&text) {
                match wire_msg {
                    LmsWireMessage::ChannelCreate { channel_id, endpoint, .. } => {
                        let ack = serde_json::json!({
                            "type": "channelAck",
                            "channelId": channel_id,
                            "endpoint": endpoint
                        });
                        let _ = socket.send(Message::Text(ack.to_string())).await;
                    }
                    LmsWireMessage::RpcCall { call_id, endpoint, .. } => {
                        let res = lms_rpc_reply(call_id, &endpoint);
                        let _ = socket.send(Message::Text(res.to_string())).await;
                    }
                    _ => {}
                }
            }
        }
    }
}

/// Enlaza el servidor a uno de los puertos candidatos de LM Studio o al puerto estándar 1234.
pub async fn bind_listener() -> (TcpListener, u16) {
    for &port in &CANDIDATE_PORTS {
        if let Ok(listener) = TcpListener::bind(format!("127.0.0.1:{}", port)).await {
            return (listener, port);
        }
    }
    let fallback = TcpListener::bind("127.0.0.1:1234")
        .await
        .expect("No se pudo enlazar ni a los puertos candidatos ni a 1234");
    (fallback, 1234)
}

#[cfg(test)]
mod c0526_tests {
    use super::*;
    use axum::http::StatusCode;

    #[tokio::test]
    async fn completion_without_inference_backend_is_unavailable_not_canned_text() {
        for model in ["deepseek-r1-distill-qwen-32b", "llama-3.3-70b-instruct", "otro-modelo"] {
            let state = Arc::new(AppState::new().unwrap());
            let req = ChatCompletionRequest {
                model: model.to_string(),
                messages: vec![ChatMessage {
                    role: "user".to_string(),
                    content: "¿Responde un modelo?".to_string(),
                    name: None,
                }],
                stream: false,
                temperature: None,
                max_tokens: None,
            };
            let response = chat_completions_handler(State(Arc::clone(&state)), Json(req))
                .await
                .into_response();
            assert_eq!(
                response.status(),
                StatusCode::SERVICE_UNAVAILABLE,
                "C0526: {model} devolvió una completion sin inferencia observada"
            );
            let body = axum::body::to_bytes(response.into_body(), 64 * 1024).await.unwrap();
            let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
            assert_eq!(json["error"]["type"], "inference_unavailable");
            assert!(json.get("choices").is_none(), "C0526: el error no debe incluir choices");
            assert!(state.gate.lock().await.get_recent_receipts().is_empty(), "C0526: se selló un recibo sin inferencia");
            assert_eq!(state.telemetry.read().tokens_generated, 0, "C0526: se contaron tokens sin inferencia");
        }
    }

    #[test]
    fn lms_rpc_call_reports_unavailable_instead_of_success() {
        // C0526: sin motor de inferencia, una llamada RPC no puede responder "ok".
        let reply = lms_rpc_reply(7, "llm.predict");
        assert_eq!(reply["type"], "rpcError", "C0526: RPC respondida como éxito: {reply}");
        assert_eq!(reply["callId"], 7);
        assert!(reply["error"]["cause"].as_str().unwrap_or("").contains("inference_unavailable"));
    }
}
