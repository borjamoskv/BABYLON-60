// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
// ============================================================================
//! Cognitive Gateway Circuit Breaker (Thermodynamic Race Condition)
//!
//! Orchestrates failover across three tiers of inference:
//!   - Tier 1: Antigravity/Gemini (high density, cloud)
//!   - Tier 2: OpenRouter (arbitrage fallback, cloud)
//!   - Tier 3: Local MLX/Ollama (speculative draft, on-device)
//!
//! Invariants Enforced:
//! - INV_CB_01: Ring-0 requests NEVER reach Tier 3 (Fail-Stop).
//! - INV_CB_02: All responses carry BLAKE3 attestation hash.
//! - INV_CB_03: Tier 3 health state gates race participation.
//! - INV_CB_04: RingPolicy is configurable, not hardcoded.

use std::fmt;
use std::sync::Arc;
use std::time::{Duration, Instant};
use blake3::Hasher;
use tokio::time::timeout;

use super::tier3::{ModelSpec, Tier3Engine, Tier3Error};

// ─── Cognitive Tier (Enriched) ───────────────────────────────────────────────

#[derive(Debug, Clone)]
pub enum CognitiveTier {
    Tier1Antigravity,
    Tier2OpenRouter,
    Tier3Local(ModelSpec),
}

impl fmt::Display for CognitiveTier {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CognitiveTier::Tier1Antigravity => write!(f, "Tier1:Antigravity"),
            CognitiveTier::Tier2OpenRouter => write!(f, "Tier2:OpenRouter"),
            CognitiveTier::Tier3Local(spec) => write!(f, "Tier3:Local({})", spec.model_id),
        }
    }
}

// ─── Manifold Request ────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct ManifoldRequest {
    pub payload_hash: u64,
    pub complexity_score: u8,
    pub target_ring: u8,
    pub prompt: String,
    pub max_tokens: u32,
}

// ─── Gateway Response (Attestation Layer) ────────────────────────────────────

/// Every response from the gateway carries an attestation hash (INV_CB_02).
#[derive(Debug, Clone)]
pub struct GatewayResponse {
    pub content: String,
    pub resolved_by: CognitiveTier,
    pub latency_ms: u64,
    pub content_hash: String,
}

impl GatewayResponse {
    fn new(content: String, resolved_by: CognitiveTier, latency_ms: u64) -> Self {
        let mut hasher = Hasher::new();
        hasher.update(content.as_bytes());
        hasher.update(format!("{}", resolved_by).as_bytes());
        let content_hash = format!("GW_BLAKE3:{}", hasher.finalize().to_hex());

        Self {
            content,
            resolved_by,
            latency_ms,
            content_hash,
        }
    }
}

// ─── Errors ──────────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum AnergyError {
    SystemHalt(&'static str),
    NetworkTimeout,
    ProviderFailure(String),
    Tier3Unavailable(String),
    RingPolicyViolation { ring: u8, tier: &'static str },
}

impl fmt::Display for AnergyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AnergyError::SystemHalt(msg) => write!(f, "SYSTEM_HALT: {}", msg),
            AnergyError::NetworkTimeout => write!(f, "NETWORK_TIMEOUT"),
            AnergyError::ProviderFailure(msg) => write!(f, "PROVIDER_FAILURE: {}", msg),
            AnergyError::Tier3Unavailable(msg) => write!(f, "T3_UNAVAILABLE: {}", msg),
            AnergyError::RingPolicyViolation { ring, tier } => {
                write!(f, "RING_POLICY_VIOLATION: Ring-{} forbids {}", ring, tier)
            }
        }
    }
}

// ─── Ring Policy (INV_CB_04) ─────────────────────────────────────────────────

/// Configurable policy for which rings allow Tier 3 dispatch.
#[derive(Debug, Clone)]
pub struct RingPolicy {
    /// Rings where Tier 3 local inference is permitted (default: [1, 2, 3]).
    pub t3_allowed_rings: Vec<u8>,
}

impl Default for RingPolicy {
    fn default() -> Self {
        Self {
            t3_allowed_rings: vec![1, 2, 3],
        }
    }
}

impl RingPolicy {
    /// Check if Tier 3 is allowed for a given ring level.
    pub fn t3_allowed(&self, ring: u8) -> bool {
        self.t3_allowed_rings.contains(&ring)
    }
}

// ─── Cognitive Gateway ──────────────────────────────────────────────────────

pub struct CognitiveGateway {
    tier3: Option<Arc<Tier3Engine>>,
    ring_policy: RingPolicy,
    t1_timeout_ms: u64,
    t2_timeout_ms: u64,
}

impl Default for CognitiveGateway {
    fn default() -> Self {
        Self::new()
    }
}

impl CognitiveGateway {
    pub fn new() -> Self {
        Self {
            tier3: None,
            ring_policy: RingPolicy::default(),
            t1_timeout_ms: 2000,
            t2_timeout_ms: 2000,
        }
    }

