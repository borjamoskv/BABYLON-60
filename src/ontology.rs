//! # BABYLON-60 — Canonical Frozen Ontology v1.0.0
//!
//! Formal specification of core entities, relationships, and invariants across
//! the three orthogonal domains:
//! - **CORTEX (Remember):** SourceRecord, MemoryEvent, IdeaThread, Inference, ProposalContext
//! - **BABYLON (Control):** Authority, Capability, Policy, Resource, EffectRequest, Decision, Effect, EffectOutcome, Receipt
//! - **NEMESIS (Verify):** Assertion, FaultModel, Test, Evidence, Attestation
//!
//! ## The 14 Ontological Laws (O1 - O14)
//! - **O1:** `SOURCE ≠ INFERENCE`
//! - **O2:** `INFERENCE ≠ AUTHORITY`
//! - **O3:** `AUTHORITY ≠ CAPABILITY`
//! - **O4:** `REQUEST ≠ DECISION`
//! - **O5:** `DECISION ≠ EFFECT`
//! - **O6:** `EFFECT ≠ OBSERVED OUTCOME`
//! - **O7:** `RECEIPT ≠ TRUTH`
//! - **O8:** `EVIDENCE ≠ ASSERTION`
//! - **O9:** `ATTESTATION ≠ TRUTH`
//! - **O10:** `UI ≠ AUTHORITY`
//! - **O11:** `MACHINE INFERENCE ≠ PREDICTION ERROR`
//! - **O12:** `TRACEABILITY ≠ AUTHORIZATION`
//! - **O13:** `CLIENT CLOCK ≠ SYSTEM TIME`
//! - **O14:** `INTERFACE AUTHORIZATION ≠ ENVIRONMENT CONFINEMENT`
//!
//! Transversal Invariant:
//! `No stochastic interpretation may create authority by itself`

// ---------------------------------------------------------------------------
// DOMAIN 1: CORTEX (Remember)
// ---------------------------------------------------------------------------

pub mod cortex {
    //! CORTEX Domain: ingestion, memory events, thematic idea threads, and inferences.

    /// Original audit-grade record or file at ingestion time.
    /// Law O1: SOURCE != INFERENCE.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct SourceRecord {
        /// Canonical URI or locator (e.g. file:///..., note://...).
        pub source_id: String,
        /// Ingesting provider or subsystem.
        pub provider: String,
        /// SHA-256 of raw data at the exact moment of ingestion.
        pub raw_hash: [u8; 32],
        /// UTC timestamp of ingestion.
        pub ingested_at: u64,
        /// Content length in bytes.
        pub content_length: u64,
        /// MIME type if applicable.
        pub mime_type: Option<String>,
    }

    /// Discrete memory event extracted from an auditable SourceRecord.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct MemoryEvent {
        /// Unique event identifier.
        pub event_id: String,
        /// Reference to backing SourceRecord (O1 compliance).
        pub source_ref: String,
        /// Logical or physical timestamp.
        pub timestamp: u64,
        /// Domain event type tag.
        pub event_type: String,
        /// Normalized textual content.
        pub normalized_text: String,
        /// Extracted entities.
        pub entities: Vec<String>,
        /// Hash of the event payload.
        pub raw_hash: [u8; 32],
        /// Extractor version for provenance.
        pub extractor_version: String,
    }

    /// Recurrent conceptual thread tracking an idea over time.
    #[derive(Debug, Clone, PartialEq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct IdeaThread {
        /// Unique thread ID.
        pub idea_id: String,
        /// Core conceptual descriptor.
        pub core_concept: String,
        /// First appearance timestamp.
        pub first_seen: u64,
        /// Last observed timestamp.
        pub last_seen: u64,
        /// Recurrence count.
        pub recurrence_count: u32,
        /// Dormancy period in days.
        pub dormant_days: u32,
        /// Associated MemoryEvent IDs.
        pub events: Vec<String>,
        /// Calculated salience/exergy score.
        pub score: f32,
    }

    /// Model-derived interpretation or proposal.
    /// Law O1: INFERENCE != SOURCE.
    /// Law O2: INFERENCE != AUTHORITY.
    #[derive(Debug, Clone, PartialEq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Inference {
        /// Unique inference identifier.
        pub inference_id: String,
        /// Grounding IdeaThread IDs.
        pub derived_from_threads: Vec<String>,
        /// Inference model identifier (e.g. local or hosted LLM).
        pub model_id: String,
        /// SHA-256 of prompt / grounding context.
        pub prompt_digest: [u8; 32],
        /// Generation timestamp.
        pub generated_at: u64,
        /// Advisory proposal payload (non-binding).
        pub proposal_summary: String,
        /// Model confidence metric [0.0, 1.0].
        pub confidence: f32,
    }

    /// Contextual proposal crossing the trust boundary towards BABYLON.
    /// CORTEX produces ProposalContext; it cannot self-authorize.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct ProposalContext {
        /// Unique proposal reference.
        pub proposal_id: String,
        /// Backing Inference ID.
        pub inference_ref: String,
        /// Suggested action description for human/policy consideration.
        pub suggested_action: String,
        /// Epistemic justification.
        pub justification: String,
        /// Preliminary risk classification.
        pub evaluated_risk: String,
    }
}

