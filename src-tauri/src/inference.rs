// C5-REAL: LOCAL INFERENCE MOTOR (TRANSFORMERS / MLX / LLAMA.CPP)
// =================================================================================
// SYS_ID: MOSKV-1 APEX ULTRATHINK P0 (Tauri v2 / Rust Agnostic Inference Layer)
// REALITY_LEVEL: C5-REAL (Zero-Network Policy / Local Silicon / WAL Ledger Audit)
// [CORTEX-TAINT:borjamoskv:inference_motor:2026-07-18T05:00:00Z]

use std::sync::Arc;
use std::time::Instant;
use tokio::net::TcpStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use serde::{Deserialize, Serialize};
use crate::void::VoidLedger;

#[derive(Serialize, Debug)]
struct OllamaRequest {
    model: String,
    prompt: String,
    stream: bool,
}

#[derive(Deserialize, Debug)]
struct OllamaResponse {
    response: Option<String>,
    error: Option<String>,
    eval_count: Option<u64>,
    eval_duration: Option<u64>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct InferenceAuditRecord {
    pub status: String,
    pub model_used: String,
    pub latency_ms: u64,
    pub tokens_generated: u64,
    pub tps: f64,
    pub response_snippet: String,
}

pub struct LocalInferenceMotor {
    pub db_state: Arc<VoidLedger>,
    pub default_model: String,
    pub fallback_model: String,
    pub endpoint_host: String,
    pub endpoint_port: u16,
}

impl LocalInferenceMotor {
    pub fn new(db_state: Arc<VoidLedger>) -> Self {
        Self {
            db_state,
            default_model: "qwen2.5:32b".to_string(),
            fallback_model: "llama3:8b".to_string(),
            endpoint_host: "127.0.0.1".to_string(),
            endpoint_port: 11434, // Ollama / MLX / llama.cpp default socket
        }
    }

    /// Execute local inference via zero-network raw TCP socket to localhost
    pub async fn execute_inference(&self, prompt: &str, requested_model: Option<&str>) -> Result<InferenceAuditRecord, String> {
        let primary_model = requested_model.unwrap_or(&self.default_model);
        let _start_time = Instant::now();

        // Try primary model first
        match self.send_raw_http_post(primary_model, prompt).await {
            Ok(record) => {
                let _ = self.audit_to_ledger(&record, prompt);
                Ok(record)
            }
            Err(primary_err) => {
                println!("⚠️ [INFERENCE_MOTOR] Fallo en modelo primario ({}): {}. Activando CascadeRouter fallback a {}...", primary_model, primary_err, self.fallback_model);
                // Circuit Breaker / Graceful Degradation to fallback local model
                match self.send_raw_http_post(&self.fallback_model, prompt).await {
                    Ok(mut fallback_record) => {
                        fallback_record.status = format!("C5-REAL_FALLBACK_FROM_{}", primary_model);
                        let _ = self.audit_to_ledger(&fallback_record, prompt);
                        Ok(fallback_record)
                    }
                    Err(fallback_err) => {
                        let err_msg = format!("FATAL_LOCAL_INFERENCE_EXHAUSTED: Primary ({}) -> {}; Fallback ({}) -> {}", primary_model, primary_err, self.fallback_model, fallback_err);
                        let _ = self.db_state.write(&err_msg, "INFERENCE_MOTOR:FAIL");
                        Err(err_msg)
                    }
                }
            }
        }
    }

