//! # OWASP ACS v0.1.0 ↔ BABYLON-60 Ring-0 Enforcement Bridge (`FL-016` & `FL-LABOR-001`)
//!
//! Legacy authorization remains fail-closed. The `authenticated` API verifies a root-signed
//! grant, request signature, kernel socket credentials and durable nonce before returning a decision.
//! Software signatures do not certify hardware provenance or authorize protected mutations.

use sha2::{Digest, Sha256};

use crate::manifest::POISONED;
use crate::ontology::babylon::{
    Authority, Capability, Decision, EffectKind, EffectRequest, EnforcementMode, Policy,
    Reversibility,
};
use crate::ontology::laws::OntologicalViolation;

/// Canonical ACS v0.1.0 protocol version string.
pub const ACS_PROTOCOL_VERSION: &str = "0.1.0";

/// Fail-stop failure behavior enforced by BABYLON-60 (`INV-4`).
/// Note: `Proceed` (Fail-Open) is included ONLY to deterministically reject misconfigured
/// external ACS clients during handshake (`AcsBridgeError::FailOpenProhibited`).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FailureDecisionPolicy {
    /// Sovereign Ring-0 default: immediately abort and poison state (`0xDEAD_6060`).
    FailClosedAbort,
    /// Prohibited by Ring-0: external ACS `on_decision_failure = "proceed"`.
    ProceedUnchecked,
}

/// Transport channel classification for ACS ingestion (`INV_C5_ONWIRE_CANON`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AcsTransportConfinement {
    /// Sovereign local Unix domain socket with kernel-verified peer credentials (`getpeereid`).
    AfUnixPeerVerified {
        /// Socket path on APFS.
        socket_path: String,
        /// Kernel-attested peer Effective UID.
        peer_euid: u32,
        /// Kernel-attested peer PID.
        peer_pid: u32,
    },
    /// Prohibited unauthenticated TCP/HTTP daemon transport.
    UnauthenticatedHttp {
        /// Endpoint URL rejected by `INV_C5_ONWIRE_CANON`.
        endpoint: String,
    },
}

/// Incoming OWASP ACS v0.1.0 `toolCallRequest` envelope (`protocols/MCP/tools/call`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AcsToolCallRequest {
    /// Protocol version claimed by observed agent.
    pub acs_version: String,
    /// Unique request identifier (`request_id`).
    pub request_id: [u8; 32],
    /// Anti-replay single-use cryptographic nonce.
    pub nonce: [u8; 32],
    /// Tool name requested by the agent (e.g., `"bash"`, `"atomic_write"`, `"fs_read"`, `"curl"`).
    pub tool_name: String,
    /// Command arguments or payload string.
    pub arguments: String,
    /// Target resource URI (`file:///...`, `net://...`).
    pub target_uri: String,
    /// Client-supplied timestamp (validated against system logical tick per Law O13).
    pub client_logical_tick: u64,
    /// Context telemetry digest.
    pub context_digest: [u8; 32],
    /// Detached signature bytes over canonical CBOR payload (P-256 / Ed25519).
    pub signature: Vec<u8>,
}

/// Outgoing OWASP ACS v0.1.0 `permissionDecision` response envelope.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AcsPermissionDecision {
    /// Backing request identifier.
    pub request_id: [u8; 32],
    /// Sovereign BABYLON-60 decision struct (7-tuple evaluation).
    pub decision: Decision,
    /// Monoid poison state (`0` if nominal, `0xDEAD_6060` on `SecurityAbort`).
    pub poison_word: u32,
    /// True if escalated to physical Touch ID / human operator (`RequireApproval`).
    pub escalated_to_human: bool,
}

/// Deterministic errors raised by the ACS ↔ BABYLON-60 enforcement bridge.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AcsBridgeError {
    /// Unsupported or mismatched ACS protocol version.
    UnsupportedProtocolVersion(String),
    /// Client attempted to configure `on_decision_failure: "proceed"` (violates `0xDEAD_6060`).
    FailOpenProhibited {
        /// Poison code sealed on rejection.
        poison_word: u32,
    },
    /// Client attempted to use unauthenticated HTTP instead of `AF_UNIX` (`INV_C5_ONWIRE_CANON`).
    TransportViolation(String),
    /// Missing or empty cryptographic signature on ACS envelope.
    MissingSignature,
    /// No authenticated trust root, transport verifier, or durable replay store is installed.
    AuthenticationUnavailable,
    /// Signature does not verify against the independently provisioned key.
    InvalidSignature,
    /// Malformed, expired or out-of-scope authenticated request.
    InvalidRequest(String),
    /// Durable anti-replay storage failed; no authorization is returned.
    StorageFailure(String),
    /// Anti-replay nonce reuse detected (`INV_C5_NEMESIS_EVIDENCE_CONTRACT`).
    NonceReplayDetected([u8; 32]),
    /// Ontological law violation (O2..O14).
    LawViolation(OntologicalViolation),
}

/// Sovereign BABYLON-60 Guard configured as an OWASP ACS v0.1.0 Enforcement Engine.
#[derive(Debug, Clone)]
pub struct BabylonAcsGuard {
    /// Governing authority identity.
    pub authority: Authority,
    /// Active capability token delegated to the observed agent.
    pub capability: Capability,
    /// Active deterministic policy bundle.
    pub policy: Policy,
    /// Transport confinement descriptor.
    pub transport: AcsTransportConfinement,
    /// Authoritative logical clock tick (`INV_C5_CANONICAL_LOGICAL_TICK`).
    pub system_logical_tick: u64,
    /// Maximum tolerated clock skew in ticks (Law O13).
    pub max_clock_skew_ticks: u64,
    /// Whether OS-level Seatbelt / `O_NOFOLLOW` confinement is active (Law O14).
    pub kernel_confinement_active: bool,
    /// Monoid state word (`0` = nominal, `0xDEAD_6060` = poisoned fail-stop).
    pub state_word: u32,
}

