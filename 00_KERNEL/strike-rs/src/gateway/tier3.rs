// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! Tier 3: Local Inference Engine (Apple MLX / Ollama / llama.cpp)
//!
//! Invariants Enforced:
//! - INV_C5_T3_01: LocalInferenceBackend trait abstraction (Stage 1 utility).
//! - INV_C5_T3_02: BLAKE3 attestation of all inference output (AX-5 cost of falsification).
//! - INV_C5_T3_03: Health tracking with exponential cooldown (AX-3 anti-escalation).
//! - INV_C5_T3_04: Zero-panic, fail-stop on unrecoverable backend errors.

use async_trait::async_trait;
use blake3::Hasher;
use std::fmt;
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use tokio::time::timeout;

// ─── Quantization Levels ─────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq)]
#[allow(non_camel_case_types)]
pub enum Quantization {
    F16,
    Q8_0,
    Q4_K_M,
    Q4_0,
}

impl fmt::Display for Quantization {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Quantization::F16 => write!(f, "F16"),
            Quantization::Q8_0 => write!(f, "Q8_0"),
            Quantization::Q4_K_M => write!(f, "Q4_K_M"),
            Quantization::Q4_0 => write!(f, "Q4_0"),
        }
    }
}

// ─── Model Specification ─────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct ModelSpec {
    pub model_id: String,
    pub vram_budget_mb: u32,
    pub max_context_tokens: u32,
    pub quantization: Quantization,
}

impl Default for ModelSpec {
    fn default() -> Self {
        Self {
            model_id: "mock-local-v0".to_string(),
            vram_budget_mb: 512,
            max_context_tokens: 2048,
            quantization: Quantization::Q4_K_M,
        }
    }
}

// ─── Inference Output (Attestation Layer) ────────────────────────────────────

/// Output from a local inference call, with BLAKE3 attestation hash (INV_C5_T3_02).
#[derive(Debug, Clone)]
pub struct InferenceOutput {
    pub content: String,
    pub tokens_generated: u32,
    pub ttft_ms: u64,
    pub total_ms: u64,
    pub content_hash: String,
    pub model_id: String,
}

impl InferenceOutput {
    /// Compute and attach BLAKE3 attestation hash to content.
    pub fn attested(content: String, tokens_generated: u32, ttft_ms: u64, total_ms: u64, model_id: &str) -> Self {
        let mut hasher = Hasher::new();
        hasher.update(content.as_bytes());
        hasher.update(model_id.as_bytes());
        let content_hash = format!("T3_BLAKE3:{}", hasher.finalize().to_hex());

        Self {
            content,
            tokens_generated,
            ttft_ms,
            total_ms,
            content_hash,
            model_id: model_id.to_string(),
        }
    }
}

// ─── Health Status ───────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub enum HealthStatus {
    Healthy { last_ttft_ms: u64 },
    Degraded { reason: String, consecutive_failures: u32 },
    Dead { last_failure: String },
}

impl HealthStatus {
    pub fn is_available(&self) -> bool {
        !matches!(self, HealthStatus::Dead { .. })
    }
}

// ─── Tier 3 Errors ──────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub enum Tier3Error {
    BackendUnavailable(String),
    InferenceTimeout { deadline_ms: u64 },
    BackendError(String),
    CooldownActive { remaining_ms: u64 },
}

impl fmt::Display for Tier3Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Tier3Error::BackendUnavailable(msg) => write!(f, "T3 Backend Unavailable: {}", msg),
            Tier3Error::InferenceTimeout { deadline_ms } => write!(f, "T3 Inference Timeout: {}ms", deadline_ms),
            Tier3Error::BackendError(msg) => write!(f, "T3 Backend Error: {}", msg),
            Tier3Error::CooldownActive { remaining_ms } => write!(f, "T3 Cooldown Active: {}ms remaining", remaining_ms),
        }
    }
}

// ─── Backend Trait (INV_C5_T3_01) ────────────────────────────────────────────

