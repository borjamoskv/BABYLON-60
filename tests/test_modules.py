"""Per-module amendment-surface prediction: determinism, ranges, leakage mitigation."""
from __future__ import annotations

import pytest

from apex_trials.features import StudyFeatures
from apex_trials.modules import _MODELS, available, predict_module_risks

_HAS = available()


def _mk(**over: object) -> StudyFeatures:
    base = dict(
        nct_id="NCT0", brief_title="t", phase="PHASE3", study_type="INTERVENTIONAL",
        n_eligibility_criteria=30, n_inclusion=15, n_exclusion=15,
        n_primary_endpoints=2, n_secondary_endpoints=6, n_arms=3,
        enrollment=800, n_sites=40, n_countries=12,
        allocation="RANDOMIZED", intervention_model="PARALLEL", masking="DOUBLE",
        is_oncology=True, is_rare_disease=False, therapeutic_area="Oncology",
    )
    base.update(over)
    return StudyFeatures(**base)  # type: ignore[arg-type]


def test_models_present():
    if not _HAS:
        pytest.skip("no module_models.json baked")
    assert set(_MODELS["modules"]) == {"elig", "design", "outcomes", "arms", "conditions", "descr"}


def test_predictions_valid_and_sorted():
    if not _HAS:
        pytest.skip("no module_models.json baked")
    risks = predict_module_risks(_mk())
    assert len(risks) == 6
    assert all(0.0 <= r.probability <= 1.0 for r in risks)
    probs = [r.probability for r in risks]
    assert probs == sorted(probs, reverse=True)          # ranked high -> low


def test_deterministic():
    if not _HAS:
        pytest.skip("no module_models.json baked")
    a = [r.as_dict() for r in predict_module_risks(_mk())]
    b = [r.as_dict() for r in predict_module_risks(_mk())]
    assert a == b


def test_leakage_mitigation_drops_self_features():
    if not _HAS:
        pytest.skip("no module_models.json baked")
    mods = _MODELS["modules"]
    assert "n_eligibility_criteria" not in mods["elig"]["used_features"]
    assert "n_endpoints" not in mods["outcomes"]["used_features"]
    assert "n_arms" not in mods["arms"]["used_features"]
    for f in ("is_crossover", "is_factorial", "high_masking"):
        assert f not in mods["design"]["used_features"]
    for f in ("is_oncology", "is_rare"):
        assert f not in mods["conditions"]["used_features"]


def test_models_beat_chance_on_record():
    if not _HAS:
        pytest.skip("no module_models.json baked")
    for m in _MODELS["modules"].values():
        assert m["auc"] > 0.55            # every module carries real held-out signal


def test_no_models_returns_empty(monkeypatch):
    import apex_trials.modules as mod
    monkeypatch.setattr(mod, "_MODELS", None)
    assert mod.predict_module_risks(_mk()) == ()
