from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ctgov import AmendmentHistory, CtGovClient, CtGovError, classify_history
from .features import StudyFeatures, extract_features
from .ledger import LedgerEntry
from .modules import ModuleRisk, predict_module_risks
from .risk_engine import RiskAssessment, assess


@dataclass(frozen=True)
class CopilotResult:
    features: StudyFeatures
    assessment: RiskAssessment
    ledger_entry: LedgerEntry
    history: AmendmentHistory | None
    module_risks: tuple[ModuleRisk, ...] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "features": self.features.as_dict(),
            "assessment": self.assessment.as_dict(),
            "ledger_entry": self.ledger_entry.as_dict(),
            "history": self.history.as_dict() if self.history is not None else None,
        }


class Copilot:
    def __init__(self, client: CtGovClient, ledger: Any) -> None:
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
                history = None
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

        def _sanitize(d: Any) -> Any:
            if isinstance(d, float):
                return str(d)
            if isinstance(d, dict):
                return {k: _sanitize(v) for k, v in d.items()}
            if isinstance(d, list):
                return [_sanitize(x) for x in d]
            return d

        top_drivers = "+".join(r.driver.split()[0].lower() for r in assessment.fired_rules if r.points > 0) or "none"
        causal_taint = f"apex-amendment-engine:{assessment.model_version}|{assessment.tier.lower()}({assessment.score})|{top_drivers}"
        entry = self.ledger.append(payload=_sanitize(payload), causal_taint=causal_taint)
        module_risks = predict_module_risks(features)
        return CopilotResult(
            features=features, assessment=assessment, ledger_entry=entry, history=history, module_risks=module_risks
        )