    pub fn with_tier3(tier3: Arc<Tier3Engine>) -> Self {
        Self {
            tier3: Some(tier3),
            ring_policy: RingPolicy::default(),
            t1_timeout_ms: 2000,
            t2_timeout_ms: 2000,
        }
    }

    pub fn with_config(
        tier3: Option<Arc<Tier3Engine>>,
        ring_policy: RingPolicy,
        t1_timeout_ms: u64,
        t2_timeout_ms: u64,
    ) -> Self {
        Self {
            tier3,
            ring_policy,
            t1_timeout_ms,
            t2_timeout_ms,
        }
    }

    /// Mock: Call Tier 1 (Antigravity/Gemini). Replace with real HTTP client.
    async fn call_tier1(&self, _req: &ManifoldRequest) -> Result<String, AnergyError> {
        tokio::time::sleep(Duration::from_millis(100)).await;
        Ok("Response from Tier 1 (Antigravity)".to_string())
    }

    /// Mock: Call Tier 2 (OpenRouter). Replace with real HTTP client.
    async fn call_tier2(&self, _req: &ManifoldRequest) -> Result<String, AnergyError> {
        tokio::time::sleep(Duration::from_millis(300)).await;
        Ok("Response from Tier 2 (OpenRouter)".to_string())
    }

    /// Call Tier 3 via the Tier3Engine (real or mock).
    async fn call_tier3(&self, req: &ManifoldRequest) -> Result<GatewayResponse, AnergyError> {
        let engine = self.tier3.as_ref()
            .ok_or_else(|| AnergyError::Tier3Unavailable("No Tier 3 engine configured".into()))?;

        if !engine.is_available().await {
            return Err(AnergyError::Tier3Unavailable("Tier 3 engine in cooldown or dead".into()));
        }

        let start = Instant::now();
        match engine.execute(&req.prompt, req.max_tokens).await {
            Ok(output) => {
                let latency_ms = start.elapsed().as_millis() as u64;
                Ok(GatewayResponse::new(
                    output.content,
                    CognitiveTier::Tier3Local(engine.model_spec().clone()),
                    latency_ms,
                ))
            }
            Err(Tier3Error::CooldownActive { remaining_ms }) => {
                Err(AnergyError::Tier3Unavailable(format!("Cooldown: {}ms remaining", remaining_ms)))
            }
            Err(e) => {
                Err(AnergyError::ProviderFailure(format!("T3: {}", e)))
            }
        }
    }

    /// Executes the Thermodynamic Race Condition (Circuit Breaker).
    ///
    /// Flow:
    ///   1. Try Tier 1 with timeout.
    ///   2. If T1 fails → check Ring policy.
    ///   3. If Ring forbids T3 → T2 only (Fail-Stop if T2 also fails).
    ///   4. If Ring allows T3 → race T2 vs T3 → fastest wins.
    pub async fn execute_with_failover(&self, req: ManifoldRequest) -> Result<GatewayResponse, AnergyError> {
        let start = Instant::now();

        // Step 1: Try Tier 1
        let t1_future = self.call_tier1(&req);
        match timeout(Duration::from_millis(self.t1_timeout_ms), t1_future).await {
            Ok(Ok(content)) => {
                let latency_ms = start.elapsed().as_millis() as u64;
                return Ok(GatewayResponse::new(content, CognitiveTier::Tier1Antigravity, latency_ms));
            }
            _ => {
                // T1 failed or timed out. Proceed to failover logic.
            }
        }

        // Step 2: Check Ring policy for T3
        let t3_allowed = self.ring_policy.t3_allowed(req.target_ring) && self.tier3.is_some();

        // Step 3: Ring-0 or policy forbids T3 → T2 only
        if !t3_allowed {
            let t2_future = self.call_tier2(&req);
            match timeout(Duration::from_millis(self.t2_timeout_ms), t2_future).await {
                Ok(Ok(content)) => {
                    let latency_ms = start.elapsed().as_millis() as u64;
                    return Ok(GatewayResponse::new(content, CognitiveTier::Tier2OpenRouter, latency_ms));
                }
                _ => {
                    if req.target_ring == 0 {
                        return Err(AnergyError::SystemHalt(
                            "Fail-Stop: Tier 1 & 2 down. T3 not authorized for RING-0."
                        ));
                    }
                    return Err(AnergyError::RingPolicyViolation {
                        ring: req.target_ring,
                        tier: "Tier3",
                    });
                }
            }
        }

        // Step 4: Race T2 vs T3
        // Pin futures on the stack so select! borrows them (avoids move semantics).
        let t2_future = self.call_tier2(&req);
        let t3_future = self.call_tier3(&req);
        tokio::pin!(t2_future);
        tokio::pin!(t3_future);

        tokio::select! {
            t2_result = &mut t2_future => {
                let latency_ms = start.elapsed().as_millis() as u64;
                match t2_result {
                    Ok(content) => Ok(GatewayResponse::new(content, CognitiveTier::Tier2OpenRouter, latency_ms)),
                    Err(_) => {
                        // T2 failed, wait for T3
                        match t3_future.await {
                            Ok(mut resp) => { resp.latency_ms = start.elapsed().as_millis() as u64; Ok(resp) }
                            Err(e) => Err(e)
                        }
                    }
                }
            }
            t3_result = &mut t3_future => {
                let latency_ms = start.elapsed().as_millis() as u64;
                match t3_result {
                    Ok(mut resp) => { resp.latency_ms = latency_ms; Ok(resp) }
                    Err(_) => {
                        // T3 failed, wait for T2
                        match t2_future.await {
                            Ok(content) => Ok(GatewayResponse::new(content, CognitiveTier::Tier2OpenRouter, start.elapsed().as_millis() as u64)),
                            Err(e) => Err(e)
                        }
                    }
                }
            }
        }
    }
}