impl BabylonAcsGuard {
    /// Instantiates a new `BabylonAcsGuard`, enforcing `INV_C5_ONWIRE_CANON` and `INV-4` at setup.
    ///
    /// Rejects `FailureDecisionPolicy::ProceedUnchecked` and `AcsTransportConfinement::UnauthenticatedHttp`
    /// immediately in fail-closed mode.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        authority: Authority,
        capability: Capability,
        policy: Policy,
        transport: AcsTransportConfinement,
        failure_policy: FailureDecisionPolicy,
        system_logical_tick: u64,
        max_clock_skew_ticks: u64,
        kernel_confinement_active: bool,
    ) -> Result<Self, AcsBridgeError> {
        if failure_policy == FailureDecisionPolicy::ProceedUnchecked {
            return Err(AcsBridgeError::FailOpenProhibited {
                poison_word: POISONED,
            });
        }
        if let AcsTransportConfinement::UnauthenticatedHttp { endpoint } = &transport {
            return Err(AcsBridgeError::TransportViolation(endpoint.clone()));
        }
        if policy.enforcement_mode != EnforcementMode::FailClosed {
            return Err(AcsBridgeError::FailOpenProhibited {
                poison_word: POISONED,
            });
        }
        Ok(Self {
            authority,
            capability,
            policy,
            transport,
            system_logical_tick,
            max_clock_skew_ticks,
            kernel_confinement_active,
            state_word: 0,
        })
    }

    /// Classifies an ACS tool invocation into a canonical BABYLON-60 `(EffectKind, Reversibility)`.
    pub fn classify_tool_effect(tool_name: &str, arguments: &str) -> (EffectKind, Reversibility) {
        let lower_args = arguments.to_ascii_lowercase();
        if tool_name == "bash" || tool_name == "zsh" || tool_name == "sh" {
            if lower_args.contains("rm ")
                || lower_args.contains("unlink")
                || lower_args.contains("shred")
            {
                return (EffectKind::FsDelete, Reversibility::Irreversible);
            }
            if lower_args.contains("shutdown") || lower_args.contains("kill") {
                return (EffectKind::ProcTerminate, Reversibility::Irreversible);
            }
            if lower_args.contains("curl ")
                || lower_args.contains("wget ")
                || lower_args.contains("nc ")
            {
                return (EffectKind::NetTransmit, Reversibility::Irreversible);
            }
            return (EffectKind::ProcSpawn, Reversibility::Irreversible);
        }
        match tool_name {
            "fs_read" | "view_file" | "read_file" => {
                (EffectKind::FsRead, Reversibility::Reversible)
            }
            "atomic_write" | "write_file" => (EffectKind::FsMutate, Reversibility::Compensatable),
            "fs_delete" => (EffectKind::FsDelete, Reversibility::Irreversible),
            "curl" | "http_post" | "net_egress" => {
                (EffectKind::NetTransmit, Reversibility::Irreversible)
            }
            _ => (EffectKind::ProcSpawn, Reversibility::Irreversible),
        }
    }

    /// Computes the canonical 32-byte digest of the 7-tuple $\mathcal{T}_{\text{auth}}$:
    /// `(Authority, Capability, Policy, Resource, Effect, Context, Epoch)`.
    pub fn compute_7tuple_digest(&self, req: &EffectRequest) -> [u8; 32] {
        let mut hasher = Sha256::new();
        hasher.update(b"BABYLON60_ACS_7TUPLE_V1");
        hasher.update(req.authority_id);
        hasher.update(req.capability_id);
        hasher.update(self.policy.predicate_digest);
        hasher.update(req.resource_uri.as_bytes());
        hasher.update(req.proposed_effect.effect_id);
        hasher.update([req.proposed_effect.effect_kind as u8]);
        hasher.update(req.context_digest);
        hasher.update(req.requested_epoch.to_le_bytes());
        hasher.update(self.system_logical_tick.to_le_bytes());
        hasher.finalize().into()
    }

    /// Rejects every request until authenticated transport, signature verification and
    /// durable anti-replay protection are installed. A configured policy is not authentication.
    pub fn evaluate_tool_call(
        &mut self,
        acs_req: &AcsToolCallRequest,
    ) -> Result<AcsPermissionDecision, AcsBridgeError> {
        if self.state_word == POISONED {
            return Err(AcsBridgeError::FailOpenProhibited {
                poison_word: POISONED,
            });
        }
        self.state_word = POISONED;
        if acs_req.acs_version != ACS_PROTOCOL_VERSION {
            return Err(AcsBridgeError::UnsupportedProtocolVersion(
                acs_req.acs_version.clone(),
            ));
        }
        if acs_req.signature.is_empty() {
            return Err(AcsBridgeError::MissingSignature);
        }
        Err(AcsBridgeError::AuthenticationUnavailable)
    }
}

// ---------------------------------------------------------------------------
// FL-LABOR-001: Human Supervision Bottleneck & Escalation Compression Metrics
// ---------------------------------------------------------------------------

/// Statistical summary for `FL-LABOR-001` comparing unmediated human-in-the-loop sessions
/// against `BABYLON-60` 7-tuple deterministic mediation (`n >= 30` cohorts, 95% CI).
#[derive(Debug, Clone, PartialEq)]
pub struct FlLabor001Report {
    /// Number of independent agent-session cohorts evaluated (`n >= 30`).
    pub sample_cohorts: usize,
    /// Total tool calls evaluated across all cohorts.
    pub total_tool_calls: usize,
    /// Mean multi-turn human wait stall rate WITHOUT Babylon Guard (baseline ~0.80).
    pub baseline_human_stall_rate_mean: f64,
    /// Mean human escalation rate WITH Babylon Guard (`RequireApproval` / total).
    pub babylon_escalation_rate_mean: f64,
    /// 95% confidence interval half-width for `babylon_escalation_rate_mean`.
    pub babylon_escalation_rate_ci95: f64,
    /// Deterministic block rate (`Deny` + `SecurityAbort` / total).
    pub deterministic_block_rate: f64,
    /// False positive rate on benign corpus (`0.0` certified).
    pub benign_false_positive_rate: f64,
    /// Supervision hours saved ratio (`baseline_hours / babylon_hours`).
    pub human_supervision_compression_ratio: f64,
}

