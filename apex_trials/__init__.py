"""apex_trials — deterministic, auditable clinical-trial amendment-risk copilot.

Built on the cortex-persist / BABYLON-60 tamper-evident ledger contract.
Data source: ClinicalTrials.gov API v2 (+ internal history plane).

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""
from __future__ import annotations

from .copilot import Copilot, CopilotResult
from .ctgov import AmendmentHistory, CtGovClient, CtGovError, HttpCache, classify_history
from .features import StudyFeatures, extract_features
from .ledger import AmendmentLedger, ChainVerification, LedgerEntry
from .risk_engine import RiskAssessment, assess

__version__ = "0.1.0"
__all__ = [
    "Copilot", "CopilotResult",
    "CtGovClient", "CtGovError", "HttpCache", "AmendmentHistory", "classify_history",
    "StudyFeatures", "extract_features",
    "AmendmentLedger", "ChainVerification", "LedgerEntry",
    "RiskAssessment", "assess",
]