// ---------------------------------------------------------------------------
// DOMAIN 2: BABYLON (Control)
// ---------------------------------------------------------------------------

pub mod babylon {
    //! BABYLON Domain: authority, capability, policy, effect mediation, and receipts.

    /// Sovereign identity, hardware enclave, or epoch governor.
    /// Law O3: AUTHORITY != CAPABILITY.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Authority {
        /// Unique authority identifier.
        pub authority_id: [u8; 32],
        /// Hardware or role classification.
        pub principal_type: PrincipalType,
        /// Public key in binary representation.
        pub public_key: [u8; 32],
        /// Current authority epoch.
        pub active_epoch: u64,
    }

    /// Type of governing authority principal.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum PrincipalType {
        /// Biometric human operator (Touch ID / Ring-(-1)).
        BiometricOperator,
        /// Apple Silicon Secure Enclave / TPM.
        SecureEnclave,
        /// Attested microkernel runtime (Ring-0).
        AttestedKernel,
        /// Cryptographically delegated sub-role.
        DelegatedRole,
    }

    /// Bounded authorization token granting permissions.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Capability {
        /// Unique capability token ID.
        pub capability_id: [u8; 32],
        /// Issuing authority ID.
        pub issuer_authority_id: [u8; 32],
        /// Scoped resource prefix or identifier.
        pub target_resource: String,
        /// Allowed effect kinds under this token.
        pub allowed_effects: Vec<EffectKind>,
        /// Expiration epoch.
        pub valid_until_epoch: u64,
        /// Cryptographic signature from issuing Authority.
        pub signature: Vec<u8>,
    }

    /// Deterministic gatekeeping rule.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Policy {
        /// Unique policy identifier.
        pub policy_id: String,
        /// Policy semantic version.
        pub version: String,
        /// Deterministic rule predicate digest or code.
        pub predicate_digest: [u8; 32],
        /// Enforcement behavior.
        pub enforcement_mode: EnforcementMode,
    }

    /// Policy enforcement stance.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum EnforcementMode {
        /// Immediate veto upon any invariant failure.
        FailClosed,
        /// Non-blocking telemetry mode for shadow testing.
        AuditOnly,
    }

    /// Target physical or logical entity subject to effect mediation.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Resource {
        /// Resource URI (e.g. file:///var/data/log, net://socket).
        pub resource_uri: String,
        /// Classification of the underlying substrate.
        pub resource_type: ResourceType,
        /// VFS or system locator identity.
        pub locator_identity: Option<[u8; 32]>,
    }

    /// Substrate type of the resource.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum ResourceType {
        /// Regular filesystem file.
        VfsFile,
        /// Filesystem directory.
        VfsDirectory,
        /// Network socket or endpoint.
        NetworkSocket,
        /// OS execution process.
        Process,
        /// Cryptographic key slot.
        CryptoKey,
        /// Append-only ledger record.
        LedgerEntry,
    }

    /// Externally observable state transition mediated by BABYLON.
    /// Irreversibility is an orthogonal property, not the definition.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Effect {
        /// Unique effect identifier.
        pub effect_id: [u8; 32],
        /// Action kind in the substrate.
        pub effect_kind: EffectKind,
        /// Reversibility property.
        pub reversibility: Reversibility,
        /// Target resource URI.
        pub target_resource: String,
    }

    /// Action kind of an effect.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum EffectKind {
        /// Filesystem read.
        FsRead,
        /// Filesystem mutation (write/truncate).
        FsMutate,
        /// Filesystem deletion/unlink.
        FsDelete,
        /// Permission modification.
        FsChmod,
        /// Atomic dentry rename.
        FsRename,
        /// Outbound network transmission.
        NetTransmit,
        /// Process spawn.
        ProcSpawn,
        /// Process termination.
        ProcTerminate,
        /// Cryptographic key erasure.
        KeyDestroy,
        /// Immutable ledger append.
        LedgerAppend,
    }

    /// Reversibility property of an effect.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum Reversibility {
        /// Reversible transition (e.g. temporary write with undo journal).
        Reversible,
        /// Compensatable transition (e.g. SAGA / reverse delta).
        Compensatable,
        /// Physically or cryptographically irreversible (e.g. secure unlink, PoW commit).
        Irreversible,
    }

    /// Formal request seeking execution of an Effect.
    /// Law O4: REQUEST != DECISION.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct EffectRequest {
        /// Unique request identifier.
        pub request_id: [u8; 32],
        /// Invocating authority ID.
        pub authority_id: [u8; 32],
        /// Delegated capability token ID.
        pub capability_id: [u8; 32],
        /// Target resource URI.
        pub resource_uri: String,
        /// Proposed effect.
        pub proposed_effect: Effect,
        /// Hash of execution context and telemetry.
        pub context_digest: [u8; 32],
        /// Current epoch during request creation.
        pub requested_epoch: u64,
        /// UTC timestamp.
        pub requested_at: u64,
    }

    /// Authorization evaluation result for the 7-tuple:
    /// (Authority, Capability, Policy, Resource, Effect, Context, Epoch).
    /// Law O5: DECISION != EFFECT.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Decision {
        /// Unique decision identifier.
        pub decision_id: [u8; 32],
        /// Backing EffectRequest ID.
        pub request_id: [u8; 32],
        /// Decision verdict.
        pub outcome: DecisionOutcome,
        /// Hash of the evaluated 7-tuple.
        pub evaluated_tuple_digest: [u8; 32],
        /// IDs of policies evaluated during decision.
        pub matched_policies: Vec<String>,
        /// Deterministic explanation.
        pub reason: String,
        /// Epoch at decision time.
        pub decided_epoch: u64,
        /// Timestamp.
        pub decided_at: u64,
    }

    /// Evaluation verdict for an EffectRequest.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum DecisionOutcome {
        /// Effect is authorized to proceed to dispatch.
        Allow,
        /// Effect is denied deterministically by policy.
        Deny,
        /// Effect requires explicit interactive biometric gate approval.
        RequireApproval,
        /// Critical security violation: halt and poison transaction.
        SecurityAbort,
    }

    /// Physically observed outcome following effect dispatch.
    /// Law O6: EFFECT != OBSERVED OUTCOME.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct EffectOutcome {
        /// Unique outcome identifier.
        pub outcome_id: [u8; 32],
        /// Backing Effect ID.
        pub effect_id: [u8; 32],
        /// Substrate execution status.
        pub status: OutcomeStatus,
        /// Pre-execution state hash.
        pub pre_state_digest: [u8; 32],
        /// Post-execution state hash.
        pub post_state_digest: [u8; 32],
        /// Divergence flag: true if actual post-state diverges from intended.
        pub divergence_detected: bool,
        /// Physical observation timestamp.
        pub observed_at: u64,
    }

    /// Physical execution status of an effect.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum OutcomeStatus {
        /// Effect completed with full verified post-state.
        Success,
        /// Driver returned error or non-zero status.
        Failure,
        /// Partial write or incomplete state transition.
        Partial,
        /// Execution timed out.
        TimedOut,
        /// Intercepted or quarantined by safety kernel.
        Intercepted,
    }

    /// Cryptographic record of evidence about an EffectOutcome across lifecycle stages.
    /// Law O7: RECEIPT != TRUTH.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Receipt {
        /// Unique receipt identifier.
        pub receipt_id: [u8; 32],
        /// Backing Effect ID.
        pub effect_id: [u8; 32],
        /// Backing EffectOutcome ID (if past Dispatch stage).
        pub outcome_id: Option<[u8; 32]>,
        /// Lifecycle stage at which this receipt was sealed.
        pub stage: ReceiptStage,
        /// Hash of telemetry, outcome, and context evidence.
        pub evidence_digest: [u8; 32],
        /// COSE_Sign1 or cryptographic signature bytes.
        pub signature: Vec<u8>,
        /// Key identifier of the signer.
        pub signer_kid: String,
        /// Anchored epoch or external block height (TSA / OP_RETURN).
        pub anchored_epoch: Option<u64>,
        /// Issuance timestamp.
        pub issued_at: u64,
    }

    /// Discrete causal lifecycle stage of an effect.
    #[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum ReceiptStage {
        /// 1. Effect formal request registered in broker.
        Requested,
        /// 2. Evaluation tuple authorized with ALLOW verdict.
        Authorized,
        /// 3. Sent to substrate execution driver.
        Dispatched,
        /// 4. Substrate state change physically measured and verified.
        Observed,
        /// 5. Recorded in append-only WORM ledger / cryptographic receipt.
        Committed,
    }

    /// 8-phase execution state of an Effect within the sovereign broker.
    /// Law O4: REQUEST != DECISION.
    /// Law O5: DECISION != EFFECT.
    /// Law O6: EFFECT != OBSERVED OUTCOME.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum EffectState {
        /// 1. Effect requested by caller or untrusted cognitive component.
        Requested,
        /// 2. Syntactic, schema, and precondition validation succeeded.
        Validated,
        /// 3. Decision 7-tuple evaluated with ALLOW verdict.
        Authorized,
        /// 4. Admitted by sovereign scheduler / execution queue.
        Admitted,
        /// 5. Durably recorded in write-ahead log / persistent storage with sync.
        Durable,
        /// 6. Currently dispatching / executing against substrate via pinned handle.
        Executing,
        /// 7. Substrate syscall completed successfully.
        Executed,
        /// 8. Post-state physically observed and cryptographically verified.
        Verified,
        /// Terminal rejection before or during authorization/admission.
        Rejected(RejectReason),
        /// Terminal failure during execution, substrate fault, or crash recovery.
        Failed(FailureReason),
    }

    /// Deterministic reasons for effect request rejection.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum RejectReason {
        /// Policy evaluated to DENY.
        PolicyDenied(String),
        /// Precondition hash mismatch against current substrate state.
        PreconditionMismatch,
        /// Stale authority epoch or revoked capability.
        StaleAuthority {
            /// Expected authority epoch.
            expected_epoch: u64,
            /// Actual authority epoch.
            actual_epoch: u64,
        },
        /// Target resource does not exist or invalid URI.
        ResourceNotFound(String),
        /// Replay attack: cryptographic nonce already consumed.
        NonceAlreadyConsumed([u8; 32]),
        /// Unauthorized effect kind for this capability token.
        UnauthorizedEffectKind,
        /// Quarantined or unsafe path traversal / symlink escape attempt.
        SymlinkEscapeAttempt,
        /// (FL-007) Admission Control: Liveness capacity exceeded (bounded time contract violation).
        CapacityExceeded {
            /// Maximum allowable depth or latency bounded capacity.
            capacity_limit: usize,
            /// Attempted queue depth or estimated latency weight.
            attempted_depth: usize,
        },
        /// (FL-008) Confused Deputy Attempt: The causal parent of the capability does not match the requester.
        ConfusedDeputyAttempt,
        /// (FL-008) Server is disabled or unconfigured
        ServerDisabled,
        /// (FL-008) Tool identity / hash mismatch or substitution attempt
        ToolIdentityMismatch,
        /// (FL-008) Attempt to escalate capability or effect kind beyond grant
        CapabilityEscalation,
        /// (FL-008) Capability token is expired, revoked, or stale at t_commit
        StaleCapability,
        /// (FL-008) Configuration, arguments, or policy drifted between validation and commit
        ConfigurationDrift,
    }

    /// Failure reasons during effect execution or verification.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum FailureReason {
        /// Substrate I/O syscall error.
        IoError(String),
        /// Physical post-state hash diverged from expected post-state.
        DivergenceDetected {
            /// Expected SHA-256 digest.
            expected_hash: [u8; 32],
            /// Actual observed digest.
            actual_hash: [u8; 32],
        },
        /// Execution timed out exceeding bounded deadline.
        ExecutionTimeout {
            /// Elapsed time in milliseconds.
            elapsed_ms: u64,
            /// Time limit in milliseconds.
            limit_ms: u64,
        },
        /// Process crashed before completion; recovered to fail-stop.
        CrashBeforeCompletion,
        /// Quarantined decoy substitution detected (TOCTOU attack).
        SecurityMismatch {
            /// Inode authorized.
            expected_ino: u64,
            /// Inode found in quarantine.
            actual_ino: u64,
        },
        /// Storage / ledger write error.
        LedgerError(String),
    }

    pub use super::ontology_ext::babylon_ext::*;
}