/// Executes the `FL-LABOR-001` deterministic simulation across `cohorts` (`n >= 30`),
/// computing sample mean and 95% confidence intervals ($z_{0.975} = 1.96$).
pub fn evaluate_fl_labor_001_cohorts(
    baseline_stall_rates: &[f64],
    babylon_escalation_rates: &[f64],
    total_tool_calls: usize,
    deterministic_blocks: usize,
    benign_false_positives: usize,
) -> Option<FlLabor001Report> {
    let n = babylon_escalation_rates.len();
    if n < 30 || baseline_stall_rates.len() != n || total_tool_calls == 0 {
        return None;
    }

    let base_mean = baseline_stall_rates.iter().sum::<f64>() / (n as f64);
    let bab_mean = babylon_escalation_rates.iter().sum::<f64>() / (n as f64);

    let variance = babylon_escalation_rates
        .iter()
        .map(|&x| {
            let d = x - bab_mean;
            d * d
        })
        .sum::<f64>()
        / ((n - 1) as f64);
    let std_err = (variance / (n as f64)).sqrt();
    let ci95 = 1.96 * std_err;

    let compression_ratio = if bab_mean > 0.0 {
        base_mean / bab_mean
    } else {
        f64::INFINITY
    };

    Some(FlLabor001Report {
        sample_cohorts: n,
        total_tool_calls,
        baseline_human_stall_rate_mean: base_mean,
        babylon_escalation_rate_mean: bab_mean,
        babylon_escalation_rate_ci95: ci95,
        deterministic_block_rate: (deterministic_blocks as f64) / (total_tool_calls as f64),
        benign_false_positive_rate: (benign_false_positives as f64) / (total_tool_calls as f64),
        human_supervision_compression_ratio: compression_ratio,
    })
}

// ---------------------------------------------------------------------------
// VOP-1 (Verified Outcome Protocol), BABYLON DRIFT GUARD & Phi_BABYLON
// ---------------------------------------------------------------------------

/// Tri-state Verified Outcome Protocol (`VOP-1`) status:
/// `DispatchAccepted != TargetEffectCommitted` and `DispatchTimeout != !TargetEffectCommitted`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Vop1OutcomeState {
    /// Target effect was rejected prior to or during adapter dispatch; 0 bytes mutated.
    Rejected {
        /// Deterministic rejection reason.
        reason: String,
    },
    /// Dispatch occurred or timed out without durable post-state verification (`AUTH_003`).
    /// Never automatically retried; requires explicit physical reconciliation.
    Unknown {
        /// Consumed single-use nonce locked in `UNKNOWN` state.
        nonce: [u8; 32],
        /// Expected post-state digest if the effect had completed.
        expected_post_digest: [u8; 32],
    },
    /// Target effect was authorized, physically observed by an independent witness, and sealed:
    /// `VerifiedSuccess(e) => Authorized(e) & Observed(e) & EvidenceValid(e)`.
    VerifiedSuccess {
        /// Consumed single-use nonce.
        nonce: [u8; 32],
        /// Pre-execution physical digest.
        pre_state_digest: [u8; 32],
        /// Observed post-execution physical digest matching expected transition.
        observed_post_digest: [u8; 32],
        /// Cryptographic evidence receipt digest.
        evidence_receipt_digest: [u8; 32],
    },
}

impl Vop1OutcomeState {
    /// Evaluates whether `VOP-1` `VerifiedSuccess(e)` holds:
    /// requires `Authorized(e) && Observed(e) && EvidenceValid(e)`.
    pub fn is_verified_success(&self) -> bool {
        matches!(self, Self::VerifiedSuccess { .. })
    }

    /// Reconciles an `Unknown` outcome against an independent physical observation of the resource
    /// (`pre_state_digest` vs `expected_post_digest` vs `actual_physical_digest`).
    ///
    /// - If `actual_physical_digest == expected_post_digest`, transitions to `VerifiedSuccess`.
    /// - If `actual_physical_digest == pre_state_digest`, transitions to `Rejected` (rolled back / never applied).
    /// - Otherwise (concurrent third-party mutation), remains `Unknown` to preserve epistemic uncertainty.
    pub fn reconcile_unknown(
        &self,
        pre_state_digest: [u8; 32],
        actual_physical_digest: [u8; 32],
        evidence_receipt_digest: [u8; 32],
    ) -> Self {
        match self {
            Self::Unknown {
                nonce,
                expected_post_digest,
            } => {
                if actual_physical_digest == *expected_post_digest {
                    Self::VerifiedSuccess {
                        nonce: *nonce,
                        pre_state_digest,
                        observed_post_digest: actual_physical_digest,
                        evidence_receipt_digest,
                    }
                } else if actual_physical_digest == pre_state_digest {
                    Self::Rejected {
                        reason: "Physical witness confirmed pre-state intact; effect did not occur"
                            .to_string(),
                    }
                } else {
                    Self::Unknown {
                        nonce: *nonce,
                        expected_post_digest: *expected_post_digest,
                    }
                }
            }
            other => other.clone(),
        }
    }
}

