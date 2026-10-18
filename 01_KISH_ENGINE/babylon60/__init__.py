"""
BABYLON-60 — C5-REAL Autonomous Agent Execution & Compliance Kernel.
Provides cryptographic attestation, BFT consensus ledgers, and EU AI Act compliance.
"""

from babylon60.api import (
    AssuranceLevel,
    AuditSession,
    BatchMerkleAccumulator,
    Tracer,
    watch,
)
from babylon60.verifier import (
    verify_compliance_certificate,
    verify_offline_evidence,
)

__version__ = "5.0.0"

__all__ = [
    "Tracer",
    "AssuranceLevel",
    "watch",
    "BatchMerkleAccumulator",
    "AuditSession",
    "verify_compliance_certificate",
    "verify_offline_evidence",
    "__version__",
]
