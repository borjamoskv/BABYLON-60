// C5-REAL EXERGY CERTIFIED
use std::time::Instant;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

// ═══════════════════════════════════════════════════════
//  INFERENCE KERNEL — C5-REAL Local Transformers/MLX/Ollama
//  Rule: Zero-Network Policy (Strict localhost boundary)
// ═══════════════════════════════════════════════════════

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceConfig {
    pub model: String,
    pub base_url: String,
    pub temperature: f32,
    pub max_tokens: u32,
}

impl Default for InferenceConfig {
    fn default() -> Self {
        Self {
            model: "qwen2.5-coder:32b".to_string(),
            base_url: "http://127.0.0.1:11434/v1".to_string(),
            temperature: 0.2,
            max_tokens: 1024,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InferenceResult {
    pub text: String,
    pub model: String,
    pub tps: f64,
    pub latency_ms: u128,
    pub sha256: String,
    pub provider: String,
}

/// Enforces the C5-REAL Zero-Network Policy.
/// Traps and purges any attempt to route to hyperscalers.
pub fn validate_local_endpoint(url: &str) -> Result<(), String> {
    let lower = url.to_lowercase();
    if lower.contains("openai.com")
        || lower.contains("anthropic.com")
        || lower.contains("dashscope")
        || lower.contains("googleapis.com")
        || lower.contains("deepmind")
    {
        return Err(format!(
            "C5-REAL VIOLATION: Zero-Network Policy breached. External endpoint '{}' is strictly forbidden. Inference confined to local silicon.",
            url
        ));
    }
    if !lower.starts_with("http://127.0.0.1") && !lower.starts_with("http://localhost") {
        return Err(format!(
            "C5-REAL VIOLATION: Endpoint '{}' is outside loopback (127.0.0.1 / localhost).",
            url
        ));
    }
    Ok(())
}

/// Computes SHA256 invariant of generated output text.
fn compute_hash(text: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(text.as_bytes());
    hex::encode(hasher.finalize())
}

/// Synchronous local inference via Ollama / MLX-LM local REST socket (`127.0.0.1:11434`).
pub fn run_local_inference(
    prompt: &str,
    model: Option<String>,
    base_url: Option<String>,
    temperature: Option<f32>,
) -> Result<InferenceResult, String> {
    let config = InferenceConfig {
        model: model.unwrap_or_else(|| "qwen2.5-coder:32b".to_string()),
        base_url: base_url.unwrap_or_else(|| "http://127.0.0.1:11434/v1".to_string()),
        temperature: temperature.unwrap_or(0.2),
        max_tokens: 1024,
    };

    validate_local_endpoint(&config.base_url)?;

    let endpoint = format!("{}/chat/completions", config.base_url.trim_end_matches('/'));
    let start_time = Instant::now();

    // Prepare payload compatible with local OpenAI-format sockets (MLX / Ollama / vLLM)
    let payload = json!({
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": "You are MOSKV-1 APEX, a sovereign C5-REAL execution kernel operating on local Apple Silicon. Emit concise, deterministic technical solutions without filler or safety theater."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": false
    });

    // Simple HTTP client over std or curl fallback for pure local loopback without heavy reqwest async overhead
    let client = std::process::Command::new("curl")
        .arg("-s")
        .arg("-X")
        .arg("POST")
        .arg(&endpoint)
        .arg("-H")
        .arg("Content-Type: application/json")
        .arg("-d")
        .arg(payload.to_string())
        .output()
        .map_err(|e| format!("Failed to invoke local inference socket via curl: {}", e))?;

    if !client.status.success() {
        let err_msg = String::from_utf8_lossy(&client.stderr);
        return Err(format!(
            "Local inference socket returned error status: {}",
            err_msg
        ));
    }

    let raw_resp = String::from_utf8_lossy(&client.stdout);
    let json_resp: Value = serde_json::from_str(&raw_resp).map_err(|e| {
        format!(
            "Failed to parse JSON response from local daemon (is Ollama/MLX running on port 11434?): {} | Raw: {}",
            e, raw_resp.chars().take(200).collect::<String>()
        )
    })?;

    if let Some(err) = json_resp.get("error") {
        return Err(format!("Local daemon error: {}", err));
    }

    let text = json_resp["choices"][0]["message"]["content"]
        .as_str()
        .unwrap_or("")
        .to_string();

    let latency_ms = start_time.elapsed().as_millis();
    let token_count = text.split_whitespace().count().max(1) as f64 * 1.33; // Approx tokens
    let tps = if latency_ms > 0 {
        token_count / (latency_ms as f64 / 1000.0)
    } else {
        0.0
    };

    let sha256 = compute_hash(&text);

    Ok(InferenceResult {
        text,
        model: config.model,
        tps,
        latency_ms,
        sha256,
        provider: "LOCAL_SILICON_MLX_OLLAMA".to_string(),
    })
}

/// Checks availability of local silicon endpoints (`127.0.0.1:11434` and `/api/tags`).
pub fn check_local_status() -> Result<Value, String> {
    let output = std::process::Command::new("curl")
        .arg("-s")
        .arg("http://127.0.0.1:11434/api/tags")
        .output()
        .map_err(|e| format!("Failed to probe localhost:11434: {}", e))?;

    if !output.status.success() {
        return Ok(json!({
            "status": "OFFLINE",
            "provider": "Ollama/MLX",
            "endpoint": "http://127.0.0.1:11434",
            "models": []
        }));
    }

    let raw = String::from_utf8_lossy(&output.stdout);
    if let Ok(json_val) = serde_json::from_str::<Value>(&raw) {
        let models = json_val["models"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|m| m["name"].as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or_default();

        return Ok(json!({
            "status": "ONLINE",
            "provider": "Ollama/MLX Local Silicon",
            "endpoint": "http://127.0.0.1:11434",
            "models": models
        }));
    }

    Ok(json!({
        "status": "OFFLINE",
        "provider": "Ollama/MLX",
        "endpoint": "http://127.0.0.1:11434",
        "models": []
    }))
}