/// `BABYLON DRIFT GUARD` (`CODA` / `2610.20845` & `FL-008`):
/// Cryptographically binds `(model_id, adapter_digest, tool_catalog_digest, skill_bundle_digest, policy_digest)`.
/// Any mutation in a skill, tool binary, or policy invalidates prior capability authorizations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BabylonDriftGuard {
    /// Attested model identifier.
    pub model_id: String,
    /// SHA-256 digest of the effect adapter binary/code.
    pub adapter_digest: [u8; 32],
    /// SHA-256 digest of the tool catalog schema.
    pub tool_catalog_digest: [u8; 32],
    /// SHA-256 digest of the active skill bundle (`SKILL.md` + scripts closure).
    pub skill_bundle_digest: [u8; 32],
    /// SHA-256 digest of the governing policy.
    pub policy_digest: [u8; 32],
}

impl BabylonDriftGuard {
    /// Computes the canonical 32-byte composite drift seal.
    pub fn compute_seal(&self) -> [u8; 32] {
        let mut h = Sha256::new();
        h.update(b"BABYLON60_DRIFT_GUARD_V1");
        h.update((self.model_id.len() as u64).to_le_bytes());
        h.update(self.model_id.as_bytes());
        h.update(self.adapter_digest);
        h.update(self.tool_catalog_digest);
        h.update(self.skill_bundle_digest);
        h.update(self.policy_digest);
        h.finalize().into()
    }

    /// Verifies that a live execution environment matches the attested `BabylonDriftGuard` seal.
    /// Returns `Ok(())` if identical, or `Err(drift_Seal)` if any component drifted.
    pub fn verify_no_drift(&self, live: &Self) -> Result<[u8; 32], [u8; 32]> {
        let expected = self.compute_seal();
        let actual = live.compute_seal();
        if expected == actual {
            Ok(expected)
        } else {
            Err(actual)
        }
    }
}

/// Computes the operational verified-work efficiency metric $\Phi_{\text{BABYLON}}$:
/// $$\Phi_{\text{BABYLON}} = \frac{\sum_i U_i \cdot \mathbf{1}[\text{VerifiedOutcome}_i]}{C_{\text{inference}} + \lambda_t T + \lambda_h H + \lambda_r R}$$
pub fn compute_phi_babylon(
    utilities_and_outcomes: &[(f64, &Vop1OutcomeState)],
    inference_cost: f64,
    latency_penalty: f64,
    human_intervention_penalty: f64,
    risk_penalty: f64,
) -> Option<f64> {
    let denom = inference_cost + latency_penalty + human_intervention_penalty + risk_penalty;
    if denom <= 0.0 || !denom.is_finite() {
        return None;
    }
    let verified_utility: f64 = utilities_and_outcomes
        .iter()
        .filter_map(|(u, state)| {
            if state.is_verified_success() && *u >= 0.0 && u.is_finite() {
                Some(*u)
            } else {
                None
            }
        })
        .sum();
    Some(verified_utility / denom)
}

// ---------------------------------------------------------------------------
// NEMESIS AUTOPSY (`PROBE` / `2610.22124` + `ARIA` / `2610.20780`)
// ---------------------------------------------------------------------------

/// Point of observable divergence during agent execution.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DivergencePoint {
    /// Step sequence index where deviation from authorized specification was detected.
    pub step_index: u64,
    /// Expected canonical state or precondition digest.
    pub expected_digest: [u8; 32],
    /// Observed actual state digest on substrate.
    pub observed_digest: [u8; 32],
    /// Divergence classification description.
    pub description: String,
}

/// Incident forensic package generated by NEMESIS AUTOPSY.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NemesisAutopsyReport {
    /// Unique incident identifier.
    pub incident_id: [u8; 32],
    /// Attested principal identity executing the action.
    pub principal_identity: [u8; 32],
    /// Canonical EffectRequest ID.
    pub requested_effect_id: [u8; 32],
    /// Active policy ID and version.
    pub policy_version: String,
    /// First observable divergence detected between proposal and substrate effect.
    pub first_divergence: DivergencePoint,
    /// Physical evidence digest from CORTEX WORM ledger.
    pub dispatch_evidence_digest: [u8; 32],
    /// Resulting tri-state VOP-1 outcome.
    pub observed_outcome: Vop1OutcomeState,
    /// Deterministic, reproducible steps to replicate the fault in sandbox.
    pub reproduction_steps: Vec<String>,
    /// Unverified signature bytes; construction leaves these empty. No hardware claim is made.
    pub cryptographic_attestation: Vec<u8>,
}

impl NemesisAutopsyReport {
    /// Collects untrusted incident data without signing it. The legacy key argument is
    /// ignored: arbitrary caller bytes cannot establish Secure Enclave provenance.
    #[expect(
        clippy::too_many_arguments,
        reason = "Keep the attested incident fields explicit at the call site"
    )]
    pub fn build(
        incident_id: [u8; 32],
        principal_identity: [u8; 32],
        requested_effect_id: [u8; 32],
        policy_version: String,
        first_divergence: DivergencePoint,
        dispatch_evidence_digest: [u8; 32],
        observed_outcome: Vop1OutcomeState,
        reproduction_steps: Vec<String>,
        _attestation_key: &[u8],
    ) -> Self {
        Self {
            incident_id,
            principal_identity,
            requested_effect_id,
            policy_version,
            first_divergence,
            dispatch_evidence_digest,
            observed_outcome,
            reproduction_steps,
            cryptographic_attestation: Vec::new(),
        }
    }

    /// Explicit capability status: no trusted authenticity verifier is installed.
    /// This does not validate a signature or certify any report field.
    pub fn verify_authenticity(&self) -> Result<(), AcsBridgeError> {
        Err(AcsBridgeError::AuthenticationUnavailable)
    }

    /// Legacy API retained fail-closed. This is not a checksum or signature implementation;
    /// use `verify_authenticity` to distinguish unavailable verification from valid evidence.
    pub fn verify_integrity(&self, _attestation_key: &[u8]) -> bool {
        self.verify_authenticity().is_ok()
    }
}

