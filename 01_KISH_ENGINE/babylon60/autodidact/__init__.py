# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω | SUBSYSTEM EXPORTS | STATE: C5-REAL
# ============================================================================
"""
Subsistema AUTODIDACT-Ω: Auto-aprendizaje, Deep Research y Falsación Popperiana.
"""

from babylon60.autodidact.crystal_compiler import CrystalCompiler
from babylon60.autodidact.engine import AutodidactOmegaEngine
from babylon60.autodidact.epistemology import (
    HumeViolationError,
    UnverifiedPremiseError,
    derive,
    hash_justification,
    hash_statement,
    optimize,
    verify,
)
from babylon60.autodidact.fetchers import ArxivFetcher, LocalCorpusFetcher
from babylon60.autodidact.falsifier import PopperianFalsifier
from babylon60.autodidact.royal_rumble import (
    EpistemicPhase,
    IdentityStatus,
    InteractionTurn,
    ModelEvaluationSitrep,
    RoyalRumbleEngine,
)
from babylon60.autodidact.types import (
    EpistemicCrystal,
    EvidenceSource,
    FalsificationVerdict,
    Justification,
    JustifiedStatement,
    Modality,
    Obligation,
    RawEvidence,
    Statement,
    StatementStatus,
)

__all__ = [
    "AutodidactOmegaEngine",
    "CrystalCompiler",
    "PopperianFalsifier",
    "ArxivFetcher",
    "LocalCorpusFetcher",
    "Statement",
    "Justification",
    "JustifiedStatement",
    "StatementStatus",
    "Modality",
    "Obligation",
    "EvidenceSource",
    "RawEvidence",
    "FalsificationVerdict",
    "EpistemicCrystal",
    "hash_statement",
    "hash_justification",
    "verify",
    "derive",
    "optimize",
    "HumeViolationError",
    "UnverifiedPremiseError",
    "RoyalRumbleEngine",
    "EpistemicPhase",
    "IdentityStatus",
    "InteractionTurn",
    "ModelEvaluationSitrep",
]