/// Trait boundary for local inference backends.
/// Any backend (MLX, Ollama, llama.cpp) must implement this trait
/// to be usable as a Tier 3 provider in the CognitiveGateway.
#[async_trait]
pub trait LocalInferenceBackend: Send + Sync {
    /// Execute inference on a prompt. Returns attestation-ready output.
    async fn infer(&self, prompt: &str, max_tokens: u32) -> Result<InferenceOutput, Tier3Error>;

    /// Lightweight health probe. Must not allocate or run inference.
    async fn health_check(&self) -> HealthStatus;

    /// Return the model specification for this backend.
    fn model_spec(&self) -> &ModelSpec;
}

// ─── Tier 3 Engine (INV_C5_T3_03) ───────────────────────────────────────────

/// Orchestrates local inference with health tracking, exponential cooldown,
/// and BLAKE3 attestation. Wraps any `LocalInferenceBackend`.
pub struct Tier3Engine {
    backend: Arc<dyn LocalInferenceBackend>,
    health: RwLock<HealthStatus>,
    consecutive_failures: AtomicU32,
    last_failure_epoch_ms: AtomicU64,
    cooldown_base_ms: u64,
    cooldown_cap_ms: u64,
    inference_timeout_ms: u64,
}

impl Tier3Engine {
    pub fn new(backend: Arc<dyn LocalInferenceBackend>) -> Self {
        Self {
            backend,
            health: RwLock::new(HealthStatus::Healthy { last_ttft_ms: 0 }),
            consecutive_failures: AtomicU32::new(0),
            last_failure_epoch_ms: AtomicU64::new(0),
            cooldown_base_ms: 1000,
            cooldown_cap_ms: 60_000,
            inference_timeout_ms: 5000,
        }
    }

    pub fn with_config(
        backend: Arc<dyn LocalInferenceBackend>,
        cooldown_base_ms: u64,
        cooldown_cap_ms: u64,
        inference_timeout_ms: u64,
    ) -> Self {
        Self {
            backend,
            health: RwLock::new(HealthStatus::Healthy { last_ttft_ms: 0 }),
            consecutive_failures: AtomicU32::new(0),
            last_failure_epoch_ms: AtomicU64::new(0),
            cooldown_base_ms,
            cooldown_cap_ms,
            inference_timeout_ms,
        }
    }

    /// Check if the engine is available (not dead or in cooldown).
    pub async fn is_available(&self) -> bool {
        let health = self.health.read().await;
        match &*health {
            HealthStatus::Healthy { .. } => true,
            HealthStatus::Degraded { consecutive_failures, .. } => {
                // Allow retries even when degraded, but check cooldown
                if *consecutive_failures > 0 {
                    !self.is_in_cooldown()
                } else {
                    true
                }
            }
            HealthStatus::Dead { .. } => !self.is_in_cooldown(),
        }
    }

    /// Compute the current cooldown duration based on consecutive failures.
    fn current_cooldown_ms(&self) -> u64 {
        let failures = self.consecutive_failures.load(Ordering::Relaxed);
        if failures == 0 {
            return 0;
        }
        let cooldown = self.cooldown_base_ms.saturating_mul(1u64 << failures.min(16));
        cooldown.min(self.cooldown_cap_ms)
    }

    /// Check if the engine is within cooldown period.
    fn is_in_cooldown(&self) -> bool {
        let last_failure = self.last_failure_epoch_ms.load(Ordering::Relaxed);
        if last_failure == 0 {
            return false;
        }
        let now_ms = epoch_ms();
        let cooldown = self.current_cooldown_ms();
        now_ms < last_failure.saturating_add(cooldown)
    }