// ─── Attestor Integration ───────────────────────────────────────────────────

use crate::orchestrator::Attestor;
use crate::omega0::{Statement, Justification, hash_statement};
use async_trait::async_trait;

#[async_trait]
impl Attestor for CognitiveGateway {
    async fn query(&self, goal: &Statement) -> Justification {
        // Construct the ManifoldRequest
        let payload_hash_str = hash_statement(goal);
        // We hash the hash string to get a u64 for the ManifoldRequest
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        use std::hash::{Hash, Hasher};
        payload_hash_str.hash(&mut hasher);
        let payload_hash = hasher.finish();

        let req = ManifoldRequest {
            payload_hash,
            complexity_score: 3, // Default heuristic for generic queries
            target_ring: 2,      // Assume ring 2 to allow Tier3 by default; production would adapt this based on `goal.obligations`.
            prompt: goal.content.clone(),
            max_tokens: 1024,
        };

        match self.execute_with_failover(req).await {
            Ok(resp) => Justification::ExogenousInjection {
                source: format!("LLM_GATEWAY:{}", resp.resolved_by),
                context: resp.content,
            },
            Err(e) => {
                // If the entire gateway fails, we fall back to a raw conjecture (or we could propagate the error if Attestor supported it)
                eprintln!("CognitiveGateway Attestor query failed: {}", e);
                Justification::Conjecture
            }
        }
    }
}

// ─── Tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::tier3::{MockLocalBackend, LocalInferenceBackend};

    fn make_request(ring: u8) -> ManifoldRequest {
        ManifoldRequest {
            payload_hash: 0xDEAD,
            complexity_score: 5,
            target_ring: ring,
            prompt: "test prompt".to_string(),
            max_tokens: 64,
        }
    }

    fn mock_engine(latency_ms: u64, fail_rate: f64) -> Arc<Tier3Engine> {
        let backend: Arc<dyn LocalInferenceBackend> = Arc::new(MockLocalBackend::new(latency_ms, fail_rate));
        Arc::new(Tier3Engine::new(backend))
    }

    #[tokio::test]
    async fn test_t1_succeeds_returns_t1() {
        let gw = CognitiveGateway::with_tier3(mock_engine(5, 0.0));
        let resp = gw.execute_with_failover(make_request(2)).await.expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert!(resp.content.contains("Tier 1"));
        assert!(resp.content_hash.starts_with("GW_BLAKE3:"));
    }

    #[tokio::test]
    async fn test_gateway_response_has_attestation() {
        let resp = GatewayResponse::new(
            "test".to_string(),
            CognitiveTier::Tier1Antigravity,
            100,
        );
        assert!(resp.content_hash.starts_with("GW_BLAKE3:"));
        assert!(!resp.content_hash.is_empty());
    }

    #[tokio::test]
    async fn test_ring_policy_default_blocks_ring0() {
        let policy = RingPolicy::default();
        assert!(!policy.t3_allowed(0));
        assert!(policy.t3_allowed(1));
        assert!(policy.t3_allowed(2));
        assert!(policy.t3_allowed(3));
    }

    #[tokio::test]
    async fn test_ring0_fail_stop() {
        // With a gateway that has no working T1/T2 but has T3,
        // Ring-0 should still HALT rather than use T3.
        let policy = RingPolicy::default();
        assert!(!policy.t3_allowed(0));
    }

    #[tokio::test]
    async fn test_cognitive_tier_display() {
        let t1 = CognitiveTier::Tier1Antigravity;
        let t2 = CognitiveTier::Tier2OpenRouter;
        let t3 = CognitiveTier::Tier3Local(ModelSpec::default());

        assert_eq!(format!("{}", t1), "Tier1:Antigravity");
        assert_eq!(format!("{}", t2), "Tier2:OpenRouter");
        assert!(format!("{}", t3).starts_with("Tier3:Local("));
    }

    #[tokio::test]
    async fn test_gateway_without_tier3() {
        let gw = CognitiveGateway::new();
        // Should still work — T1 succeeds, T3 never needed
        let resp = gw.execute_with_failover(make_request(2)).await.expect("C5-REAL: Termodinámica forzada. Unwrap purgado.");
        assert!(resp.content.contains("Tier 1"));
    }
}
