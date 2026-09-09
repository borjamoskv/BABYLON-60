// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! Tier 3: Ollama HTTP Backend Integration
//!
//! Maps local HTTP endpoints (e.g., localhost:11434) to the LocalInferenceBackend trait.
//! Enforces:
//! - Strict timeouts.
//! - Non-streaming standard responses to capture metadata (eval_duration, prompt_eval_count).

use async_trait::async_trait;
use reqwest::{Client, ClientBuilder};
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};

use crate::gateway::tier3::{
    HealthStatus, InferenceOutput, LocalInferenceBackend, ModelSpec, Quantization, Tier3Error,
};

// ─── DTOs for Ollama API ─────────────────────────────────────────────────────

#[derive(Serialize)]
struct OllamaGenerateRequest<'a> {
    model: &'a str,
    prompt: &'a str,
    stream: bool,
    options: OllamaOptions,
}

#[derive(Serialize)]
struct OllamaOptions {
    num_predict: u32,
    temperature: f32,
}

#[derive(Deserialize, Debug)]
struct OllamaGenerateResponse {
    response: String,
    done: bool,
    eval_count: Option<u32>,
    eval_duration: Option<u64>,  // in nanoseconds
    load_duration: Option<u64>,  // in nanoseconds
}

#[derive(Deserialize, Debug)]
struct OllamaTagsResponse {
    models: Vec<OllamaModelInfo>,
}

#[derive(Deserialize, Debug)]
struct OllamaModelInfo {
    name: String,
}

// ─── Ollama Backend ─────────────────────────────────────────────────────────

pub struct OllamaBackend {
    endpoint: String,
    client: Client,
    spec: ModelSpec,
}

impl OllamaBackend {
    /// Initialize a new Ollama backend targeting a specific endpoint (e.g. "http://localhost:11434")
    pub fn new(endpoint: &str, model_name: &str) -> Result<Self, reqwest::Error> {
        let client = ClientBuilder::new()
            .timeout(Duration::from_secs(30)) // Upper bound failsafe timeout
            .build()?;

        let spec = ModelSpec {
            model_id: model_name.to_string(),
            vram_budget_mb: 2048,           // Default assumption
            max_context_tokens: 4096,       // Default assumption
            quantization: Quantization::Q4_K_M, // Standard for Ollama
        };

        Ok(Self {
            endpoint: endpoint.trim_end_matches('/').to_string(),
            client,
            spec,
        })
    }
}

#[async_trait]
impl LocalInferenceBackend for OllamaBackend {
    async fn infer(&self, prompt: &str, max_tokens: u32) -> Result<InferenceOutput, Tier3Error> {
        let start = Instant::now();

        let req_body = OllamaGenerateRequest {
            model: &self.spec.model_id,
            prompt,
            stream: false, // Wait for full response to get the exact eval durations
            options: OllamaOptions {
                num_predict: max_tokens,
                temperature: 0.1, // Near deterministic
            },
        };

        let url = format!("{}/api/generate", self.endpoint);

        let response = self.client.post(&url)
            .json(&req_body)
            .send()
            .await
            .map_err(|e| Tier3Error::BackendError(format!("Network error: {}", e)))?;

        if !response.status().is_success() {
            let status = response.status();
            let text = response.text().await.unwrap_or_default();
            return Err(Tier3Error::BackendError(format!("HTTP {} - {}", status, text)));
        }

        let ollama_resp: OllamaGenerateResponse = response.json().await
            .map_err(|e| Tier3Error::BackendError(format!("Parse error: {}", e)))?;

        let total_ms = start.elapsed().as_millis() as u64;

        // Extract metrics (Ollama returns nanoseconds)
        let tokens_generated = ollama_resp.eval_count.unwrap_or(0);
        let eval_duration_ms = ollama_resp.eval_duration.map(|ns| ns / 1_000_000).unwrap_or(total_ms);
        let load_duration_ms = ollama_resp.load_duration.map(|ns| ns / 1_000_000).unwrap_or(0);
        
        // Approximate TTFT: Total time minus the evaluation duration (which is the generation phase)
        let ttft_ms = total_ms.saturating_sub(eval_duration_ms).max(load_duration_ms);

        Ok(InferenceOutput::attested(
            ollama_resp.response,
            tokens_generated,
            ttft_ms,
            total_ms,
            &self.spec.model_id,
        ))
    }

    async fn health_check(&self) -> HealthStatus {
        let start = Instant::now();
        let url = format!("{}/api/tags", self.endpoint);

        match self.client.get(&url).timeout(Duration::from_millis(500)).send().await {
            Ok(resp) if resp.status().is_success() => {
                if let Ok(tags) = resp.json::<OllamaTagsResponse>().await {
                    let has_model = tags.models.iter().any(|m| m.name == self.spec.model_id || m.name == format!("{}:latest", self.spec.model_id));
                    if has_model {
                        HealthStatus::Healthy { last_ttft_ms: start.elapsed().as_millis() as u64 }
                    } else {
                        HealthStatus::Degraded { 
                            reason: format!("Model '{}' not found in Ollama", self.spec.model_id),
                            consecutive_failures: 1 
                        }
                    }
                } else {
                    HealthStatus::Degraded { reason: "Failed to parse Ollama tags".to_string(), consecutive_failures: 1 }
                }
            }
            Ok(resp) => {
                HealthStatus::Degraded { reason: format!("Ollama returned HTTP {}", resp.status()), consecutive_failures: 1 }
            }
            Err(e) => {
                HealthStatus::Dead { last_failure: format!("Ollama unreachable: {}", e) }
            }
        }
    }

    fn model_spec(&self) -> &ModelSpec {
        &self.spec
    }
}
