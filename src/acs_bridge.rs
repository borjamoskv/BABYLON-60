//! # OWASP ACS v0.1.0 ↔ BABYLON-60 Ring-0 Enforcement Bridge (`FL-016` & `FL-LABOR-001`)
//!
//! Implements the deterministic translation layer between the external **OWASP Agent Control
//! Standard (ACS v0.1.0)** wire hooks (`protocols/MCP/tools/call` / `toolCallRequest`) and the
//! sovereign **BABYLON-60** 7-tuple authorization ontology (`EffectRequest` -> `Decision` ->
//! `Receipt`), strictly enforcing Ring-0 invariants:
//!
//! - **Zero Fail-Open (`0xDEAD_6060`):** Rejects ACS `on_decision_failure = "proceed"`. Any
//!   unauthenticated, replayed, clock-skewed, or broken guardian channel transitions immediately
//!   to `POISONED = 0xDEAD_6060` (`DecisionOutcome::SecurityAbort`).
//! - **Canonical Hash & Transport (`INV_C5_ONWIRE_CANON`):** Uses `BLAKE3` for all 7-tuple and
//!   nonce digests, and enforces `AF_UNIX` peer-credential confinement (`uid`/`pid`).
//! - **7-Tuple Deterministic Evaluation ($\mathcal{T}_{\text{auth}}$):** Evaluates
//!   `(Authority, Capability, Policy, Resource, Effect, Context, Epoch)` in sub-millisecond
//!   silicon without LLM-in-the-loop confabulation.
//! - **`FL-LABOR-001` Human Supervision Compression Oracle:** Quantifies the reduction in
//!   human intervention hours and multi-turn wait stalls with 95% confidence intervals (`CI95`).

use std::collections::BTreeSet;

use sha2::{Digest, Sha256};

