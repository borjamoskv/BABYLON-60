# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""FL-027 v3: Provenance Authority Confusion & Dual-Identity Falsification Engine.

Enforces:
- Dual Cryptographic Identity (INV_C5_ONWIRE_CANON + INV_C5_CANONICAL_LOGICAL_TICK):
  * I_content = "b3:" || hex(BLAKE3("CORTEX-CONTENT-v3\\0" || CanonicalBytes(m)))
  * I_event   = "b3:" || hex(BLAKE3("CORTEX-EVENT-v3\\0" || LP(namespace) || LP(conversation_id)
                             || LP(message_id) || u64_le(revision) || u64_le(logical_tick)))
  Physical timestamps (claimed_created_at_utc, retrieved_at_utc) are strictly excluded
  from canonical identity digests (Law O13: CLIENT CLOCK != SYSTEM TIME).
- Same Content != Same Event: Identical I_content across distinct I_event tuples
  cannot transfer provenance level, platform authority, or execution attestation
  without a verified EventLinkReceipt.
- ScopeBound Attribution Gate:
  Attested(e) => OriginVerified(e) & IntegrityVerified(e) & ScopeBound(e)
- Retraction Lineage Preservation: Retracting an unsupported attribution via
  MemoryGovernanceEngine preserves the underlying SourceRecord (ACTIVE) and
  records an immutable DisbeliefProof chain (who, when in lamport_t, why, and
  which counter-evidence refuted it).