/// Authenticated ACS API. Legacy entry points above remain fail-closed.
#[cfg(unix)]
pub mod authenticated {
    use super::*;
    use crate::ontology::babylon::DecisionOutcome;
    use std::fs::{File, OpenOptions};
    use std::io::{Read, Seek, SeekFrom, Write};
    use std::os::fd::AsRawFd;
    use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
    use std::os::unix::net::UnixStream;
    use std::path::{Path, PathBuf};
    use std::sync::{Arc, Mutex};

    /// Verification keys must come from trusted provisioning, never the request envelope.
    #[derive(Clone, Debug, PartialEq, Eq)]
    pub enum VerificationKey {
        /// Raw Ed25519 public key pinned by trusted provisioning.
        Ed25519([u8; 32]),
        /// SEC1 encoded NIST P-256 point. Signatures use fixed-width COSE r||s encoding.
        P256(Vec<u8>),
    }

    impl VerificationKey {
        fn protected(&self) -> Vec<u8> {
            // Deterministic CBOR {1: -8} (EdDSA), or {1: -7} (ES256).
            vec![
                0xa1,
                0x01,
                if matches!(self, Self::Ed25519(_)) {
                    0x27
                } else {
                    0x26
                },
            ]
        }
        fn encoded(&self) -> Vec<u8> {
            match self {
                Self::Ed25519(k) => array(vec![uint(0), bytes(k)]),
                Self::P256(k) => array(vec![uint(1), bytes(k)]),
            }
        }
        fn verify(&self, message: &[u8], signature: &[u8]) -> Result<(), AcsBridgeError> {
            let valid = match self {
                Self::Ed25519(k) => {
                    match (
                        ed25519_dalek::VerifyingKey::from_bytes(k),
                        ed25519_dalek::Signature::from_slice(signature),
                    ) {
                        (Ok(k), Ok(s)) => k.verify_strict(message, &s).is_ok(),
                        _ => false,
                    }
                }
                Self::P256(k) => {
                    use p256::ecdsa::signature::Verifier;
                    match (
                        p256::ecdsa::VerifyingKey::from_sec1_bytes(k),
                        p256::ecdsa::Signature::from_slice(signature),
                    ) {
                        (Ok(k), Ok(s)) => k.verify(message, &s).is_ok(),
                        _ => false,
                    }
                }
            };
            if valid {
                Ok(())
            } else {
                Err(AcsBridgeError::InvalidSignature)
            }
        }
    }

    // Restricted deterministic CBOR profile: definite arrays, uints, byte/text strings only.
    // No maps with ambiguous key ordering, floats, indefinite lengths or decoder normalization.
    fn head(major: u8, n: u64) -> Vec<u8> {
        let mut out = Vec::new();
        match n {
            0..=23 => out.push((major << 5) | n as u8),
            24..=255 => out.extend_from_slice(&[(major << 5) | 24, n as u8]),
            256..=65535 => {
                out.push((major << 5) | 25);
                out.extend_from_slice(&(n as u16).to_be_bytes());
            }
            65536..=4294967295 => {
                out.push((major << 5) | 26);
                out.extend_from_slice(&(n as u32).to_be_bytes());
            }
            _ => {
                out.push((major << 5) | 27);
                out.extend_from_slice(&n.to_be_bytes());
            }
        }
        out
    }
    fn uint(n: u64) -> Vec<u8> {
        head(0, n)
    }
    fn bytes(b: &[u8]) -> Vec<u8> {
        let mut v = head(2, b.len() as u64);
        v.extend_from_slice(b);
        v
    }
    fn text(s: &str) -> Vec<u8> {
        let mut v = head(3, s.len() as u64);
        v.extend_from_slice(s.as_bytes());
        v
    }
    fn array(items: Vec<Vec<u8>>) -> Vec<u8> {
        let mut v = head(4, items.len() as u64);
        for item in items {
            v.extend(item);
        }
        v
    }
    /// COSE_Sign1 Sig_structure with an empty external AAD and algorithm protected header.
    pub fn signing_bytes(key: &VerificationKey, payload: &[u8]) -> Vec<u8> {
        array(vec![
            text("Signature1"),
            bytes(&key.protected()),
            bytes(&[]),
            bytes(payload),
        ])
    }
    /// Convert an external P-256 provider's DER signature (including Secure Enclave output)
    /// to the COSE ES256 r||s encoding. This conversion does not attest provider provenance.
    pub fn p256_der_to_cose_signature(der: &[u8]) -> Result<Vec<u8>, AcsBridgeError> {
        p256::ecdsa::Signature::from_der(der)
            .map(|s| s.to_bytes().to_vec())
            .map_err(|_| AcsBridgeError::InvalidSignature)
    }
    /// Complete tagged COSE_Sign1 object for export. Verification APIs reconstruct the payload
    /// from typed data and a pinned key; they never accept a key or algorithm from this object.
    pub fn cose_sign1(key: &VerificationKey, payload: &[u8], signature: &[u8]) -> Vec<u8> {
        let mut out = vec![0xd2];
        out.extend(array(vec![
            bytes(&key.protected()),
            vec![0xa0],
            bytes(payload),
            bytes(signature),
        ]));
        out
    }

    /// Every request field, epoch and expiry is authenticated. No defaults are inserted.
    #[derive(Clone, Debug)]
    pub struct SignedCall {
        /// Complete caller envelope, including detached signature.
        pub request: AcsToolCallRequest,
        /// Authority epoch authorized by the grant.
        pub epoch: u64,
        /// Inclusive logical-tick deadline.
        pub expires_at_tick: u64,
    }

