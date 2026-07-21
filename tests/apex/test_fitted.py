"""Fitted-model path: determinism, calibration output, mode switching, weights sanity."""

from __future__ import annotations


import pytest

from apex_trials.features import StudyFeatures
from apex_trials.risk_engine import _FITTED, assess, RAW_MAX

_HAS_FITTED = _FITTED is not None


def _mk(**over: object) -> StudyFeatures:
    base = dict(
        nct_id="NCT0",
        brief_title="t",
        phase="NA",
        study_type="INTERVENTIONAL",
        n_eligibility_criteria=0,
        n_inclusion=0,
        n_exclusion=0,
        n_primary_endpoints=1,
        n_secondary_endpoints=0,
        n_arms=1,
        enrollment=0,
        n_sites=0,
        n_countries=0,
        allocation="NA",
        intervention_model="PARALLEL",
        masking="NONE",
        is_oncology=False,
        is_rare_disease=False,
        therapeutic_area="general",
    )
    base.update(over)
    return StudyFeatures(**base)  # type: ignore[arg-type]


def test_fitted_weights_are_valid_distribution() -> None:
    if not _HAS_FITTED:
        pytest.skip("no fitted_weights.json baked")
    imp = _FITTED["importances"]  # type: ignore
    assert len(imp) == 9
    assert all(w >= 0 for w in imp)  # non-negative: drivers only add risk
    assert abs(sum(imp) - 1.0) < 1e-3  # normalized (JSON stores 6-dp rounded)


def test_hand_mode_matches_raw_band_normalization() -> None:
    f = _mk(n_eligibility_criteria=40, phase="PHASE3")
    a = assess(f, mode="hand")
    assert a.mode == "hand-tuned"
    assert a.expected_amendments is None
    assert a.score == round(a.raw_score / RAW_MAX * 100)


def test_fitted_mode_is_deterministic_and_calibrated() -> None:
    if not _HAS_FITTED:
        pytest.skip("no fitted_weights.json baked")
    f = _mk(n_eligibility_criteria=50, phase="PHASE3", enrollment=2000, n_countries=25, is_oncology=True)
    a1 = assess(f, mode="fitted")
    a2 = assess(f, mode="fitted")
    assert a1.as_dict() == a2.as_dict()  # reproducible
    assert a1.mode == "fitted"
    assert 0 <= a1.score <= 100
    assert a1.expected_amendments is not None and a1.expected_amendments >= 0
    # contributions align to the 9 drivers and (rounding aside) reconstruct the score
    assert len(a1.contributions) == 9
    assert abs(sum(a1.contributions) - a1.score) <= 1.0


def test_minimal_protocol_zero_in_both_modes() -> None:
    assert assess(_mk(), mode="hand").score == 0
    assert assess(_mk(), mode="fitted").score == 0


def test_auto_uses_fitted_when_available() -> None:
    a = assess(_mk(n_eligibility_criteria=30), mode="auto")
    expected_mode = "fitted" if _HAS_FITTED else "hand-tuned"
    assert a.mode == expected_mode