    /// Execute inference with health tracking and attestation.
    pub async fn execute(&self, prompt: &str, max_tokens: u32) -> Result<InferenceOutput, Tier3Error> {
        // 1. Cooldown gate
        if self.is_in_cooldown() {
            let remaining = {
                let last = self.last_failure_epoch_ms.load(Ordering::Relaxed);
                let cooldown = self.current_cooldown_ms();
                last.saturating_add(cooldown).saturating_sub(epoch_ms())
            };
            return Err(Tier3Error::CooldownActive { remaining_ms: remaining });
        }

        // 2. Execute with timeout
        let start = Instant::now();
        let result = timeout(
            Duration::from_millis(self.inference_timeout_ms),
            self.backend.infer(prompt, max_tokens),
        ).await;

        match result {
            Ok(Ok(output)) => {
                // Success: reset failure state
                self.consecutive_failures.store(0, Ordering::Relaxed);
                self.last_failure_epoch_ms.store(0, Ordering::Relaxed);
                let mut health = self.health.write().await;
                *health = HealthStatus::Healthy { last_ttft_ms: output.ttft_ms };
                Ok(output)
            }
            Ok(Err(e)) => {
                // Backend returned an error
                self.record_failure(&format!("{}", e)).await;
                Err(e)
            }
            Err(_elapsed) => {
                // Timeout
                let elapsed_ms = start.elapsed().as_millis() as u64;
                self.record_failure(&format!("Inference timeout after {}ms", elapsed_ms)).await;
                Err(Tier3Error::InferenceTimeout { deadline_ms: self.inference_timeout_ms })
            }
        }
    }

    /// Record a failure and update health state.
    async fn record_failure(&self, reason: &str) {
        let failures = self.consecutive_failures.fetch_add(1, Ordering::Relaxed) + 1;
        self.last_failure_epoch_ms.store(epoch_ms(), Ordering::Relaxed);

        let mut health = self.health.write().await;
        if failures >= 5 {
            *health = HealthStatus::Dead {
                last_failure: reason.to_string(),
            };
        } else {
            *health = HealthStatus::Degraded {
                reason: reason.to_string(),
                consecutive_failures: failures,
            };
        }
    }

    /// Hard reset the engine health state.
    pub async fn reset(&self) {
        self.consecutive_failures.store(0, Ordering::Relaxed);
        self.last_failure_epoch_ms.store(0, Ordering::Relaxed);
        let mut health = self.health.write().await;
        *health = HealthStatus::Healthy { last_ttft_ms: 0 };
    }

    /// Clear only the cooldown timer without resetting health or failure count.
    /// Used for testing to allow immediate retries while preserving failure state.
    pub fn clear_cooldown(&self) {
        self.last_failure_epoch_ms.store(0, Ordering::Relaxed);
    }

    /// Get current health status snapshot.
    pub async fn health(&self) -> HealthStatus {
        self.health.read().await.clone()
    }

    /// Get the model spec from the underlying backend.
    pub fn model_spec(&self) -> &ModelSpec {
        self.backend.model_spec()
    }
}

// ─── Mock Backend (Test/PoC) ─────────────────────────────────────────────────

/// Mock local inference backend for testing and stress testing.
/// Simulates latency and configurable failure patterns.
pub struct MockLocalBackend {
    pub spec: ModelSpec,
    pub latency_ms: u64,
    pub fail_rate: f64,
}

impl MockLocalBackend {
    pub fn new(latency_ms: u64, fail_rate: f64) -> Self {
        Self {
            spec: ModelSpec::default(),
            latency_ms,
            fail_rate,
        }
    }

    pub fn with_spec(latency_ms: u64, fail_rate: f64, spec: ModelSpec) -> Self {
        Self {
            spec,
            latency_ms,
            fail_rate,
        }
    }
}

#[async_trait]
impl LocalInferenceBackend for MockLocalBackend {
    async fn infer(&self, prompt: &str, max_tokens: u32) -> Result<InferenceOutput, Tier3Error> {
        let start = Instant::now();

        // Simulate processing latency
        tokio::time::sleep(Duration::from_millis(self.latency_ms)).await;

        // Stochastic failure simulation
        if self.fail_rate > 0.0 {
            let should_fail = {
                use rand::Rng;
                let mut rng = rand::thread_rng();
                rng.gen_bool(self.fail_rate.clamp(0.0, 1.0))
            };
            if should_fail {
                return Err(Tier3Error::BackendError("Mock stochastic failure".to_string()));
            }
        }

        let total_ms = start.elapsed().as_millis() as u64;
        let content = format!("T3_LOCAL_DRAFT[{}t|{}]", max_tokens, &prompt[..prompt.len().min(32)]);
        let tokens = max_tokens.min(128); // Mock token count

        Ok(InferenceOutput::attested(
            content,
            tokens,
            self.latency_ms / 2, // Mock TTFT ~ half total latency
            total_ms,
            &self.spec.model_id,
        ))
    }