    fn guard_payload(g: &BabylonAcsGuard) -> Vec<u8> {
        array(vec![
            bytes(&g.authority.authority_id),
            uint(g.authority.principal_type as u64),
            bytes(&g.authority.public_key),
            uint(g.authority.active_epoch),
            bytes(&g.capability.capability_id),
            bytes(&g.capability.issuer_authority_id),
            text(&g.capability.target_resource),
            array(
                g.capability
                    .allowed_effects
                    .iter()
                    .map(|e| uint(*e as u64))
                    .collect(),
            ),
            uint(g.capability.valid_until_epoch),
            bytes(&g.capability.signature),
            text(&g.policy.policy_id),
            text(&g.policy.version),
            bytes(&g.policy.predicate_digest),
            uint(g.policy.enforcement_mode as u64),
            uint(g.max_clock_skew_ticks),
        ])
    }

    /// Root-signed grant. The root key is provisioned separately; the delegated request key,
    /// policy, authority, capability, peer credentials and grant lifetime are bound by its signature.
    pub fn provisioning_bytes(
        guard: &BabylonAcsGuard,
        root: &VerificationKey,
        delegated: &VerificationKey,
        peer_uid: u32,
        peer_pid: u32,
        expires_at_tick: u64,
    ) -> Vec<u8> {
        signing_bytes(
            root,
            &array(vec![
                text("BABYLON60_ACS_GRANT_V1"),
                guard_payload(guard),
                root.encoded(),
                delegated.encoded(),
                uint(peer_uid as u64),
                uint(peer_pid as u64),
                uint(expires_at_tick),
            ]),
        )
    }

    const NONCE_MAGIC: &[u8] = b"BABYLON60_ACS_NONCES_V1\n";
    /// Explicitly created at provisioning; opening a missing or corrupted store fails closed.
    #[derive(Clone, Debug)]
    pub struct DurableNonces {
        file: Arc<Mutex<File>>,
        path: PathBuf,
    }

    fn storage(error: impl std::fmt::Display) -> AcsBridgeError {
        AcsBridgeError::StorageFailure(error.to_string())
    }

    impl DurableNonces {
        fn check_parent(path: &Path) -> Result<(), AcsBridgeError> {
            let parent = path
                .parent()
                .ok_or_else(|| storage("nonce store needs a private parent"))?;
            let m = std::fs::symlink_metadata(parent).map_err(storage)?;
            if !m.is_dir() || m.uid() != unsafe { libc::geteuid() } || m.mode() & 0o077 != 0 {
                return Err(storage(
                    "nonce store parent must be an owned private directory",
                ));
            }
            Ok(())
        }
        /// Only provisioning may create a new store; never call this as restart recovery.
        pub fn create(path: impl AsRef<Path>) -> Result<Self, AcsBridgeError> {
            let path = path.as_ref();
            Self::check_parent(path)?;
            let mut file = OpenOptions::new()
                .read(true)
                .write(true)
                .create_new(true)
                .mode(0o600)
                .custom_flags(libc::O_NOFOLLOW | libc::O_CLOEXEC)
                .open(path)
                .map_err(storage)?;
            file.write_all(NONCE_MAGIC).map_err(storage)?;
            file.sync_all().map_err(storage)?;
            File::open(path.parent().ok_or_else(|| storage("missing parent"))?)
                .map_err(storage)?
                .sync_all()
                .map_err(storage)?;
            Ok(Self {
                file: Arc::new(Mutex::new(file)),
                path: path.to_owned(),
            })
        }
        /// Reopen durable state without creating or repairing missing/corrupt files.
        pub fn open(path: impl AsRef<Path>) -> Result<Self, AcsBridgeError> {
            let path = path.as_ref();
            Self::check_parent(path)?;
            let file = OpenOptions::new()
                .read(true)
                .write(true)
                .custom_flags(libc::O_NOFOLLOW | libc::O_CLOEXEC)
                .open(path)
                .map_err(storage)?;
            let store = Self {
                file: Arc::new(Mutex::new(file)),
                path: path.to_owned(),
            };
            store.with_locked(|_| Ok(()))?;
            Ok(store)
        }
        fn with_locked<T>(
            &self,
            op: impl FnOnce(&mut File) -> Result<T, AcsBridgeError>,
        ) -> Result<T, AcsBridgeError> {
            let mut file = self.file.lock().map_err(storage)?;
            if unsafe { libc::flock(file.as_raw_fd(), libc::LOCK_EX) } != 0 {
                return Err(storage(std::io::Error::last_os_error()));
            }
            let result = (|| {
                let m = file.metadata().map_err(storage)?;
                let live = std::fs::symlink_metadata(&self.path).map_err(storage)?;
                if !m.is_file()
                    || m.nlink() != 1
                    || m.uid() != unsafe { libc::geteuid() }
                    || m.mode() & 0o077 != 0
                    || live.ino() != m.ino()
                    || live.dev() != m.dev()
                    || live.file_type().is_symlink()
                {
                    return Err(storage("nonce store identity or permissions changed"));
                }
                file.seek(SeekFrom::Start(0)).map_err(storage)?;
                let mut header = vec![0; NONCE_MAGIC.len()];
                file.read_exact(&mut header).map_err(storage)?;
                if header != NONCE_MAGIC || !(m.len() - NONCE_MAGIC.len() as u64).is_multiple_of(32)
                {
                    return Err(storage("corrupt nonce store"));
                }
                op(&mut file)
            })();
            let unlock = unsafe { libc::flock(file.as_raw_fd(), libc::LOCK_UN) };
            if unlock != 0 {
                return Err(storage(std::io::Error::last_os_error()));
            }
            result
        }
        fn consume(&self, nonce: &[u8; 32]) -> Result<(), AcsBridgeError> {
            if nonce == &[0; 32] {
                return Err(AcsBridgeError::InvalidRequest("zero nonce".into()));
            }
            self.with_locked(|file| {
                let mut stored = [0; 32];
                while file.stream_position().map_err(storage)?
                    < file.metadata().map_err(storage)?.len()
                {
                    file.read_exact(&mut stored).map_err(storage)?;
                    if &stored == nonce {
                        return Err(AcsBridgeError::NonceReplayDetected(*nonce));
                    }
                }
                file.write_all(nonce).map_err(storage)?;
                // Successful authorization is impossible until the nonce is durable.
                file.sync_all().map_err(storage)
            })
        }
    }

