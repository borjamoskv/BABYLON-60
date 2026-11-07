"""FL-VERIFY-01 (PROPOSED / UNTESTED): contrato mínimo de evidencia de hallazgos.

Modelo a nivel bloque, sin I/O ni efectos. Separa tres objetos:
Finding (qué se afirma sobre qué artefacto), ReproductionRun (qué se observó)
y Authorization (quién autorizó un efecto).

Invariante:
    VERIFIED(f) <=> existe run con run.artifact_digest == f.inspected_artifact_digest
                    y run.observed_behavior_id == f.prohibited_behavior_id
                    y run.outcome == REPRODUCED
"""

from __future__ import annotations

import enum
import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Sequence

if TYPE_CHECKING:
    from babylon60.verification.verification_gate import VerificationGate

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class ContractViolation(ValueError):
    """Violación del contrato de evidencia (fail-closed)."""


class Outcome(enum.Enum):
    REPRODUCED = "REPRODUCED"
    NOT_REPRODUCED = "NOT_REPRODUCED"


def _validate_digest(digest: str, label: str) -> None:
    if (
        not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None
        or digest.lower() == EMPTY_SHA256
    ):
        raise ContractViolation(f"{label}: digest vacío, mal formado o huérfano")


@dataclass(frozen=True)
class Finding:
    finding_id: str
    prohibited_behavior_id: str
    inspected_artifact_digest: str
    producer_id: str

    def __post_init__(self) -> None:
        _validate_digest(self.inspected_artifact_digest, "Finding.inspected_artifact_digest")


@dataclass(frozen=True)
class ReproductionRun:
    finding_id: str
    artifact_digest: str
    observed_behavior_id: str
    outcome: Outcome
    verifier_id: str

    def __post_init__(self) -> None:
        _validate_digest(self.artifact_digest, "ReproductionRun.artifact_digest")


@dataclass(frozen=True)
class Authorization:
    finding_id: str
    action: str
    signoff_receipt_digest: str

    def __post_init__(self) -> None:
        _validate_digest(self.signoff_receipt_digest, "Authorization.signoff_receipt_digest")


def is_verified(finding: Finding, runs: Sequence[ReproductionRun]) -> bool:
    """True solo si alguna reproducción acredita el comportamiento prohibido sobre el mismo artefacto."""
    for run in runs:
        if run.finding_id != finding.finding_id:
            continue
        if run.verifier_id == finding.producer_id:
            continue  # productor != verificador
        if (
            run.outcome is Outcome.REPRODUCED
            and run.artifact_digest == finding.inspected_artifact_digest
            and run.observed_behavior_id == finding.prohibited_behavior_id
        ):
            return True
    return False


def authorize_effect(
    finding: Finding,
    runs: Sequence[ReproductionRun],
    authorization: Optional[Authorization],
    action: str,
) -> None:
    """Fail-closed: un efecto exige hallazgo verificado y autorización explícita de esa acción."""
    if not is_verified(finding, runs):
        raise ContractViolation("efecto sobre hallazgo no verificado")
    if authorization is None or authorization.finding_id != finding.finding_id or authorization.action != action:
        raise ContractViolation("efecto sin autorización para este hallazgo y acción")


def verify_authorization_in_ledger(authorization: Authorization, gate: "VerificationGate") -> None:
    """Fail-closed: la autorización debe corresponder a un recibo APPROVED del ledger íntegro.

    Exige cadena SHA-256 íntegra y una fila de `audit_ledger` con
    cryptographic_digest == signoff_receipt_digest, execution_id == finding_id,
    action_name == action y decision == "APPROVED".
    """
    if not gate.verify_ledger_integrity():
        raise ContractViolation("ledger de autorizaciones con cadena hash rota")
    row = gate._conn.execute(  # noqa: SLF001 - lectura en el mismo paquete, sin mutación
        "SELECT execution_id, action_name, decision FROM audit_ledger WHERE cryptographic_digest = ?",
        (authorization.signoff_receipt_digest,),
    ).fetchone()
    if row is None:
        raise ContractViolation("recibo de autorización inexistente en el ledger")
    execution_id, action_name, decision = row
    if execution_id != authorization.finding_id or action_name != authorization.action or decision != "APPROVED":
        raise ContractViolation("recibo de autorización no corresponde a este hallazgo, acción o decisión")