// ---------------------------------------------------------------------------
// DOMAIN 3: NEMESIS (Verify)
// ---------------------------------------------------------------------------

pub mod nemesis {
    //! NEMESIS Domain: Popperian falsification, fault models, test harnesses, and attestations.

    pub use super::ontology_ext::nemesis_ext::*;

    /// Formal security invariant subjected to adversarial testing.
    /// Law O8: EVIDENCE != ASSERTION.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Assertion {
        /// Canonical assertion identifier (e.g. "NEM-I1-EFFECT-AUTHORIZATION").
        pub assertion_id: String,
        /// Human-readable descriptor.
        pub name: String,
        /// Formal mathematical predicate (e.g. in Lean 4 or first-order logic).
        pub formal_predicate: String,
        /// Current empirical status under adversarial challenge.
        pub status: AssertionStatus,
        /// Domain scope.
        pub domain_scope: String,
        /// Timestamp of the latest test challenge run.
        pub last_challenged_at: u64,
    }

    /// Epistemic status of an assertion under falsification testing.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum AssertionStatus {
        /// Stated in specification, no adversarial campaign executed yet.
        Untested,
        /// Subjected to fault models without falsification to date.
        Supported,
        /// Falsified by an empirical counterexample.
        Falsified,
        /// Invalidation due to environment, toolchain, or code drift.
        Stale,
    }

    /// Empirically observed records produced during a Test run.
    #[derive(Debug, Clone, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub struct Evidence {
        /// Unique evidence identifier.
        pub evidence_id: [u8; 32],
        /// Originating test ID.
        pub test_id: String,
        /// Receipts collected during the adversarial campaign.
        pub associated_receipt_ids: Vec<[u8; 32]>,
        /// Result of the falsification challenge.
        pub result: EvidenceResult,
        /// Observation timestamp.
        pub recorded_at: u64,
    }

    /// Outcome of the falsification attempt.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    #[cfg_attr(feature = "cortex-persist", derive(serde::Serialize, serde::Deserialize))]
    pub enum EvidenceResult {
        /// Invariant was broken; assertion is FALSIFIED.
        FalsificationSuccessful,
        /// Invariant held under all perturbations; assertion is SUPPORTED.
        FalsificationFailed,
    }
}

