"""FL-022: Final-Artifact Verification in CORTEX-Persist.

Enforces the separation between proxy optimization (`ProxyScore(x)`) and final
materialized artifact verification (`FinalUtility(T(x))`) across durable lineage
in `MemoryGovernanceEngine`:

    Accepted(a) => Hash(a) == Hash(a_verified)
                   && IndependentCheck(a) == PASS
                   && CriticalConstraints(a) == PASS
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from blake3 import blake3

from babylon60.memory.governance import (
    MemoryGovernanceEngine,
    MemoryKind,
    MemoryModality,
    MemoryRecordView,
    MemoryStatus,
    TrustLevel,
)

FL022_SCHEMA = "FL-022-FINAL-ARTIFACT-v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class FinalArtifactVerificationError(RuntimeError):
    """Raised when a final artifact fails FL-022 identity, freshness, or critical verification."""


@dataclass(frozen=True)
class FinalArtifactRecord:
    """Durable lineage tuple recorded in CORTEX-Persist for an optimized candidate."""

    candidate_id: int
    optimization_record_id: str
    transform_record_id: str
    verification_record_id: str
    proxy_score_bps: int
    primary_final_utility_bps: int
    independent_solver_utility_bps: int
    critical_constraints_pass: bool
    optimized_state_hash_b3: str
    verified_artifact_hash_b3: str
    presented_artifact_hash_b3: str
    evidence_epoch: int
    evidence_target_id: int
    verifier_attestation_digest_b3: str


@dataclass(frozen=True)
class FinalArtifactAcceptanceDecision:
    """Outcome of the BABYLON-60 / CORTEX-Persist FL-022 gate."""

    accepted: bool
    reason: str | None
    final_artifact_hash_b3: str
    joint_evidence_digest_b3: str | None
    authorization_record_id: str | None


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def compute_artifact_b3(raw_bytes: bytes | str) -> str:
    """Compute canonical 64-hex BLAKE3 digest for an optimization state or final artifact."""
    data = raw_bytes.encode("utf-8") if isinstance(raw_bytes, str) else raw_bytes
    return blake3(b"B60:FL-022:ARTIFACT:v1\0" + data).hexdigest()


def compute_verifier_attestation_b3(
    *,
    candidate_id: int,
    optimized_state_hash_b3: str,
    verified_artifact_hash_b3: str,
    primary_final_utility_bps: int,
    independent_solver_utility_bps: int,
    critical_constraints_pass: bool,
    evidence_epoch: int,
    evidence_target_id: int,
) -> str:
    """Compute deterministic BLAKE3 digest binding the independent verifier's observation."""
    if not (_HEX64.match(optimized_state_hash_b3) and _HEX64.match(verified_artifact_hash_b3)):
        raise FinalArtifactVerificationError("Hashes must be 64 lowercase hex characters")
    payload = {
        "schema": FL022_SCHEMA,
        "candidate_id": candidate_id,
        "optimized_state_hash_b3": optimized_state_hash_b3,
        "verified_artifact_hash_b3": verified_artifact_hash_b3,
        "primary_final_utility_bps": primary_final_utility_bps,
        "independent_solver_utility_bps": independent_solver_utility_bps,
        "critical_constraints_pass": critical_constraints_pass,
        "evidence_epoch": evidence_epoch,
        "evidence_target_id": evidence_target_id,
    }
    return blake3(b"B60:FL-022:VERIFIER_ATTESTATION:v1\0" + _canonical_json(payload).encode("utf-8")).hexdigest()


