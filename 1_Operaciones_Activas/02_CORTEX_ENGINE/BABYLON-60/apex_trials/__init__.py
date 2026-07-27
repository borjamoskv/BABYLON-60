# C5-REAL EXERGY CERTIFIED
"""apex_trials — deterministic, auditable clinical-trial amendment-risk transducer.

Built on the cortex-persist / BABYLON-60 tamper-evident ledger contract.
Data source: ClinicalTrials.gov API v2 (+ internal history plane).

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""

from __future__ import annotations

from .transducer import Transducer, TransducerResult
from .ctgov import AmendmentHistory, CtGovClient, CtGovError, HttpCache, classify_history
from .features import StudyFeatures, extract_features
from .ledger import AmendmentLedger, BabylonBFTLedgerAdapter, ChainVerification, LedgerEntry
from .risk_engine import RiskAssessment, assess

# Backwards compatibility aliases
Copilot = Transducer
CopilotResult = TransducerResult

__version__ = "0.2.0"
__all__ = [
    "Transducer",
    "TransducerResult",
    "Copilot",
    "CopilotResult",
    "CtGovClient",
    "CtGovError",
    "HttpCache",
    "AmendmentHistory",
    "classify_history",
    "StudyFeatures",
    "extract_features",
    "AmendmentLedger",
    "BabylonBFTLedgerAdapter",
    "ChainVerification",
    "LedgerEntry",
    "RiskAssessment",
    "assess",
]
