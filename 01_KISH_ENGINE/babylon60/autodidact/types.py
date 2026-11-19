# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω | EPISTEMIC PRIMITIVES & TYPES | STATE: C5-REAL
# ============================================================================
"""
Tipos y primitivas causales para el Motor AUTODIDACT-Ω.
Formalización: Lógica intuicionista de Harrop + Guillotina de Hume.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Modality(str, Enum):
    """
    Parámetro de modalidad M ∈ {Epistemic, Deontic}.
    Captura formal de la Guillotina de Hume:
    - EPISTEMIC: Aserciones sobre lo que ES (hechos, hipótesis, observaciones, teoremas).
    - DEONTIC: Aserciones sobre lo que DEBE SER (políticas, restricciones éticas, mandatos).
    """

    EPISTEMIC = "epistemic"
    DEONTIC = "deontic"


class Obligation(str, Enum):
    """
    Obligaciones de prueba que deben ser descargadas para verificar un Statement.
    """

    PROVENANCE = "provenance"
    REPRODUCIBILITY = "reproducibility"
    CONTRADICTION = "contradiction"
    CONFIDENCE = "confidence"
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    ENVIRONMENT_MATCH = "environment_match"
    MODEL_ORTHOGONALITY = "model_orthogonality"
    OBSERVED_CONSTRAINTS = "observed_constraints"


class EvidenceSource(str, Enum):
    """Fuentes físicas y lógicas de evidencia."""

    FILESYSTEM = "filesystem"
    GIT_OBJECTS = "git_objects"
    COMPILER_LOGS = "compiler_logs"
    CPU_COUNTERS = "cpu_counters"
    KERNEL_EVENTS = "kernel_events"
    ARXIV_PAPER = "arxiv_paper"
    SILICON_BENCHMARK = "silicon_benchmark"
    SWARM_CONSENSUS = "swarm_consensus"


@dataclass
class RawEvidence:
    """Evidencia primaria cruda no interpretada."""

    source: EvidenceSource
    raw_payload: str | bytes | Dict[str, Any]
    timestamp_ns: int = field(default_factory=time.time_ns)
    digest_sha256: Optional[str] = None


@dataclass
class Statement:
    """
    Statement⟨M⟩ — Proposición tipada parametrizada por modalidad.
    Corresponde a una fórmula de Harrop sobre signatura Σ.
    """

    content: str
    modality: Modality
    obligations: List[Obligation] = field(default_factory=list)


@dataclass
class Justification:
    """
    Término de prueba que establece POR QUÉ un Statement es válido.
    """

    kind: str  # "FormalProof", "StatisticalInference", "Observation", "ExpertConsensus", "Conjecture", "Axiom"
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class StatementStatus(str, Enum):
    """Estatus ontológico del Statement en el grafo de conocimiento."""

    CANDIDATE = "candidate"
    STABILIZED = "stabilized"
    CANONICAL = "canonical"
    FALSIFIED = "falsified"
    DISCREDITED = "discredited"  # Invalidad por colapso en cascada de sus premisas (B4)


@dataclass
class JustifiedStatement:
    """El par atómico de conocimiento formal: (S, J)."""

    statement: Statement
    justification: Justification
    statement_hash: Optional[str] = None
    created_at_ns: int = field(default_factory=time.time_ns)
    status: StatementStatus = StatementStatus.CANDIDATE
    dependencies: List[str] = field(default_factory=list)  # Hashes de premisas causales


@dataclass
class FalsificationVerdict:
    """Resultado formal de una prueba de falsación Popperiana."""

    claim: str
    falsified: bool
    verdict: str  # "FALSIFIED", "SUPPORTED", "UNTESTABLE"
    contradiction_node: Optional[str] = None
    telemetry: Dict[str, Any] = field(default_factory=dict)
    evidence_digest: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "falsified": self.falsified,
            "verdict": self.verdict,
            "contradiction_node": self.contradiction_node,
            "telemetry": self.telemetry,
            "evidence_digest": self.evidence_digest,
        }


@dataclass(frozen=True)
class ScopedClaimRecord:
    """Afirmación delimitada por alcance y evidencia (FL-022-v2 & BORJARIO IR B3/B6).

    Prohíbe etiquetas ontológicas absolutas (`status = SAFE`) exigiendo alcance explícito
    (`verified_profile`, `observed_profile`), desacoplamiento de modelos
    (`optimizer_model != verifier_model`), identidad criptográfica entre verificación y
    despliegue (`artifact_digest == deployed_digest`) y cumplimiento de restricciones observadas.
    """

    claim_id: str
    claim: str
    verifier_model: str
    optimizer_model: str
    artifact_digest: str
    deployed_digest: str
    verified_profile: str
    observed_profile: str
    logical_tick: int
    critical_constraints_pass: bool
    result: str  # "SUPPORTED" | "OBSERVED" | "FALSIFIED" | "REJECTED_OUT_OF_SCOPE"

    def __post_init__(self) -> None:
        if not self.verified_profile.strip() or not self.observed_profile.strip():
            raise ValueError("BJR-E013: ScopedClaimRecord requires explicit verified_profile and observed_profile.")
        if self.result not in ("SUPPORTED", "OBSERVED", "FALSIFIED", "REJECTED_OUT_OF_SCOPE"):
            raise ValueError(
                f"BJR-E021: Invalid claim result '{self.result}'; ontological 'SAFE' labels are forbidden."
            )

    @property
    def is_valid_fl022_v2(self) -> bool:
        return (
            bool(self.artifact_digest)
            and self.artifact_digest == self.deployed_digest
            and bool(self.verifier_model)
            and bool(self.optimizer_model)
            and self.verifier_model != self.optimizer_model
            and self.verified_profile == self.observed_profile
            and self.critical_constraints_pass is True
            and self.result in ("SUPPORTED", "OBSERVED")
        )

    def to_justification_parameters(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim": self.claim,
            "verifier_model": self.verifier_model,
            "optimizer_model": self.optimizer_model,
            "artifact_digest": self.artifact_digest,
            "deployed_digest": self.deployed_digest,
            "verified_profile": self.verified_profile,
            "observed_profile": self.observed_profile,
            "logical_tick": self.logical_tick,
            "critical_constraints_pass": self.critical_constraints_pass,
            "result": self.result,
        }


@dataclass
class EpistemicCrystal:
    """Documento formal consolidado (Cristal Epistémico) con firma de autoría e integridad."""

    topic: str
    thesis: str
    statements: List[JustifiedStatement]
    falsification_verdicts: List[FalsificationVerdict]
    merkle_root: str
    author: str = "Borja Fernández Angulo"
    affiliation: str = "Investigador en Sistemas Complejos"
    compiled_at_iso: str = ""
    markdown_content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "thesis": self.thesis,
            "author": self.author,
            "affiliation": self.affiliation,
            "compiled_at_iso": self.compiled_at_iso,
            "merkle_root": self.merkle_root,
            "statements": [
                {
                    "content": s.statement.content,
                    "modality": s.statement.modality.value,
                    "obligations": [o.value for o in s.statement.obligations],
                    "justification_kind": s.justification.kind,
                    "confidence": s.justification.confidence,
                    "statement_hash": s.statement_hash,
                    "status": s.status.value,
                    "dependencies": s.dependencies,
                }
                for s in self.statements
            ],
            "falsification_verdicts": [fv.to_dict() for fv in self.falsification_verdicts],
            "markdown_content": self.markdown_content,
        }
