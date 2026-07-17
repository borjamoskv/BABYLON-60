"""apex_trials.modules — deterministic per-module amendment-surface prediction.

Loads the baked logistic models (module_models.json, produced by fit_module_models.py)
and predicts, for each substantive protocol module, the probability it will be amended.
Inference is a plain standardize + sigmoid — no sklearn/numpy needed at runtime, fully
deterministic (same protocol -> same probabilities, byte-for-byte).

Each model is leakage-mitigated: it excludes the feature derived from its own module.

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .features import StudyFeatures

_MODELS_PATH = Path(__file__).with_name("module_models.json")


def _load() -> dict[str, Any] | None:
    if _MODELS_PATH.exists():
        return json.loads(_MODELS_PATH.read_text(encoding="utf-8"))
    return None


_MODELS: dict[str, Any] | None = _load()


@dataclass(frozen=True)
class ModuleRisk:
    module: str          # short key, e.g. "elig"
    label: str           # e.g. "Eligibility"
    probability: float   # P(module amended), 0..1
    base_rate: float     # corpus prevalence
    lift: float          # probability / base_rate

    def as_dict(self) -> dict[str, Any]:
        return {
            "module": self.module, "label": self.label,
            "probability": self.probability, "base_rate": self.base_rate, "lift": self.lift,
        }


def _feature_map(f: StudyFeatures) -> dict[str, float]:
    phase_ord = {"EARLY_PHASE1": 1, "PHASE1": 1, "PHASE2": 2, "PHASE3": 3, "PHASE4": 1.5}.get(f.phase, 0)
    return {
        "n_eligibility_criteria": float(f.n_eligibility_criteria),
        "n_endpoints": float(f.n_primary_endpoints + f.n_secondary_endpoints),
        "n_arms": float(f.n_arms),
        "log_enrollment": math.log1p(f.enrollment),
        "n_countries": float(f.n_countries),
        "phase_ord": float(phase_ord),
        "is_crossover": 1.0 if "CROSSOVER" in f.intervention_model.upper() else 0.0,
        "is_factorial": 1.0 if "FACTORIAL" in f.intervention_model.upper() else 0.0,
        "high_masking": 1.0 if f.masking.upper() in ("TRIPLE", "QUADRUPLE") else 0.0,
        "is_oncology": 1.0 if f.is_oncology else 0.0,
        "is_rare": 1.0 if f.is_rare_disease else 0.0,
    }


def available() -> bool:
    return _MODELS is not None


def model_version() -> str | None:
    return _MODELS["model_version"] if _MODELS is not None else None


def predict_module_risks(features: StudyFeatures) -> tuple[ModuleRisk, ...]:
    """Per-module P(amendment), sorted high->low. Empty tuple if models absent."""
    if _MODELS is None:
        return ()
    fmap = _feature_map(features)
    risks: list[ModuleRisk] = []
    for key, m in _MODELS["modules"].items():
        used = m["used_features"]
        mean, std, coef = m["mean"], m["std"], m["coef"]
        logit = float(m["intercept"])
        for i, feat in enumerate(used):
            z = (fmap[feat] - mean[i]) / (std[i] if std[i] else 1.0)
            logit += coef[i] * z
        p = 1.0 / (1.0 + math.exp(-logit))
        base = float(m["base_rate"])
        risks.append(ModuleRisk(
            module=key, label=m["label"],
            probability=round(p, 4), base_rate=round(base, 4),
            lift=round(p / base, 3) if base > 0 else 0.0,
        ))
    risks.sort(key=lambda r: r.probability, reverse=True)
    return tuple(risks)