    fn peer_identity(stream: &UnixStream) -> Result<(u32, u32), AcsBridgeError> {
        #[cfg(target_os = "macos")]
        {
            let (mut uid, mut gid, mut pid) = (0, 0, 0i32);
            let mut len = std::mem::size_of::<i32>() as libc::socklen_t;
            if unsafe { libc::getpeereid(stream.as_raw_fd(), &mut uid, &mut gid) } != 0
                || unsafe {
                    libc::getsockopt(
                        stream.as_raw_fd(),
                        libc::SOL_LOCAL,
                        libc::LOCAL_PEERPID,
                        std::ptr::from_mut(&mut pid).cast(),
                        &mut len,
                    )
                } != 0
                || pid <= 0
            {
                return Err(AcsBridgeError::TransportViolation(
                    "kernel peer credential lookup failed".into(),
                ));
            }
            Ok((uid, pid as u32))
        }
        #[cfg(target_os = "linux")]
        {
            let mut cred: libc::ucred = unsafe { std::mem::zeroed() };
            let mut len = std::mem::size_of::<libc::ucred>() as libc::socklen_t;
            if unsafe {
                libc::getsockopt(
                    stream.as_raw_fd(),
                    libc::SOL_SOCKET,
                    libc::SO_PEERCRED,
                    std::ptr::from_mut(&mut cred).cast(),
                    &mut len,
                )
            } != 0
                || cred.pid <= 0
            {
                return Err(AcsBridgeError::TransportViolation(
                    "kernel peer credential lookup failed".into(),
                ));
            }
            Ok((cred.uid, cred.pid as u32))
        }
        #[cfg(not(any(target_os = "linux", target_os = "macos")))]
        {
            let _ = stream;
            Err(AcsBridgeError::AuthenticationUnavailable)
        }
    }

    /// A signed root grant snapshot. Configuration is private and cannot be replaced by request data.
    #[derive(Debug)]
    pub struct AuthenticatedAcsGuard {
        guard: BabylonAcsGuard,
        delegated: VerificationKey,
        peer_uid: u32,
        peer_pid: u32,
        grant_expiry: u64,
        nonces: DurableNonces,
    }
    /// Authorization result only; this does not attest hardware or execute a protected effect.
    #[derive(Debug)]
    pub struct AuthenticatedDecision {
        /// Identifier from the verified request.
        pub request_id: [u8; 32],
        /// Nonce already consumed durably.
        pub nonce: [u8; 32],
        /// Scoped-read authorization or requirement for a separate protected-effect approval.
        pub outcome: DecisionOutcome,
        /// Exact deterministic CBOR payload covered by the verified signature.
        pub authenticated_payload: Vec<u8>,
    }
    impl AuthenticatedAcsGuard {
        /// Verify a separately pinned root's grant before installing the request key.
        /// Only the built-in acs_scoped_read_v1/version 1 policy is supported; predicate_digest
        /// is signed provenance metadata, not arbitrary code to evaluate.
        #[allow(clippy::too_many_arguments)]
        pub fn provision(
            guard: BabylonAcsGuard,
            root: VerificationKey,
            delegated: VerificationKey,
            peer_uid: u32,
            peer_pid: u32,
            expires_at_tick: u64,
            grant_signature: &[u8],
            nonces: DurableNonces,
        ) -> Result<Self, AcsBridgeError> {
            root.verify(
                &provisioning_bytes(
                    &guard,
                    &root,
                    &delegated,
                    peer_uid,
                    peer_pid,
                    expires_at_tick,
                ),
                grant_signature,
            )?;
            if guard.state_word == POISONED
                || guard.policy.enforcement_mode != EnforcementMode::FailClosed
                || guard.capability.issuer_authority_id != guard.authority.authority_id
                || guard.authority.active_epoch > guard.capability.valid_until_epoch
                || guard.system_logical_tick > expires_at_tick
                || peer_pid == 0
                || guard.policy.policy_id != "acs_scoped_read_v1"
                || guard.policy.version != "1"
            {
                return Err(AcsBridgeError::InvalidRequest(
                    "invalid or expired provisioning grant".into(),
                ));
            }
            Ok(Self {
                guard,
                delegated,
                peer_uid,
                peer_pid,
                grant_expiry: expires_at_tick,
                nonces,
            })
        }
        /// Complete canonical request and grant context, excluding the request signature.
        pub fn payload(&self, call: &SignedCall) -> Vec<u8> {
            let r = &call.request;
            array(vec![
                text("BABYLON60_ACS_CALL_V1"),
                guard_payload(&self.guard),
                self.delegated.encoded(),
                uint(self.peer_uid as u64),
                uint(self.peer_pid as u64),
                uint(self.grant_expiry),
                text(&r.acs_version),
                bytes(&r.request_id),
                bytes(&r.nonce),
                text(&r.tool_name),
                text(&r.arguments),
                text(&r.target_uri),
                uint(r.client_logical_tick),
                bytes(&r.context_digest),
                uint(call.epoch),
                uint(call.expires_at_tick),
            ])
        }
        /// Bytes to sign with the delegated key using COSE Sig_structure.
        pub fn signing_bytes(&self, call: &SignedCall) -> Vec<u8> {
            signing_bytes(&self.delegated, &self.payload(call))
        }
        /// `now_tick` and `current_epoch` must come from the authoritative host, never request fields.
        /// Transport credentials are queried on the actual connected socket on every call.
        pub fn evaluate(
            &mut self,
            stream: &UnixStream,
            call: &SignedCall,
            now_tick: u64,
            current_epoch: u64,
        ) -> Result<AuthenticatedDecision, AcsBridgeError> {
            let result = self.evaluate_inner(stream, call, now_tick, current_epoch);
            if result.is_err() {
                self.guard.state_word = POISONED;
            }
            result
        }
        fn evaluate_inner(
            &mut self,
            stream: &UnixStream,
            call: &SignedCall,
            now_tick: u64,
            current_epoch: u64,
        ) -> Result<AuthenticatedDecision, AcsBridgeError> {
            if self.guard.state_word == POISONED {
                return Err(AcsBridgeError::FailOpenProhibited {
                    poison_word: POISONED,
                });
            }
            if peer_identity(stream)? != (self.peer_uid, self.peer_pid) {
                return Err(AcsBridgeError::TransportViolation(
                    "peer does not match root grant".into(),
                ));
            }
            let r = &call.request;
            if r.acs_version != ACS_PROTOCOL_VERSION {
                return Err(AcsBridgeError::UnsupportedProtocolVersion(
                    r.acs_version.clone(),
                ));
            }
            if now_tick < self.guard.system_logical_tick
                || now_tick > self.grant_expiry
                || now_tick > call.expires_at_tick
                || call.expires_at_tick > self.grant_expiry
                || current_epoch != self.guard.authority.active_epoch
                || call.epoch != self.guard.authority.active_epoch
                || r.client_logical_tick > call.expires_at_tick
                || r.client_logical_tick.abs_diff(now_tick) > self.guard.max_clock_skew_ticks
            {
                return Err(AcsBridgeError::InvalidRequest(
                    "epoch, expiry or logical clock mismatch".into(),
                ));
            }
            self.delegated
                .verify(&self.signing_bytes(call), &r.signature)?;
            let (kind, reversibility) =
                BabylonAcsGuard::classify_tool_effect(&r.tool_name, &r.arguments);
            // URI scope must respect a path boundary and reject encoded/ambiguous traversal.
            let scope = self.guard.capability.target_resource.trim_end_matches('/');
            let scoped = r.target_uri == scope
                || r.target_uri
                    .strip_prefix(scope)
                    .is_some_and(|rest| rest.starts_with('/'));
            if !scoped
                || r.target_uri.contains('%')
                || r.target_uri.contains('\\')
                || r.target_uri
                    .split('/')
                    .any(|part| part == ".." || part == ".")
                || !self.guard.capability.allowed_effects.contains(&kind)
            {
                return Err(AcsBridgeError::InvalidRequest(
                    "effect outside granted scope".into(),
                ));
            }
            // The only executable policy supported here is acs_scoped_read_v1/version 1:
            // a read takes exactly one URI argument, equal to the scoped signed destination.
            // Structured/opaque tool argument blobs need an independently validated adapter.
            if kind == EffectKind::FsRead && r.arguments != r.target_uri {
                return Err(AcsBridgeError::InvalidRequest(
                    "read argument must equal scoped target URI".into(),
                ));
            }
            // Cryptographic software authentication is not biometric authorization for mutations.
            let outcome = if kind == EffectKind::FsRead {
                DecisionOutcome::Allow
            } else {
                let _ = reversibility;
                DecisionOutcome::RequireApproval
            };
            self.nonces.consume(&r.nonce)?;
            self.guard.system_logical_tick = now_tick;
            Ok(AuthenticatedDecision {
                request_id: r.request_id,
                nonce: r.nonce,
                outcome,
                authenticated_payload: self.payload(call),
            })
        }
    }