    async fn health_check(&self) -> HealthStatus {
        HealthStatus::Healthy { last_ttft_ms: self.latency_ms / 2 }
    }

    fn model_spec(&self) -> &ModelSpec {
        &self.spec
    }
}

// ─── Utility ─────────────────────────────────────────────────────────────────

fn epoch_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

// ─── Tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn mock_backend(latency_ms: u64, fail_rate: f64) -> Arc<dyn LocalInferenceBackend> {
        Arc::new(MockLocalBackend::new(latency_ms, fail_rate))
    }

    #[tokio::test]
    async fn test_successful_inference_with_attestation() {
        let engine = Tier3Engine::new(mock_backend(10, 0.0));
        let result = engine.execute("test prompt", 64).await;
        assert!(result.is_ok());

        let output = result.unwrap();
        assert!(output.content_hash.starts_with("T3_BLAKE3:"));
        assert!(output.tokens_generated > 0);
        assert_eq!(output.model_id, "mock-local-v0");
    }

    #[tokio::test]
    async fn test_health_transitions_on_failure() {
        let engine = Tier3Engine::with_config(
            mock_backend(5, 1.0), // 100% fail rate
            100, 5000, 10000,
        );

        // First failure → Degraded
        let _ = engine.execute("fail", 32).await;
        match engine.health().await {
            HealthStatus::Degraded { consecutive_failures, .. } => {
                assert_eq!(consecutive_failures, 1);
            }
            other => panic!("Expected Degraded, got {:?}", other),
        }

        // 4 more failures → Dead (threshold = 5)
        for _ in 0..4 {
            // Reset cooldown so we can actually call execute
            engine.last_failure_epoch_ms.store(0, Ordering::Relaxed);
            let _ = engine.execute("fail", 32).await;
        }
        match engine.health().await {
            HealthStatus::Dead { .. } => {}
            other => panic!("Expected Dead after 5 failures, got {:?}", other),
        }
    }

    #[tokio::test]
    async fn test_cooldown_blocks_execution() {
        let engine = Tier3Engine::with_config(
            mock_backend(5, 1.0),
            500, 60000, 10000,
        );

        // Trigger failure
        let _ = engine.execute("fail", 32).await;

        // Immediate retry should be blocked by cooldown
        let result = engine.execute("retry", 32).await;
        match result {
            Err(Tier3Error::CooldownActive { .. }) => {}
            other => panic!("Expected CooldownActive, got {:?}", other),
        }
    }

    #[tokio::test]
    async fn test_reset_clears_health() {
        let engine = Tier3Engine::with_config(
            mock_backend(5, 1.0),
            100, 5000, 10000,
        );

        // Trigger failures
        let _ = engine.execute("fail", 32).await;
        engine.reset().await;

        match engine.health().await {
            HealthStatus::Healthy { .. } => {}
            other => panic!("Expected Healthy after reset, got {:?}", other),
        }
        assert!(engine.is_available().await);
    }

    #[tokio::test]
    async fn test_blake3_hash_determinism() {
        let o1 = InferenceOutput::attested("hello world".into(), 2, 5, 10, "model-a");
        let o2 = InferenceOutput::attested("hello world".into(), 2, 5, 10, "model-a");
        let o3 = InferenceOutput::attested("hello world".into(), 2, 5, 10, "model-b");

        // Same content + model → same hash
        assert_eq!(o1.content_hash, o2.content_hash);
        // Different model → different hash
        assert_ne!(o1.content_hash, o3.content_hash);
    }

    #[tokio::test]
    async fn test_is_available_when_healthy() {
        let engine = Tier3Engine::new(mock_backend(5, 0.0));
        assert!(engine.is_available().await);
    }
}
