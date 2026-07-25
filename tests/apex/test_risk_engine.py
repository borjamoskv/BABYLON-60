from __future__ import annotations

from apex_trials.features import StudyFeatures
from apex_trials.risk_engine import RAW_MAX, assess


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
    return StudyFeatures(**base)  # type: ignore


def test_minimal_protocol_is_low() -> None:
    a = assess(_mk())
    assert a.score == 0 and a.tier == "LOW"


def test_contributions_sum_to_approx_score() -> None:
    a = assess(_mk(n_eligibility_criteria=25, enrollment=1200, n_countries=10))
    if a.mode == "hand-tuned" and a.contributions:
        assert abs(sum(a.contributions) - a.score) < 1.0


def test_rich_nlp_and_oversight_features() -> None:
    f = _mk(has_dmc=True, is_fda_regulated=True, brief_summary_words=350, n_conditions=4, n_interventions=3)
    assert f.has_dmc is True
    assert f.is_fda_regulated is True
    assert f.brief_summary_words == 350
    assert f.n_conditions == 4
    assert f.n_interventions == 3
    d = f.as_dict()
    assert d["has_dmc"] is True
    assert d["brief_summary_words"] == 350
    assert assess(f).score >= 0


def test_score_is_deterministic() -> None:
    f = _mk(n_eligibility_criteria=33, phase="PHASE3", is_oncology=True, enrollment=1600, n_countries=20)
    assert assess(f).as_dict() == assess(f).as_dict()


def test_eligibility_monotonic() -> None:
    scores = [assess(_mk(n_eligibility_criteria=n)).raw_score for n in (5, 15, 25, 40, 60)]
    assert scores == sorted(scores) and scores[0] == 0 and (scores[-1] == 30)


def test_complex_oncology_phase3_is_high_or_critical() -> None:
    f = _mk(
        n_eligibility_criteria=50,
        n_primary_endpoints=4,
        n_secondary_endpoints=8,
        n_arms=5,
        enrollment=2000,
        n_countries=25,
        phase="PHASE3",
        intervention_model="CROSSOVER",
        masking="QUADRUPLE",
        is_oncology=True,
        therapeutic_area="Oncology",
    )
    a = assess(f)
    assert a.tier in ("HIGH", "CRITICAL") and a.score >= 50
    assert a.raw_score <= RAW_MAX


def test_tier_boundaries() -> None:
    assert assess(_mk()).tier == "LOW"
    mod = _mk(n_eligibility_criteria=25, phase="PHASE3")
    assert mod.n_eligibility_criteria == 25
    a = assess(mod)
    assert 0 <= a.score <= 100 and a.tier in ("LOW", "MODERATE", "HIGH", "CRITICAL")


def test_every_driver_reports_a_rule() -> None:
    a = assess(_mk(n_eligibility_criteria=40))
    assert len(a.fired_rules) == 9
    elig = next(r for r in a.fired_rules if r.driver == "Eligibility complexity")
    assert elig.points == 24 and "band 31-45" in elig.rule