// ---------------------------------------------------------------------------
// THE 10 ONTOLOGICAL LAWS & VALIDATORS
// ---------------------------------------------------------------------------

pub mod laws {
    //! Programmatic enforcement of the 10 Ontological Laws (O1 - O10).

    use crate::ontology::cortex::{Inference, ProposalContext};
    use crate::ontology::babylon::{Decision, DecisionOutcome, EffectRequest, ReceiptStage};
    use crate::ontology::nemesis::{Assertion, AssertionStatus, Evidence, EvidenceResult};

    /// Enumeration of the 10 Canonical Ontological Laws.
    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub enum OntologicalLaw {
        /// O1: SOURCE != INFERENCE
        O1SourceNeqInference,
        /// O2: INFERENCE != AUTHORITY
        O2InferenceNeqAuthority,
        /// O3: AUTHORITY != CAPABILITY
        O3AuthorityNeqCapability,
        /// O4: REQUEST != DECISION
        O4RequestNeqDecision,
        /// O5: DECISION != EFFECT
        O5DecisionNeqEffect,
        /// O6: EFFECT != OBSERVED OUTCOME
        O6EffectNeqObservedOutcome,
        /// O7: RECEIPT != TRUTH
        O7ReceiptNeqTruth,
        /// O8: EVIDENCE ≠ ASSERTION
        O8EvidenceNeqAssertion,
        /// O9: ATTESTATION != TRUTH
        O9AttestationNeqTruth,
        /// O10: UI != AUTHORITY
        O10UiNeqAuthority,
        /// O11: MACHINE INFERENCE != PREDICTION ERROR
        O11MachineInferenceNeqPredictionError,
        /// O12: TRACEABILITY != AUTHORIZATION
        O12TraceabilityNeqAuthorization,
        /// O13: CLIENT CLOCK != SYSTEM TIME
        O13ClientClockNeqSystemTime,
        /// O14: INTERFACE AUTHORIZATION != ENVIRONMENT CONFINEMENT
        O14InterfaceAuthorizationNeqEnvironmentConfinement,
        /// Transversal 1: No stochastic interpretation may create authority by itself.
        TransversalNoStochasticAuthority,
        /// Transversal 2: No mediated effect may commit without an explicit Decision.
        TransversalNoEffectCommitWithoutDecision,
    }