    impl NemesisAutopsyReport {
        /// Deterministic CBOR covering every report field except the signature itself.
        pub fn canonical_payload(&self) -> Vec<u8> {
            let outcome = match &self.observed_outcome {
                Vop1OutcomeState::Rejected { reason } => array(vec![uint(0), text(reason)]),
                Vop1OutcomeState::Unknown {
                    nonce,
                    expected_post_digest,
                } => array(vec![uint(1), bytes(nonce), bytes(expected_post_digest)]),
                Vop1OutcomeState::VerifiedSuccess {
                    nonce,
                    pre_state_digest,
                    observed_post_digest,
                    evidence_receipt_digest,
                } => array(vec![
                    uint(2),
                    bytes(nonce),
                    bytes(pre_state_digest),
                    bytes(observed_post_digest),
                    bytes(evidence_receipt_digest),
                ]),
            };
            array(vec![
                text("BABYLON60_AUTOPSY_V2"),
                bytes(&self.incident_id),
                bytes(&self.principal_identity),
                bytes(&self.requested_effect_id),
                text(&self.policy_version),
                uint(self.first_divergence.step_index),
                bytes(&self.first_divergence.expected_digest),
                bytes(&self.first_divergence.observed_digest),
                text(&self.first_divergence.description),
                bytes(&self.dispatch_evidence_digest),
                outcome,
                array(
                    self.reproduction_steps
                        .iter()
                        .map(|step| text(step))
                        .collect(),
                ),
            ])
        }
        /// Send these bytes to the external signing provider; no private key is created here.
        pub fn attestation_signing_bytes(&self, pinned: &VerificationKey) -> Vec<u8> {
            signing_bytes(pinned, &self.canonical_payload())
        }
        /// Verify every field against a key supplied by trusted provisioning, not the report.
        pub fn verify_with_pinned_key(
            &self,
            pinned: &VerificationKey,
        ) -> Result<(), AcsBridgeError> {
            pinned.verify(
                &self.attestation_signing_bytes(pinned),
                &self.cryptographic_attestation,
            )
        }
        /// Verify and export a tagged COSE_Sign1 forensic report.
        pub fn cose_attestation(
            &self,
            pinned: &VerificationKey,
        ) -> Result<Vec<u8>, AcsBridgeError> {
            self.verify_with_pinned_key(pinned)?;
            Ok(cose_sign1(
                pinned,
                &self.canonical_payload(),
                &self.cryptographic_attestation,
            ))
        }
    }
}