    async fn send_raw_http_post(&self, model: &str, prompt: &str) -> Result<InferenceAuditRecord, String> {
        let addr = format!("{}:{}", self.endpoint_host, self.endpoint_port);
        let mut stream = TcpStream::connect(&addr).await.map_err(|e| format!("Socket Connect Error: {}", e))?;

        let req_payload = OllamaRequest {
            model: model.to_string(),
            prompt: prompt.to_string(),
            stream: false,
        };
        let body_json = serde_json::to_string(&req_payload).map_err(|e| format!("JSON Serialize Error: {}", e))?;

        let http_req = format!(
            "POST /api/generate HTTP/1.1\r\nHost: {}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
            addr,
            body_json.len(),
            body_json
        );

        stream.write_all(http_req.as_bytes()).await.map_err(|e| format!("Socket Write Error: {}", e))?;
        stream.flush().await.map_err(|e| format!("Socket Flush Error: {}", e))?;

        let mut raw_response = Vec::new();
        stream.read_to_end(&mut raw_response).await.map_err(|e| format!("Socket Read Error: {}", e))?;

        let resp_str = String::from_utf8_lossy(&raw_response);
        let body_str = if let Some(idx) = resp_str.find("\r\n\r\n") {
            &resp_str[idx + 4..]
        } else if let Some(idx) = resp_str.find("\n\n") {
            &resp_str[idx + 2..]
        } else {
            &resp_str
        };

        // Check HTTP status code
        if !resp_str.starts_with("HTTP/1.1 200") && !resp_str.starts_with("HTTP/1.0 200") {
            return Err(format!("HTTP Error response: {}", body_str.trim().chars().take(200).collect::<String>()));
        }

        let parsed = serde_json::from_str::<OllamaResponse>(body_str.trim())
            .map_err(|e| format!("Response Parse Error: {} on payload: {}", e, body_str.chars().take(100).collect::<String>()))?;

        if let Some(err) = parsed.error {
            return Err(format!("Ollama daemon error: {}", err));
        }

        let response_text = parsed.response.unwrap_or_else(|| "".to_string());
        let tokens = parsed.eval_count.unwrap_or(response_text.split_whitespace().count() as u64);
        let duration_ns = parsed.eval_duration.unwrap_or(1000000); // default 1ms to prevent div by zero
        let duration_sec = duration_ns as f64 / 1_000_000_000.0;
        let tps = if duration_sec > 0.0 { tokens as f64 / duration_sec } else { 0.0 };
        let latency_ms = (duration_ns / 1_000_000) as u64;

        Ok(InferenceAuditRecord {
            status: "C5-REAL_LOCAL_SILICON".to_string(),
            model_used: model.to_string(),
            latency_ms,
            tokens_generated: tokens,
            tps,
            response_snippet: response_text.chars().take(500).collect(),
        })
    }

    fn audit_to_ledger(&self, record: &InferenceAuditRecord, prompt: &str) -> Result<(), String> {
        let audit_payload = format!(
            "INFERENCE_EXEC|model:{}|tokens:{}|tps:{:.2}|latency:{}ms|prompt_len:{}|resp:{}",
            record.model_used, record.tokens_generated, record.tps, record.latency_ms, prompt.len(), record.response_snippet
        );
        let taint = format!("INFERENCE_MOTOR:{}", record.model_used);
        self.db_state.write(&audit_payload, &taint).map_err(|e| format!("Ledger Write Error: {:?}", e))
    }
}

// Tauri commands exposed to frontend / IPC
#[tauri::command]
pub async fn infer_local_command(
    prompt: String,
    model_type: Option<String>,
    state: tauri::State<'_, crate::Apex>,
) -> Result<InferenceAuditRecord, String> {
    let motor = LocalInferenceMotor::new(state.void_state.clone());
    motor.execute_inference(&prompt, model_type.as_deref()).await
}

#[tauri::command]
pub async fn check_inference_health_command(
    state: tauri::State<'_, crate::Apex>,
) -> Result<String, String> {
    let motor = LocalInferenceMotor::new(state.void_state.clone());
    let addr = format!("{}:{}", motor.endpoint_host, motor.endpoint_port);
    
    match TcpStream::connect(&addr).await {
        Ok(_) => {
            let msg = format!("{{\"status\": \"C5-REAL_ACTIVE\", \"socket\": \"{}\", \"default_model\": \"{}\"}}", addr, motor.default_model);
            let _ = state.void_state.write(&msg, "INFERENCE_HEALTH_CHECK:OK");
            Ok(msg)
        }
        Err(e) => {
            let msg = format!("{{\"status\": \"C4-SIM_OFFLINE\", \"socket\": \"{}\", \"error\": \"{}\"}}", addr, e);
            let _ = state.void_state.write(&msg, "INFERENCE_HEALTH_CHECK:FAIL");
            Ok(msg)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use crate::void::VoidLedger;

    #[test]
    fn test_local_inference_motor_init() {
        if let Ok(db) = VoidLedger::init() {
            let motor = LocalInferenceMotor::new(Arc::new(db));
            assert_eq!(motor.default_model, "qwen2.5:32b");
            assert_eq!(motor.fallback_model, "llama3:8b");
            assert_eq!(motor.endpoint_host, "127.0.0.1");
            assert_eq!(motor.endpoint_port, 11434);
        }
    }
}