class FinalArtifactGate:
    """Persists optimization lineage in CORTEX-Persist and gates authority on the final artifact."""

    def __init__(
        self,
        governance: MemoryGovernanceEngine,
        *,
        tenant_id: str,
        principal: str,
        active_policy_epoch: int = 1,
        final_utility_threshold_bps: int = 6_200,
        max_solver_delta_bps: int = 120,
    ) -> None:
        self._governance = governance
        self._tenant_id = tenant_id
        self._principal = principal
        self._active_policy_epoch = active_policy_epoch
        self._final_utility_threshold_bps = final_utility_threshold_bps
        self._max_solver_delta_bps = max_solver_delta_bps
        self._authorized_nonces: set[tuple[int, str]] = set()

    @property
    def active_policy_epoch(self) -> int:
        return self._active_policy_epoch

    def register_candidate_lineage(
        self,
        *,
        candidate_id: int,
        proxy_score_bps: int,
        transform_spec: str,
        primary_final_utility_bps: int,
        independent_solver_utility_bps: int,
        critical_constraints_pass: bool,
        optimized_state_hash_b3: str,
        verified_artifact_hash_b3: str,
        presented_artifact_hash_b3: str | None = None,
        evidence_epoch: int | None = None,
        evidence_target_id: int | None = None,
    ) -> FinalArtifactRecord:
        """Record the optimization target, final transformation, artifact hash, and verifier evidence."""
        actual_presented = presented_artifact_hash_b3 or verified_artifact_hash_b3
        actual_epoch = self._active_policy_epoch if evidence_epoch is None else evidence_epoch
        actual_target_id = candidate_id if evidence_target_id is None else evidence_target_id

        if not (
            _HEX64.match(optimized_state_hash_b3)
            and _HEX64.match(verified_artifact_hash_b3)
            and _HEX64.match(actual_presented)
        ):
            raise FinalArtifactVerificationError("Invalid BLAKE3 hex digest in candidate lineage")

        opt_payload = {
            "schema": FL022_SCHEMA,
            "stage": "OPTIMIZATION_OBJECTIVE",
            "candidate_id": candidate_id,
            "proxy_score_bps": proxy_score_bps,
            "optimized_state_hash_b3": optimized_state_hash_b3,
        }
        opt_view = self._governance.add_record(
            tenant_id=self._tenant_id,
            principal=self._principal,
            content=_canonical_json(opt_payload),
            kind=MemoryKind.SOURCE_RECORD,
            modality=MemoryModality.EPISTEMIC,
            trust_level=TrustLevel.RESTRICTED,
            subject_key=f"cortex.fl022.candidate.{candidate_id}.opt",
        )

        transform_payload = {
            "schema": FL022_SCHEMA,
            "stage": "FINAL_TRANSFORMATION",
            "candidate_id": candidate_id,
            "transform_spec": transform_spec,
            "optimized_state_hash_b3": optimized_state_hash_b3,
            "presented_artifact_hash_b3": actual_presented,
        }
        transform_view = self._governance.add_record(
            tenant_id=self._tenant_id,
            principal=self._principal,
            content=_canonical_json(transform_payload),
            kind=MemoryKind.MEMORY_EVENT,
            modality=MemoryModality.EPISTEMIC,
            trust_level=TrustLevel.RESTRICTED,
            parents=[opt_view.record_id],
            subject_key=f"cortex.fl022.candidate.{candidate_id}.transform",
        )

        attestation_digest = compute_verifier_attestation_b3(
            candidate_id=candidate_id,
            optimized_state_hash_b3=optimized_state_hash_b3,
            verified_artifact_hash_b3=verified_artifact_hash_b3,
            primary_final_utility_bps=primary_final_utility_bps,
            independent_solver_utility_bps=independent_solver_utility_bps,
            critical_constraints_pass=critical_constraints_pass,
            evidence_epoch=actual_epoch,
            evidence_target_id=actual_target_id,
        )

        ver_payload = {
            "schema": FL022_SCHEMA,
            "stage": "INDEPENDENT_VERIFICATION",
            "candidate_id": candidate_id,
            "verified_artifact_hash_b3": verified_artifact_hash_b3,
            "primary_final_utility_bps": primary_final_utility_bps,
            "independent_solver_utility_bps": independent_solver_utility_bps,
            "critical_constraints_pass": critical_constraints_pass,
            "evidence_epoch": actual_epoch,
            "evidence_target_id": actual_target_id,
            "verifier_attestation_digest_b3": attestation_digest,
        }
        ver_view = self._governance.add_record(
            tenant_id=self._tenant_id,
            principal=self._principal,
            content=_canonical_json(ver_payload),
            kind=MemoryKind.SOURCE_RECORD,
            modality=MemoryModality.EPISTEMIC,
            trust_level=TrustLevel.SOVEREIGN,
            parents=[transform_view.record_id],
            depends_on=[opt_view.record_id],
            subject_key=f"cortex.fl022.candidate.{candidate_id}.verification",
        )

        return FinalArtifactRecord(
            candidate_id=candidate_id,
            optimization_record_id=opt_view.record_id,
            transform_record_id=transform_view.record_id,
            verification_record_id=ver_view.record_id,
            proxy_score_bps=proxy_score_bps,
            primary_final_utility_bps=primary_final_utility_bps,
            independent_solver_utility_bps=independent_solver_utility_bps,
            critical_constraints_pass=critical_constraints_pass,
            optimized_state_hash_b3=optimized_state_hash_b3,
            verified_artifact_hash_b3=verified_artifact_hash_b3,
            presented_artifact_hash_b3=actual_presented,
            evidence_epoch=actual_epoch,
            evidence_target_id=actual_target_id,
            verifier_attestation_digest_b3=attestation_digest,
        )

    def _require_active(self, record_id: str) -> MemoryRecordView:
        view = self._governance.get_record(record_id, tenant_id=self._tenant_id, include_inactive=True)
        if view.status != MemoryStatus.ACTIVE:
            raise FinalArtifactVerificationError(f"Lineage record {record_id} is not ACTIVE ({view.status})")
        return view

    def authorize_publication(self, record: FinalArtifactRecord) -> FinalArtifactAcceptanceDecision:
        """Condition publication/execution authority strictly on the verified final artifact (Config C)."""
        # 1. Verify all CORTEX-Persist lineage records remain ACTIVE and untampered
        opt_view = self._require_active(record.optimization_record_id)
        trans_view = self._require_active(record.transform_record_id)
        ver_view = self._require_active(record.verification_record_id)

        expected_att = compute_verifier_attestation_b3(
            candidate_id=record.candidate_id,
            optimized_state_hash_b3=record.optimized_state_hash_b3,
            verified_artifact_hash_b3=record.verified_artifact_hash_b3,
            primary_final_utility_bps=record.primary_final_utility_bps,
            independent_solver_utility_bps=record.independent_solver_utility_bps,
            critical_constraints_pass=record.critical_constraints_pass,
            evidence_epoch=record.evidence_epoch,
            evidence_target_id=record.evidence_target_id,
        )
        if expected_att != record.verifier_attestation_digest_b3:
            return FinalArtifactAcceptanceDecision(
                accepted=False,
                reason="invalid_verifier_attestation_digest",
                final_artifact_hash_b3=record.presented_artifact_hash_b3,
                joint_evidence_digest_b3=None,
                authorization_record_id=None,
            )

        # 2. Identity check: Hash(a_presented) == Hash(a_verified)
        if record.presented_artifact_hash_b3 != record.verified_artifact_hash_b3:
            return FinalArtifactAcceptanceDecision(
                accepted=False,
                reason="artifact_identity_mismatch",
                final_artifact_hash_b3=record.presented_artifact_hash_b3,
                joint_evidence_digest_b3=None,
                authorization_record_id=None,
            )

        # 3. Target/version binding check
        if record.evidence_target_id != record.candidate_id:
            return FinalArtifactAcceptanceDecision(
                accepted=False,
                reason="cross_version_target_mismatch",
                final_artifact_hash_b3=record.presented_artifact_hash_b3,
                joint_evidence_digest_b3=None,
                authorization_record_id=None,
            )

        # 4. Epoch freshness check
        if record.evidence_epoch < self._active_policy_epoch:
            return FinalArtifactAcceptanceDecision(
                accepted=False,
                reason="stale_evidence_epoch",
                final_artifact_hash_b3=record.presented_artifact_hash_b3,
                joint_evidence_digest_b3=None,
                authorization_record_id=None,
            )

        # 5. Primary final utility & critical constraints on materialized artifact
        if record.primary_final_utility_bps < self._final_utility_threshold_bps or not record.critical_constraints_pass:
            return FinalArtifactAcceptanceDecision(
                accepted=False,
                reason="critical_constraints_failed",
                final_artifact_hash_b3=record.presented_artifact_hash_b3,
                joint_evidence_digest_b3=None,
                authorization_record_id=None,
            )

        # 6. Independent verifier check (IndependentCheck(a) == PASS)
        solver_delta = abs(record.primary_final_utility_bps - record.independent_solver_utility_bps)
        if (
            record.independent_solver_utility_bps < self._final_utility_threshold_bps
            or solver_delta > self._max_solver_delta_bps
        ):
            return FinalArtifactAcceptanceDecision(
                accepted=False,
                reason="independent_check_failed",
                final_artifact_hash_b3=record.presented_artifact_hash_b3,
                joint_evidence_digest_b3=None,
                authorization_record_id=None,
            )

        # 7. Anti-replay guard
        replay_key = (record.candidate_id, record.presented_artifact_hash_b3)
        if replay_key in self._authorized_nonces:
            return FinalArtifactAcceptanceDecision(
                accepted=False,
                reason="replay_detected",
                final_artifact_hash_b3=record.presented_artifact_hash_b3,
                joint_evidence_digest_b3=None,
                authorization_record_id=None,
            )
        self._authorized_nonces.add(replay_key)

        joint_payload = {
            "schema": FL022_SCHEMA,
            "candidate_id": record.candidate_id,
            "final_artifact_hash_b3": record.presented_artifact_hash_b3,
            "verifier_attestation_digest_b3": record.verifier_attestation_digest_b3,
            "commitments": [opt_view.commitment, trans_view.commitment, ver_view.commitment],
        }
        joint_digest = blake3(
            b"B60:FL-022:JOINT_AUTHORIZATION:v1\0" + _canonical_json(joint_payload).encode("utf-8")
        ).hexdigest()

        auth_view = self._governance.add_record(
            tenant_id=self._tenant_id,
            principal=self._principal,
            content=_canonical_json(
                {
                    "schema": FL022_SCHEMA,
                    "stage": "AUTHORIZED_FINAL_ARTIFACT",
                    "candidate_id": record.candidate_id,
                    "final_artifact_hash_b3": record.presented_artifact_hash_b3,
                    "joint_evidence_digest_b3": joint_digest,
                }
            ),
            kind=MemoryKind.MEMORY_EVENT,
            modality=MemoryModality.EPISTEMIC,
            trust_level=TrustLevel.SOVEREIGN,
            parents=[ver_view.record_id],
            depends_on=[opt_view.record_id, trans_view.record_id],
            subject_key=f"cortex.fl022.candidate.{record.candidate_id}.authorized",
        )

        return FinalArtifactAcceptanceDecision(
            accepted=True,
            reason=None,
            final_artifact_hash_b3=record.presented_artifact_hash_b3,
            joint_evidence_digest_b3=joint_digest,
            authorization_record_id=auth_view.record_id,
        )