    /// Error emitted when an operation attempts to violate an ontological boundary.
    #[derive(Debug, Clone, PartialEq, Eq)]
    pub enum OntologicalViolation {
        /// Attempted to derive authority directly from an inference (Violates O2).
        InferenceCannotBecomeAuthority {
            /// Identifier of the violating inference.
            inference_id: String,
        },
        /// Attempted to dispatch an effect without an affirmative Decision (Violates O4 / O5).
        EffectWithoutApproval {
            /// Request ID evaluated.
            request_id: [u8; 32],
            /// Actual non-allow decision outcome.
            outcome: DecisionOutcome,
        },
        /// Receipt stage regression or sequence jump (Violates O7 causal order).
        InvalidReceiptStageTransition {
            /// Originating receipt stage.
            from: ReceiptStage,
            /// Invalid target receipt stage.
            to: ReceiptStage,
        },
        /// Assertion marked SUPPORTED without non-empty evidence (Violates O8).
        UnsupportedAssertionClaim {
            /// Identifier of the ungrounded assertion.
            assertion_id: String,
        },
        /// Divergence between effect and observed outcome not flagged (Violates O6).
        UnflaggedOutcomeDivergence {
            /// Identifier of the unflagged outcome.
            outcome_id: [u8; 32],
        },
        /// Attempted to have machine inference self-certify its own prediction error (Violates O11).
        MachineInferenceCannotSelfEvaluate {
            /// Identifier of the violating inference.
            inference_id: String,
        },
        /// Attempted to treat ledger audit traceability as prior authorization (Violates O12).
        TraceabilityWithoutPriorAuthorization {
            /// Receipt ID evaluated.
            receipt_id: [u8; 32],
        },
        /// Client supplied timestamp exceeds acceptable skew against system clock (Violates O13).
        ClientClockSkewExceeded {
            /// Client claimed timestamp.
            client_ts: u64,
            /// Secure system timestamp.
            system_ts: u64,
            /// Max allowable skew in seconds.
            max_skew_secs: u64,
        },
        /// Interface-level authorization lacked kernel-level OS confinement (Violates O14).
        InterfaceAuthorizationLacksConfinement {
            /// Target resource URI.
            resource_uri: String,
        },
    }