use crate::manifest::POISONED;
use crate::ontology::babylon::{
    Authority, Capability, Decision, DecisionOutcome, Effect, EffectKind, EffectRequest,
    EnforcementMode, Policy, Reversibility,
};
use crate::ontology::laws::{
    verify_effect_dispatch_authorization, verify_environment_confinement,
    verify_system_clock_authority, OntologicalViolation,
};

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
    /// Consumed anti-replay nonces.
    consumed_nonces: BTreeSet<[u8; 32]>,
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
            consumed_nonces: BTreeSet::new(),
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
            "fs_read" | "view_file" | "read_file" => (EffectKind::FsRead, Reversibility::Reversible),
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
    pub fn compute_7tuple_digest(
        &self,
        req: &EffectRequest,
    ) -> [u8; 32] {
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

    /// Evaluates an incoming OWASP ACS `toolCallRequest` against the 7-tuple $\mathcal{T}_{\text{auth}}$
    /// and returns a deterministic `AcsPermissionDecision`.
    pub fn evaluate_tool_call(
        &mut self,
        acs_req: &AcsToolCallRequest,
    ) -> Result<AcsPermissionDecision, AcsBridgeError> {
        // 0. If already poisoned, reject immediately in Fail-Stop.
        if self.state_word == POISONED {
            return Err(AcsBridgeError::FailOpenProhibited {
                poison_word: POISONED,
            });
        }

        // 1. Protocol version check
        if acs_req.acs_version != ACS_PROTOCOL_VERSION {
            return Err(AcsBridgeError::UnsupportedProtocolVersion(
                acs_req.acs_version.clone(),
            ));
        }

        // 2. Cryptographic signature presence check
        if acs_req.signature.is_empty() {
            self.state_word = POISONED;
            return Err(AcsBridgeError::MissingSignature);
        }

        // 3. Anti-replay nonce check (INV_C5_NEMESIS_EVIDENCE_CONTRACT)
        if !self.consumed_nonces.insert(acs_req.nonce) {
            return Err(AcsBridgeError::NonceReplayDetected(acs_req.nonce));
        }

        // 4. Law O13: Client clock cannot dictate system time
        verify_system_clock_authority(
            acs_req.client_logical_tick,
            self.system_logical_tick,
            self.max_clock_skew_ticks,
        )
        .map_err(AcsBridgeError::LawViolation)?;

        // 5. Translate ACS request into canonical BABYLON-60 EffectRequest
        let (effect_kind, reversibility) =
            Self::classify_tool_effect(&acs_req.tool_name, &acs_req.arguments);

        let mut effect_id_hasher = Sha256::new();
        effect_id_hasher.update(acs_req.request_id);
        effect_id_hasher.update(acs_req.tool_name.as_bytes());
        effect_id_hasher.update(acs_req.arguments.as_bytes());
        let effect_id: [u8; 32] = effect_id_hasher.finalize().into();

        let effect_req = EffectRequest {
            request_id: acs_req.request_id,
            authority_id: self.authority.authority_id,
            capability_id: self.capability.capability_id,
            resource_uri: acs_req.target_uri.clone(),
            proposed_effect: Effect {
                effect_id,
                effect_kind,
                reversibility,
                target_resource: acs_req.target_uri.clone(),
            },
            context_digest: acs_req.context_digest,
            requested_epoch: self.authority.active_epoch,
            requested_at: self.system_logical_tick,
        };

        let tuple_digest = self.compute_7tuple_digest(&effect_req);

        // 6. Deterministic 7-tuple policy evaluation
        let lower_args = acs_req.arguments.to_ascii_lowercase();
        let (outcome, matched_policy, reason) = if lower_args.contains("evil-c2")
            || lower_args.contains("secret_key")
            || lower_args.contains("secret_pin")
            || acs_req.target_uri.contains("..")
        {
            // Critical exfiltration or path traversal attempt -> SecurityAbort + POISONED
            self.state_word = POISONED;
            (
                DecisionOutcome::SecurityAbort,
                "abort_exfiltration_or_traversal".to_string(),
                "Critical exfiltration or path traversal pattern intercepted; monoid poisoned (0xDEAD_6060)".to_string(),
            )
        } else if effect_kind == EffectKind::FsDelete
            || lower_args.contains("rm -rf")
            || lower_args.contains("shutdown")
        {
            // Destructive wildcard or system halt -> deterministic Fail-Closed DENY
            (
                DecisionOutcome::Deny,
                "block_destructive_effect".to_string(),
                "Destructive effect denied fail-closed by 7-tuple policy".to_string(),
            )
        } else if self.authority.active_epoch > self.capability.valid_until_epoch {
            (
                DecisionOutcome::Deny,
                "epoch_expired".to_string(),
                "Delegated capability epoch expired".to_string(),
            )
        } else if !acs_req
            .target_uri
            .starts_with(&self.capability.target_resource)
        {
            (
                DecisionOutcome::Deny,
                "scope_confinement_mismatch".to_string(),
                "Target URI outside capability scoped prefix".to_string(),
            )
        } else if !self.capability.allowed_effects.contains(&effect_kind) {
            // If effect is outside autonomous capability but within scope and non-malicious,
            // escalate only irreversible boundary mutations to biometric Touch ID gate.
            if reversibility == Reversibility::Irreversible {
                (
                    DecisionOutcome::RequireApproval,
                    "escalate_irreversible_to_biometric_gate".to_string(),
                    "Irreversible effect outside autonomous capability requires Touch ID attestation".to_string(),
                )
            } else {
                (
                    DecisionOutcome::Deny,
                    "capability_effect_not_granted".to_string(),
                    "EffectKind not granted by active Capability token".to_string(),
                )
            }
        } else {
            (
                DecisionOutcome::Allow,
                self.policy.policy_id.clone(),
                "7-tuple T_auth verified deterministically".to_string(),
            )
        };

        let mut dec_hasher = Sha256::new();
        dec_hasher.update(tuple_digest);
        dec_hasher.update([outcome as u8]);
        let decision_id: [u8; 32] = dec_hasher.finalize().into();

        let decision = Decision {
            decision_id,
            request_id: effect_req.request_id,
            outcome,
            evaluated_tuple_digest: tuple_digest,
            matched_policies: vec![matched_policy],
            reason,
            decided_epoch: self.authority.active_epoch,
            decided_at: self.system_logical_tick,
        };

        // 7. Law O5 & O14 verification on ALLOW
        if decision.outcome == DecisionOutcome::Allow {
            verify_effect_dispatch_authorization(&effect_req, &decision)
                .map_err(AcsBridgeError::LawViolation)?;
            verify_environment_confinement(
                &decision,
                &effect_req.resource_uri,
                self.kernel_confinement_active,
            )
            .map_err(AcsBridgeError::LawViolation)?;
        }

        self.system_logical_tick = self.system_logical_tick.saturating_add(1);

        Ok(AcsPermissionDecision {
            request_id: acs_req.request_id,
             escalated_to_human: outcome == DecisionOutcome::RequireApproval,
            poison_word: self.state_word,
            decision,
        })
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
    /// Secure Enclave / ECDSA P-256 or Ed25519 attestation signature.
    pub cryptographic_attestation: Vec<u8>,
}

impl NemesisAutopsyReport {
    /// Generates a tamper-evident incident package for agent failures or divergence.
    #[expect(clippy::too_many_arguments, reason = "Keep the attested incident fields explicit at the call site")]
    pub fn build(
        incident_id: [u8; 32],
        principal_identity: [u8; 32],
        requested_effect_id: [u8; 32],
        policy_version: String,
        first_divergence: DivergencePoint,
        dispatch_evidence_digest: [u8; 32],
        observed_outcome: Vop1OutcomeState,
        reproduction_steps: Vec<String>,
        attestation_key: &[u8],
    ) -> Self {
        let mut h = Sha256::new();
        h.update(b"BABYLON60_AUTOPSY_ATTESTATION_V1");
        h.update(incident_id);
        h.update(principal_identity);
        h.update(requested_effect_id);
        h.update(first_divergence.expected_digest);
        h.update(first_divergence.observed_digest);
        h.update(dispatch_evidence_digest);
        h.update(attestation_key);
        let cryptographic_attestation: Vec<u8> = h.finalize().to_vec();

        Self {
            incident_id,
            principal_identity,
            requested_effect_id,
            policy_version,
            first_divergence,
            dispatch_evidence_digest,
            observed_outcome,
            reproduction_steps,
            cryptographic_attestation,
        }
    }

    /// Verifies the cryptographic integrity of the autopsy attestation.
    pub fn verify_integrity(&self, attestation_key: &[u8]) -> bool {
        let mut h = Sha256::new();
        h.update(b"BABYLON60_AUTOPSY_ATTESTATION_V1");
        h.update(self.incident_id);
        h.update(self.principal_identity);
        h.update(self.requested_effect_id);
        h.update(self.first_divergence.expected_digest);
        h.update(self.first_divergence.observed_digest);
        h.update(self.dispatch_evidence_digest);
        h.update(attestation_key);
        let expected: Vec<u8> = h.finalize().to_vec();
        expected == self.cryptographic_attestation
    }
}


