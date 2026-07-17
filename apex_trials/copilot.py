"""apex_trials.copilot — orchestration: fetch -> features -> score -> ledger.

This is the seam that makes the product *superior on the auditability axis*:
every risk assessment is committed to the cortex-persist hash-chain as an
immutable, reproducible, tamper-evident record. The causal_taint encodes the
model version and the exact drivers that fired, so the ledger IS the
regulatory audit trail (21 CFR Part 11 §11.10(e)) — computer-generated,
ordered, and independently verifiable, with no black box in between.

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ctgov import AmendmentHistory, CtGovClient, CtGovError, classify_history
from .features import StudyFeatures, extract_features
from .ledger import AmendmentLedger, LedgerEntry
from .risk_engine import RiskAssessment, assess


@dataclass(frozen=True)
class CopilotResult:
    features: StudyFeatures
    assessment: RiskAssessment
    ledger_entry: LedgerEntry
    history: AmendmentHistory | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "features": self.features.as_dict(),
            "assessment": self.assessment.as_dict(),
            "ledger_entry": self.ledger_entry.as_dict(),
            "history": self.history.as_dict() if self.history is not None else None,
        }


class Copilot:
    def __init__(self, client: CtGovClient, ledger: AmendmentLedger) -> None:
        self.client = client
        self.ledger = ledger

    def score(self, nct_id: str, with_history: bool = True) -> CopilotResult:
        study = self.client.get_study(nct_id)
        features = extract_features(study)
        assessment = assess(features)

        history: AmendmentHistory | None = None
        if with_history:
            try:
                history = classify_history(nct_id, self.client.get_history(nct_id))
            except CtGovError:
                history = None  # history plane optional; scoring is complete without it

        # Deterministic decision payload -> hashed into the chain. No wall-clock here.
        payload: dict[str, Any] = {
            "nct_id": features.nct_id,
            "model_version": assessment.model_version,
            "mode": assessment.mode,
            "score": assessment.score,
            "tier": assessment.tier,
            "raw_score": assessment.raw_score,
            "expected_amendments": assessment.expected_amendments,
            "features": features.as_dict(),
            "fired_rules": [r.as_dict() for r in assessment.fired_rules],
            "contributions": list(assessment.contributions),
        }
        top_drivers = "+".join(
            r.driver.split()[0].lower() for r in assessment.fired_rules if r.points > 0
        ) or "none"
        # causal_taint carries the model tag so the audit trail records WHICH model decided.
        causal_taint = (
            f"apex-amendment-engine:{assessment.model_version}|"
            f"{assessment.tier.lower()}({assessment.score})|{top_drivers}"
        )

        entry = self.ledger.append(payload=payload, causal_taint=causal_taint)
        return CopilotResult(features=features, assessment=assessment, ledger_entry=entry, history=history)