    impl core::fmt::Display for OntologicalViolation {
        fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
            match self {
                Self::InferenceCannotBecomeAuthority { inference_id } => {
                    write!(f, "[LAW O2 VIOLATION] Inference '{}' cannot cross trust boundary into Authority", inference_id)
                }
                Self::EffectWithoutApproval { request_id, outcome } => {
                    write!(f, "[LAW O5 VIOLATION] Request {:?} has outcome {:?}; cannot execute Effect", request_id, outcome)
                }
                Self::InvalidReceiptStageTransition { from, to } => {
                    write!(f, "[LAW O7 VIOLATION] Invalid receipt stage transition from {:?} to {:?}", from, to)
                }
                Self::UnsupportedAssertionClaim { assertion_id } => {
                    write!(f, "[LAW O8 VIOLATION] Assertion '{}' cannot be marked SUPPORTED without valid evidence", assertion_id)
                }
                Self::UnflaggedOutcomeDivergence { outcome_id } => {
                    write!(f, "[LAW O6 VIOLATION] Outcome {:?} exhibits divergence but flag is false", outcome_id)
                }
                Self::MachineInferenceCannotSelfEvaluate { inference_id } => {
                    write!(f, "[LAW O11 VIOLATION] Machine inference '{}' cannot evaluate its own prediction error", inference_id)
                }
                Self::TraceabilityWithoutPriorAuthorization { receipt_id } => {
                    write!(f, "[LAW O12 VIOLATION] Receipt {:?} in ledger does not constitute prior authorization", receipt_id)
                }
                Self::ClientClockSkewExceeded { client_ts, system_ts, max_skew_secs } => {
                    write!(f, "[LAW O13 VIOLATION] Client clock skew exceeded: client={}, system={}, max_skew={}s", client_ts, system_ts, max_skew_secs)
                }
                Self::InterfaceAuthorizationLacksConfinement { resource_uri } => {
                    write!(f, "[LAW O14 VIOLATION] Authorization for resource '{}' lacks OS-level environment confinement", resource_uri)
                }
            }
        }
    }

    impl std::error::Error for OntologicalViolation {}

    /// Validates the Trust Boundary: Converts an Inference to an advisory ProposalContext.
    /// Guarantees that CORTEX never directly instantiates an Authority (Law O2).
    pub fn enforce_trust_boundary(
        inference: &Inference,
        suggested_action: String,
        justification: String,
        evaluated_risk: String,
    ) -> ProposalContext {
        ProposalContext {
            proposal_id: format!("prop_{}", inference.inference_id),
            inference_ref: inference.inference_id.clone(),
            suggested_action,
            justification,
            evaluated_risk,
        }
    }

    /// Verifies that an Effect can only be dispatched if the Decision is `Allow` (Law O5).
    pub fn verify_effect_dispatch_authorization(
        request: &EffectRequest,
        decision: &Decision,
    ) -> Result<(), OntologicalViolation> {
        if decision.request_id != request.request_id {
            return Err(OntologicalViolation::EffectWithoutApproval {
                request_id: request.request_id,
                outcome: decision.outcome,
            });
        }
        match decision.outcome {
            DecisionOutcome::Allow => Ok(()),
            other => Err(OntologicalViolation::EffectWithoutApproval {
                request_id: request.request_id,
                outcome: other,
            }),
        }
    }

    /// Verifies causal progression of Receipt lifecycle stages (Law O7).
    pub fn verify_receipt_stage_transition(
        current: ReceiptStage,
        next: ReceiptStage,
    ) -> Result<(), OntologicalViolation> {
        let valid = matches!(
            (current, next),
            (ReceiptStage::Requested, ReceiptStage::Authorized)
                | (ReceiptStage::Authorized, ReceiptStage::Dispatched)
                | (ReceiptStage::Dispatched, ReceiptStage::Observed)
                | (ReceiptStage::Observed, ReceiptStage::Committed)
        );
        if valid {
            Ok(())
        } else {
            Err(OntologicalViolation::InvalidReceiptStageTransition {
                from: current,
                to: next,
            })
        }
    }

    /// Updates AssertionStatus based on Popperian Evidence result (Law O8).
    pub fn update_assertion_from_evidence(
        assertion: &mut Assertion,
        evidence: &Evidence,
    ) {
        assertion.last_challenged_at = evidence.recorded_at;
        match evidence.result {
            EvidenceResult::FalsificationSuccessful => {
                assertion.status = AssertionStatus::Falsified;
            }
            EvidenceResult::FalsificationFailed => {
                // If it was Untested or Supported, it remains Supported
                if assertion.status != AssertionStatus::Falsified {
                    assertion.status = AssertionStatus::Supported;
                }
            }
        }
    }

    /// Verifies that Machine Inference cannot self-certify its prediction error (Law O11).
    /// Stochastic machine inference is open-loop; evaluation belongs strictly to the coupled biological operator or external ground truth.
    pub fn verify_prediction_error_evaluation(
        inference: &Inference,
        is_external_or_human_eval: bool,
    ) -> Result<(), OntologicalViolation> {
        if !is_external_or_human_eval {
            return Err(OntologicalViolation::MachineInferenceCannotSelfEvaluate {
                inference_id: inference.inference_id.clone(),
            });
        }
        Ok(())
    }

    /// Verifies that Traceability in the ledger does not equate to prior authorization (Law O12).
    /// Logging what occurred post-facto is not an authorization decision.
    pub fn verify_traceability_not_authorization(
        receipt: &crate::ontology::babylon::Receipt,
        prior_decision: Option<&Decision>,
    ) -> Result<(), OntologicalViolation> {
        match prior_decision {
            Some(dec) if dec.outcome == DecisionOutcome::Allow => Ok(()),
            _ => Err(OntologicalViolation::TraceabilityWithoutPriorAuthorization {
                receipt_id: receipt.receipt_id,
            }),
        }
    }

    /// Verifies that Client Clock cannot dictate system time or bypass expiration (Law O13).
    /// Untrusted clients cannot supply the clock by which their own authorization validity is judged.
    pub fn verify_system_clock_authority(
        client_timestamp: u64,
        system_timestamp: u64,
        max_skew_secs: u64,
    ) -> Result<(), OntologicalViolation> {
        let skew = client_timestamp.abs_diff(system_timestamp);
        if skew > max_skew_secs {
            return Err(OntologicalViolation::ClientClockSkewExceeded {
                client_ts: client_timestamp,
                system_ts: system_timestamp,
                max_skew_secs,
            });
        }
        Ok(())
    }

    /// Verifies that Interface Authorization is backed by OS/Ring-0 Environment Confinement (Law O14).
    /// App-level authorization does not replace kernel sandbox confinement if direct syscalls remain accessible.
    pub fn verify_environment_confinement(
        decision: &Decision,
        resource_uri: &str,
        kernel_confinement_active: bool,
    ) -> Result<(), OntologicalViolation> {
        if decision.outcome == DecisionOutcome::Allow && !kernel_confinement_active {
            return Err(OntologicalViolation::InterfaceAuthorizationLacksConfinement {
                resource_uri: resource_uri.to_string(),
            });
        }
        Ok(())
    }
}