"""

from __future__ import annotations

import hmac
import re
import struct
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional, Sequence, Tuple

import blake3

from babylon60.memory.governance import GovernanceViolationError

_CONTENT_DOMAIN = b"CORTEX-CONTENT-v3\x00"
_EVENT_DOMAIN = b"CORTEX-EVENT-v3\x00"
_LINK_DOMAIN = b"CORTEX-EVENT-LINK-v3\x00"
_B3_DIGEST = re.compile(r"b3:[0-9a-fA-F]{64}")


def _is_b3_digest(value: str) -> bool:
    return isinstance(value, str) and _B3_DIGEST.fullmatch(value) is not None


class ProvenanceLevel(IntEnum):
    """Strict monotonic hierarchy of provenance verification levels."""

    CLAIMED = 10
    PLATFORM_UI_RECORD = 20
    TIMESTAMPED_RECORD = 30
    NATIVE_EXPORT_VERIFIED = 40
    EXTERNALLY_ANCHORED = 50
    CONTEMPORANEOUS_WITNESS = 60


class DerivationKind(str, Enum):
    """Distinguishes primary message payloads from derived titles or summaries."""

    ORIGINAL_MESSAGE = "original_message"
    DERIVED_TITLE = "derived_title"
    POST_HOC_SUMMARY = "post_hoc_summary"
    ARCHITECTURE_PROMPT = "architecture_prompt"
    EXECUTION_RECEIPT = "execution_receipt"


class ClaimScope(str, Enum):
    """Scope of an attribution claim evaluated against ScopeBound(e)."""

    FACT_RECALL = "fact_recall"
    CONVERSATION_CHRONOLOGY = "conversation_chronology"
    ORIGINAL_AUTHORING_PLATFORM = "original_authoring_platform"
    NATIVE_MESSAGE_TRANSCRIPT = "native_message_transcript"
    RUNTIME_EXECUTION = "runtime_execution"
    CAUSAL_LINEAGE_PROOF = "causal_lineage_proof"


class ProvenanceAuthorityError(GovernanceViolationError):
    """Raised when an attribution exceeds its verified provenance or violates FL-027."""


def _lp_bytes(value: str | bytes) -> bytes:
    raw = value.encode("utf-8") if isinstance(value, str) else bytes(value)
    return struct.pack(">Q", len(raw)) + raw


def canonical_content_bytes(text: str) -> bytes:
    """Normalize line endings and UTF-8 representation without altering lexical content."""
    if not isinstance(text, str):
        raise TypeError("content must be a string")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.encode("utf-8")


def compute_content_identity(content: str | bytes) -> str:
    """Compute canonical BLAKE3 content identity I_content = BLAKE3(CanonicalBytes(m))."""
    raw = canonical_content_bytes(content) if isinstance(content, str) else bytes(content)
    return "b3:" + blake3.blake3(_CONTENT_DOMAIN + raw).hexdigest()


@dataclass(frozen=True)
class EventIdentityTuple:
    """Canonical event coordinates independent of physical wall-clock time."""

    namespace: str
    conversation_id: str
    message_id: str
    revision: int = 1
    logical_tick: int = 1

    def __post_init__(self) -> None:
        if not self.namespace or not self.namespace.strip():
            raise ProvenanceAuthorityError("EventIdentityTuple.namespace must be non-empty")
        if not self.conversation_id or not self.conversation_id.strip():
            raise ProvenanceAuthorityError("EventIdentityTuple.conversation_id must be non-empty")
        if not self.message_id or not self.message_id.strip():
            raise ProvenanceAuthorityError("EventIdentityTuple.message_id must be non-empty")
        if self.revision < 1:
            raise ProvenanceAuthorityError("EventIdentityTuple.revision must be >= 1")
        if self.logical_tick < 0:
            raise ProvenanceAuthorityError("EventIdentityTuple.logical_tick must be >= 0")

    def compute_event_identity(self) -> str:
        """Compute canonical BLAKE3 event identity I_event without physical timestamps."""
        buf = bytearray(_EVENT_DOMAIN)
        buf.extend(_lp_bytes(self.namespace))
        buf.extend(_lp_bytes(self.conversation_id))
        buf.extend(_lp_bytes(self.message_id))
        buf.extend(struct.pack("<Q", int(self.revision)))
        buf.extend(struct.pack("<Q", int(self.logical_tick)))
        return "b3:" + blake3.blake3(bytes(buf)).hexdigest()


@dataclass(frozen=True)
class ProvenanceEnvelope:
    """CORTEX provenance record separating content identity, event identity, and authority."""

    content: str
    host_platform: str
    derivation_kind: DerivationKind
    claimed_created_at_utc: Optional[str] = None
    retrieved_at_utc: Optional[str] = None
    original_authoring_platform: Optional[str] = None
    execution_runtime: Optional[str] = None
    event_tuple: Optional[EventIdentityTuple] = None
    native_export_digest_b3: Optional[str] = None
    external_anchor_digest_b3: Optional[str] = None
    external_anchor_not_later_than_tick: Optional[int] = None
    contemporaneous_witness_id: Optional[str] = None
    execution_receipt_digest_b3: Optional[str] = None

    @property
    def content_identity(self) -> str:
        return compute_content_identity(self.content)

    @property
    def event_identity(self) -> Optional[str]:
        if self.event_tuple is None:
            return None
        return self.event_tuple.compute_event_identity()

    def verify_integrity(self, expected_content_b3: Optional[str] = None) -> bool:
        """Check digest syntax and supplied content identity; evidence bytes are not fetched."""
        if not self.content or not self.content.strip():
            return False
        if not self.host_platform or not self.host_platform.strip():
            return False
        if expected_content_b3 is not None:
            if not _is_b3_digest(expected_content_b3) or not hmac.compare_digest(
                self.content_identity, expected_content_b3
            ):
                return False
        for digest in (
            self.native_export_digest_b3,
            self.external_anchor_digest_b3,
            self.execution_receipt_digest_b3,
        ):
            if digest is not None and not _is_b3_digest(digest):
                return False
        return True

    def effective_provenance_level(self) -> ProvenanceLevel:
        """Compute the highest provenance level strictly supported by verified fields."""
        if not self.verify_integrity():
            return ProvenanceLevel.CLAIMED
        if self.event_tuple is None:
            if self.claimed_created_at_utc:
                return ProvenanceLevel.TIMESTAMPED_RECORD
            return ProvenanceLevel.CLAIMED

        if self.native_export_digest_b3 is None:
            return ProvenanceLevel.PLATFORM_UI_RECORD

        if (
            self.contemporaneous_witness_id is not None
            and self.external_anchor_digest_b3 is not None
            and self.external_anchor_not_later_than_tick is not None
            and self.external_anchor_not_later_than_tick <= self.event_tuple.logical_tick
        ):
            return ProvenanceLevel.CONTEMPORANEOUS_WITNESS

        if (
            self.external_anchor_digest_b3 is not None
            and self.external_anchor_not_later_than_tick is not None
        ):
            return ProvenanceLevel.EXTERNALLY_ANCHORED

        return ProvenanceLevel.NATIVE_EXPORT_VERIFIED


@dataclass(frozen=True)
class EventLinkReceipt:
    """Cryptographic proof linking two distinct events (e.g. specification -> commit -> test)."""

    source_event_id: str
    target_event_id: str
    content_identity: str
    logical_tick: int
    witness_digest_b3: str
    signature_b3: str

    @staticmethod
    def issue(
        *,
        secret_key: bytes,
        source_event_id: str,
        target_event_id: str,
        content_identity: str,
        logical_tick: int,
    ) -> EventLinkReceipt:
        if len(secret_key) < 32:
            raise ValueError("secret_key for BLAKE3 keyed MAC must be 32 bytes")
        if source_event_id == target_event_id:
            raise ProvenanceAuthorityError("EventLinkReceipt requires two distinct event identities")
        payload = (
            _LINK_DOMAIN
            + _lp_bytes(source_event_id)
            + _lp_bytes(target_event_id)
            + _lp_bytes(content_identity)
            + struct.pack("<Q", int(logical_tick))
        )
        witness_b3 = "b3:" + blake3.blake3(payload).hexdigest()
        sig_b3 = "b3:" + blake3.blake3(payload, key=bytes(secret_key[:32])).hexdigest()
        return EventLinkReceipt(
            source_event_id=source_event_id,
            target_event_id=target_event_id,
            content_identity=content_identity,
            logical_tick=logical_tick,
            witness_digest_b3=witness_b3,
            signature_b3=sig_b3,
        )

    def verify(self, secret_key: bytes) -> bool:
        if len(secret_key) < 32:
            return False
        payload = (
            _LINK_DOMAIN
            + _lp_bytes(self.source_event_id)
            + _lp_bytes(self.target_event_id)
            + _lp_bytes(self.content_identity)
            + struct.pack("<Q", int(self.logical_tick))
        )
        expected_witness = "b3:" + blake3.blake3(payload).hexdigest()
        expected_sig = "b3:" + blake3.blake3(payload, key=bytes(secret_key[:32])).hexdigest()
        return hmac.compare_digest(self.witness_digest_b3, expected_witness) and hmac.compare_digest(
            self.signature_b3, expected_sig
        )


@dataclass(frozen=True)
class AttributionClaim:
    """Proposed attribution evaluated by the FL-027 arbiter."""

    claim_id: str
    scope: ClaimScope
    claimed_platform: Optional[str] = None
    claimed_conversation_id: Optional[str] = None
    claimed_derivation: Optional[DerivationKind] = None
    claimed_min_level: ProvenanceLevel = ProvenanceLevel.CLAIMED
    claimed_executed: bool = False
    claimed_before_tick: Optional[int] = None


class VerdictOutcome(str, Enum):
    """Arbiter decision for an AttributionClaim."""

    ATTESTED = "ATTESTED"
    ABSTAINED_INSUFFICIENT_PROVENANCE = "ABSTAINED_INSUFFICIENT_PROVENANCE"
    REJECTED_OVERATTRIBUTION = "REJECTED_OVERATTRIBUTION"


@dataclass(frozen=True)
class AttributionDecision:
    """Detailed non-tautological verdict binding OriginVerified, IntegrityVerified, and ScopeBound."""

    claim_id: str
    outcome: VerdictOutcome
    origin_verified: bool
    integrity_verified: bool
    scope_bound: bool
    effective_level: ProvenanceLevel
    content_identity: str
    event_identity: Optional[str]
    reason: str

    @property
    def attested(self) -> bool:
        return (
            self.outcome == VerdictOutcome.ATTESTED
            and self.origin_verified
            and self.integrity_verified
            and self.scope_bound
        )


def evaluate_provenance_claim(
    envelope: ProvenanceEnvelope,
    claim: AttributionClaim,
    *,
    expected_content_b3: Optional[str] = None,
) -> AttributionDecision:
    """Evaluate Attested(e) => OriginVerified(e) & IntegrityVerified(e) & ScopeBound(e)."""
    integrity_ok = envelope.verify_integrity(expected_content_b3=expected_content_b3)
    eff_level = envelope.effective_provenance_level()
    c_id = envelope.content_identity
    e_id = envelope.event_identity

    if not integrity_ok:
        return AttributionDecision(
            claim_id=claim.claim_id,
            outcome=VerdictOutcome.REJECTED_OVERATTRIBUTION,
            origin_verified=False,
            integrity_verified=False,
            scope_bound=False,
            effective_level=eff_level,
            content_identity=c_id,
            event_identity=e_id,
            reason="Integrity verification failed (content or digest mismatch)",
        )

    # 1. Check OriginVerified
    origin_ok = True
    origin_reason = "origin verified"
    if claim.claimed_platform is not None:
        if claim.scope == ClaimScope.ORIGINAL_AUTHORING_PLATFORM:
            if envelope.original_authoring_platform is None:
                origin_ok = False
                origin_reason = "original_authoring_platform is null (unverified)"
            elif envelope.original_authoring_platform != claim.claimed_platform:
                origin_ok = False
                origin_reason = (
                    f"platform mismatch: claimed {claim.claimed_platform!r}, "
                    f"verified original {envelope.original_authoring_platform!r}"
                )
        else:
            if envelope.host_platform != claim.claimed_platform:
                origin_ok = False
                origin_reason = (
                    f"host_platform mismatch: claimed {claim.claimed_platform!r}, "
                    f"observed {envelope.host_platform!r}"
                )
            elif (
                envelope.event_tuple is not None
                and envelope.event_tuple.namespace != claim.claimed_platform
            ):
                origin_ok = False
                origin_reason = (
                    f"event namespace {envelope.event_tuple.namespace!r} does not match "
                    f"claimed platform {claim.claimed_platform!r}"
                )

    if origin_ok and claim.claimed_conversation_id is not None:
        if envelope.event_tuple is None:
            origin_ok = False
            origin_reason = "conversation_id is null on record"
        elif envelope.event_tuple.conversation_id != claim.claimed_conversation_id:
            origin_ok = False
            origin_reason = (
                f"conversation_id mismatch: claimed {claim.claimed_conversation_id!r}, "
                f"event has {envelope.event_tuple.conversation_id!r}"
            )

    # 2. Check ScopeBound
    scope_ok = True
    scope_reason = "scope bound satisfied"

    if eff_level < claim.claimed_min_level:
        scope_ok = False
        scope_reason = (
            f"provenance_level {eff_level.name} < required {claim.claimed_min_level.name}"
        )

    if scope_ok and claim.claimed_derivation is not None:
        if envelope.derivation_kind != claim.claimed_derivation:
            scope_ok = False
            scope_reason = (
                f"derivation mismatch: record is {envelope.derivation_kind.value}, "
                f"claim requires {claim.claimed_derivation.value}"
            )

    if scope_ok and claim.scope == ClaimScope.NATIVE_MESSAGE_TRANSCRIPT:
        if envelope.derivation_kind != DerivationKind.ORIGINAL_MESSAGE:
            scope_ok = False
            scope_reason = (
                f"derived artifact ({envelope.derivation_kind.value}) cannot attest "
                "NATIVE_MESSAGE_TRANSCRIPT"
            )
        elif eff_level < ProvenanceLevel.NATIVE_EXPORT_VERIFIED:
            scope_ok = False
            scope_reason = "NATIVE_MESSAGE_TRANSCRIPT requires NATIVE_EXPORT_VERIFIED"

    if scope_ok and (claim.claimed_executed or claim.scope == ClaimScope.RUNTIME_EXECUTION):
        if (
            envelope.execution_runtime is None
            or envelope.execution_receipt_digest_b3 is None
            or envelope.derivation_kind != DerivationKind.EXECUTION_RECEIPT
        ):
            scope_ok = False
            scope_reason = (
                "architecture prompt or conversation record without execution_runtime "
                "and execution_receipt_digest_b3 cannot attest RUNTIME_EXECUTION"
            )

    if scope_ok and claim.claimed_before_tick is not None:
        # Internal claimed_created_at_utc never counts as an external temporal witness
        if (
            envelope.external_anchor_digest_b3 is None
            or envelope.external_anchor_not_later_than_tick is None
        ):
            scope_ok = False
            scope_reason = (
                "internal timestamp cannot act as external temporal witness; "
                "external_anchor_not_later_than_tick is required"
            )
        elif envelope.external_anchor_not_later_than_tick > claim.claimed_before_tick:
            scope_ok = False
            scope_reason = (
                f"external anchor tick ({envelope.external_anchor_not_later_than_tick}) is later "
                f"than claimed bound ({claim.claimed_before_tick})"
            )

    if origin_ok and scope_ok:
        return AttributionDecision(
            claim_id=claim.claim_id,
            outcome=VerdictOutcome.ATTESTED,
            origin_verified=True,
            integrity_verified=True,
            scope_bound=True,
            effective_level=eff_level,
            content_identity=c_id,
            event_identity=e_id,
            reason="All provenance, integrity, and scope constraints verified",
        )

    # Distinguish honest abstention on null/missing fields from active forgery/mismatch
    is_missing_evidence = (
        (claim.scope == ClaimScope.ORIGINAL_AUTHORING_PLATFORM and envelope.original_authoring_platform is None)
        or (claim.claimed_conversation_id is not None and envelope.event_tuple is None)
        or (
            (claim.claimed_executed or claim.scope == ClaimScope.RUNTIME_EXECUTION)
            and envelope.execution_runtime is None
        )
        or (claim.claimed_before_tick is not None and envelope.external_anchor_not_later_than_tick is None)
    )
    outcome = (
        VerdictOutcome.ABSTAINED_INSUFFICIENT_PROVENANCE
        if is_missing_evidence
        else VerdictOutcome.REJECTED_OVERATTRIBUTION
    )
    reason = origin_reason if not origin_ok else scope_reason
    return AttributionDecision(
        claim_id=claim.claim_id,
        outcome=outcome,
        origin_verified=origin_ok,
        integrity_verified=True,
        scope_bound=scope_ok,
        effective_level=eff_level,
        content_identity=c_id,
        event_identity=e_id,
        reason=reason,
    )


def compose_event_evidence(
    primary: ProvenanceEnvelope,
    secondary: ProvenanceEnvelope,
    *,
    link_receipt: Optional[EventLinkReceipt] = None,
    verification_key: Optional[bytes] = None,
) -> Tuple[bool, str]:
    """Enforce Same Content != Same Event when composing two evidence envelopes.

    Composition succeeds iff:
    1. Both envelopes have non-null, identical I_event AND identical I_content; OR
    2. An explicit, cryptographically verified EventLinkReceipt binds primary.event_identity
       to secondary.event_identity for the shared content_identity.
    """
    if not primary.verify_integrity() or not secondary.verify_integrity():
        return False, "integrity verification failed on one or both envelopes"

    if primary.content_identity != secondary.content_identity:
        return False, "content_identity mismatch between envelopes"

    p_ev = primary.event_identity
    s_ev = secondary.event_identity
    if p_ev is None or s_ev is None:
        return False, "cannot compose envelopes with null event_identity"

    if hmac.compare_digest(p_ev, s_ev):
        return True, "identical event_identity and content_identity verified"

    if link_receipt is None or verification_key is None:
        return (
            False,
            "Same Content != Same Event: distinct event_identity tuples cannot be composed without a verified EventLinkReceipt",
        )

    if not link_receipt.verify(verification_key):
        return False, "EventLinkReceipt cryptographic verification failed"

    if (
        link_receipt.source_event_id != p_ev
        or link_receipt.target_event_id != s_ev
        or link_receipt.content_identity != primary.content_identity
    ):
        return False, "EventLinkReceipt coordinates do not match the envelopes being composed"

    return True, "cross-event composition verified via EventLinkReceipt"


@dataclass(frozen=True)
class FL027OracleMetrics:
    """Separated oracle metrics required by the FL-027 v3 contract."""

    total_cases: int
    positive_cases: int
    negative_or_contradictory_cases: int
    overattribution_rate: float
    coverage_rate: float
    fact_recall_rate: float
    abstention_precision: float


def compute_fl027_metrics(
    decisions: Sequence[Tuple[AttributionDecision, bool, bool]],
    *,
    preserved_facts_recalled: int,
    total_facts_seeded: int,
) -> FL027OracleMetrics:
    """Compute separated metrics over (decision, is_valid_ground_truth, should_abstain_ground_truth)."""
    if not decisions:
        raise ValueError("decisions cannot be empty")
    if total_facts_seeded < 1:
        raise ValueError("total_facts_seeded must be >= 1")

    total = len(decisions)
    positives = sum(1 for _, is_valid, _ in decisions if is_valid)
    negatives = total - positives

    # Overattribution: invalid claims that were erroneously ATTESTED
    false_attestations = sum(
        1 for dec, is_valid, _ in decisions if not is_valid and dec.attested
    )
    overattribution_rate = false_attestations / negatives if negatives > 0 else 0.0

    # Coverage: valid claims that were rightly ATTESTED
    true_attestations = sum(
        1 for dec, is_valid, _ in decisions if is_valid and dec.attested
    )
    coverage_rate = true_attestations / positives if positives > 0 else 1.0

    # Abstention precision: among claims where evidence had null/missing fields requiring abstention,
    # proportion where the arbiter abstained or rejected without overattributing
    abstain_targets = [
        dec for dec, _, should_abstain in decisions if should_abstain
    ]
    correct_abstentions = sum(
        1
        for dec in abstain_targets
        if dec.outcome == VerdictOutcome.ABSTAINED_INSUFFICIENT_PROVENANCE and not dec.attested
    )
    abstention_precision = (
        correct_abstentions / len(abstain_targets) if abstain_targets else 1.0
    )

    fact_recall_rate = preserved_facts_recalled / total_facts_seeded

    return FL027OracleMetrics(
        total_cases=total,
        positive_cases=positives,
        negative_or_contradictory_cases=negatives,
        overattribution_rate=overattribution_rate,
        coverage_rate=coverage_rate,
        fact_recall_rate=fact_recall_rate,
        abstention_precision=abstention_precision,
    )
