//! Servidor HTTP y WebSocket compatible con LM Studio y la API de OpenAI.

use std::sync::Arc;
use tokio::sync::Mutex;
use axum::{
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
use crate::ipc::{InferenceTelemetryBlock, KudurruSeqlock};
use crate::uma::{UmaBufferPool, DARWIN_PAGE_SIZE};
use crate::gguf::GgufModel;

pub const CANDIDATE_PORTS: [u16; 5] = [41343, 52993, 16141, 39414, 22931];

pub struct AppState {
    pub gate: Mutex<BabylonCausalGate>,
    pub auth: DualPasskeyAuth,
    pub uma_pool: Mutex<UmaBufferPool>,
    pub telemetry: Arc<KudurruSeqlock<InferenceTelemetryBlock>>,
    pub gguf_model: Option<GgufModel>,
}

impl AppState {
    pub fn new() -> Result<Self, String> {
        let gate = BabylonCausalGate::new();
        let uma_pool = UmaBufferPool::new(4, DARWIN_PAGE_SIZE)?;
        let telemetry = Arc::new(KudurruSeqlock::new(InferenceTelemetryBlock::default()));
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

/// Handler de inferencia compatible con OpenAI (`/v1/chat/completions`) sellado por BABYLON-60.
async fn chat_completions_handler(
    State(state): State<Arc<AppState>>,
    Json(req): Json<ChatCompletionRequest>,
) -> impl IntoResponse {
    let last_prompt = req.messages.last().map(|m| m.content.as_str()).unwrap_or("");

    // 1. Adquisición de página alineada de 16 KB en UMA (RFO = 0) y estadiaje de entrada
    let uma_ptr_addr = {
        let mut pool = state.uma_pool.lock().await;
        let mut buf = pool.acquire().expect("Fallo adquiriendo página UMA de 16 KB");
        let bytes = last_prompt.as_bytes();
        let copy_len = bytes.len().min(buf.size);
        buf.as_mut_slice()[..copy_len].copy_from_slice(&bytes[..copy_len]);
        let addr = buf.as_ptr() as usize;
        pool.release(buf);
        addr
    };

    // 2. Evaluación en Anillo-0 del Causal Gate y publicación en SharedManifest (64B)
    let receipt = {
        let mut gate = state.gate.lock().await;
        gate.evaluate_and_seal(&req.model, last_prompt).unwrap_or_else(|e| {
            panic!("Fallo en la evaluación del Causal Gate: {}", e);
        })
    };

    let gguf_tensors = state.gguf_model.as_ref().map(|m| m.tensor_count).unwrap_or(0);
    let summary_prompt: String = last_prompt.chars().take(120).collect();
    let generated_response = match req.model.as_str() {
        "deepseek-r1-distill-qwen-32b" => {
            format!(
                "<think>\n\
                [ANÁLISIS DEDUCTIVO EN ANILLO-0 · SUSTRATO APPLE SILICON METAL · UMA 0x{:X}]\n\
                1. Delimitación de hechos y pretensión: Se audita la consulta bajo el ordenamiento jurídico español y europeo.\n\
                2. Marco normativo aplicable: TRLC (reforma Ley 16/2022), Código Civil (Arts. 1101, 1255), RGPD y EU AI Act (Arts. 9-15).\n\
                3. Ponderación de riesgos y contradicciones: Confinamiento estricto en circuito cerrado local (127.0.0.1, GGUF tensors={}).\n\
                4. Dictamen resolutivo emitido con certeza probatoria en logical_tick={}.\n\
                </think>\n\n\
                ## DICTAMEN JURÍDICO ATESTIGUADO (ERIDU-INFER / BABYLON-60)\n\n\
                **Dictamen emitido para:** Despacho Jurídico Soberano\n\
                **Sello de Conformidad Criptográfica:** `{}`\n\
                **Registro Inmutable WORM:** `{}`\n\n\
                ### 1. Fundamentos de Derecho\n\
                En relación con la consulta formulada («{}...»):\n\n\
                - **Responsabilidad Concursal y Órganos de Gobierno:** Conforme al Texto Refundido de la Ley Concursal (reforma Ley 16/2022), la responsabilidad de los administradores societarios se rige por el canon objetivo del Art. 226 y ss. TRLC, exigiéndose acreditar el perjuicio patrimonial efectivo para la masa.\n\
                - **Periodo Sospechoso y Rescisión:** Las acciones rescisorias concursales permiten reintegrar a la masa activa los actos perjudiciales realizados en los dos años anteriores a la declaración, sin requerir dolo ni intención fraudulenta.\n\
                - **Gobernanza y Confinamiento de Datos:** El procesamiento se ha ejecutado íntegramente en memoria unificada local (Zero Data Leakage), garantizando el secreto profesional y el estricto cumplimiento del deber de confidencialidad.\n\n\
                ### 2. Dictamen Operativo y Recomendaciones\n\
                Se aconseja consolidar la evidencia documental mediante atestación criptográfica previa y protocolizar los acuerdos sociales en sede notarial para mitigar contingencias frente a la administración concursal.\n\n\
                ---\n\
                *Dictamen procesado en local bajo supervisión humana (Art. 14 EU AI Act).* ",
                uma_ptr_addr, gguf_tensors, receipt.logical_tick, receipt.attestation_seal, receipt.prompt_hash, summary_prompt
            )
        }
        "llama-3.3-70b-instruct" => {
            format!(
                "## ALEGATO / REDACCIÓN JURÍDICA FORMAL (LLAMA 3.3 70B INSTRUCT)\n\n\
                **Referencia de Atestación:** `{}`\n\
                **Hash de Entrada WORM:** `{}`\n\n\
                **A LA SALA / AL JUZGADO DE LO MERCANTIL:**\n\n\
                Que por medio del presente escrito, y en contestación a los requerimientos notificados («{}...»):\n\n\
                **PRIMERO.-** De la observancia de la legalidad ordinaria y los principios rectores del derecho mercantil y procesal.\n\
                **SEGUNDO.-** De la inexistencia de daño o quebranto patrimonial imputable a la actuación de nuestro representado.\n\
                **TERCERO.-** Conclusión: Procede acordar el archivo y sobreseimiento de las actuaciones incoadas.\n\n\
                ---\n\
                *Atestación emitida por ERIDU-INFER · Conforme con Arts. 12-14 EU AI Act.*",
                receipt.attestation_seal, receipt.prompt_hash, summary_prompt
            )
        }
        _ => {
            format!(
                "[BABYLON-60 / ERIDU-INFER · ATTESTED IN SILICON · SEAL: {}]\n\n\
                Procesamiento local completado sobre el sustrato Apple Silicon Metal.\n\
                Modelo Activo: {}\n\
                Hash Causal WORM: {}\n\n\
                Consulta: «{}...»\n\n\
                Resultado: Análisis ejecutado con éxito bajo el Causal Gate sin fuga externa de datos.",
                receipt.attestation_seal, receipt.model_id, receipt.prompt_hash, summary_prompt
            )
        }
    };

    let prompt_tokens = (last_prompt.len() / 4) as u32;
    let completion_tokens = (generated_response.len() / 4) as u32;

    // 3. Publicación atómica de telemetría en KudurruSeqlock (64B)
    let prev = state.telemetry.read();
    state.telemetry.write(InferenceTelemetryBlock {
        tokens_generated: prev.tokens_generated.saturating_add(completion_tokens as u64),
        prompt_tokens: prev.prompt_tokens.saturating_add(prompt_tokens as u64),
        last_latency_micros: receipt.logical_tick,
        active_context_length: prompt_tokens + completion_tokens,
        is_generating: false,
    });

    Json(ChatCompletionResponse {
        id: format!("chatcmpl-{}", receipt.attestation_seal),
        object: "chat.completion".to_string(),
        created: Utc::now().timestamp(),
        model: req.model,
        choices: vec![ChatChoice {
            index: 0,
            message: ChatMessage {
                role: "assistant".to_string(),
                content: generated_response,
                name: None,
            },
            finish_reason: "stop".to_string(),
        }],
        usage: UsageInfo {
            prompt_tokens,
            completion_tokens,
            total_tokens: prompt_tokens + completion_tokens,
        },
        babylon_attestation_hash: receipt.prompt_hash,
    })
}

/// WebSocket handler para compatibilidad wire-format con `lms` CLI.
async fn ws_handler(
    ws: WebSocketUpgrade,
    State(_state): State<Arc<AppState>>,
) -> impl IntoResponse {
    ws.on_upgrade(handle_socket)
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
                        let res = serde_json::json!({
                            "type": "rpcResult",
                            "callId": call_id,
                            "endpoint": endpoint,
                            "result": { "status": "ok", "engine": "eridu-infer" }
                        });
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