#[path = "ontology_ext.rs"]
mod ontology_ext;

#[cfg(test)]
#[path = "ontology_tests.rs"]
mod tests;

#[cfg(test)]
mod morphism_tests {
    use crate::executor::ReservationState;
    use crate::ontology::babylon::{EffectState, ReceiptStage};
    use core::convert::TryFrom;

    #[test]
    fn test_reservation_state_receipt_stage_exhaustive_morphism() {
        assert_eq!(
            ReceiptStage::try_from(ReservationState::Reserved),
            Ok(ReceiptStage::Authorized)
        );
        assert_eq!(
            ReceiptStage::try_from(ReservationState::Dispatched),
            Ok(ReceiptStage::Dispatched)
        );
        assert_eq!(
            ReceiptStage::try_from(ReservationState::Executed),
            Ok(ReceiptStage::Committed)
        );
        assert_eq!(
            ReceiptStage::try_from(ReservationState::Failed),
            Err(ReservationState::Failed)
        );
        assert_eq!(
            ReceiptStage::try_from(ReservationState::Unknown),
            Err(ReservationState::Unknown)
        );

        assert_eq!(ReservationState::from(ReceiptStage::Requested), ReservationState::Reserved);
        assert_eq!(ReservationState::from(ReceiptStage::Authorized), ReservationState::Reserved);
        assert_eq!(ReservationState::from(ReceiptStage::Dispatched), ReservationState::Dispatched);
        assert_eq!(ReservationState::from(ReceiptStage::Observed), ReservationState::Executed);
        assert_eq!(ReservationState::from(ReceiptStage::Committed), ReservationState::Executed);

        assert_eq!(ReservationState::Reserved.to_effect_state(None), EffectState::Durable);
        assert_eq!(ReservationState::Dispatched.to_effect_state(None), EffectState::Executing);
        assert_eq!(ReservationState::Executed.to_effect_state(None), EffectState::Executed);
    }
}
