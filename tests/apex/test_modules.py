from __future__ import annotations

import pytest

from apex_trials.features import StudyFeatures
from apex_trials.modules import _MODELS, available, predict_module_risks

_HAS = available()


def _mk(**over: object) -> StudyFeatures:
    base = dict(
        nct_id="NCT0",
        brief_title="t",
        phase="PHASE3",
        study_type="INTERVENTIONAL",
        n_eligibility_criteria=30,
        n_inclusion=15,
        n_exclusion=15,
        n_primary_endpoints=2,
        n_secondary_endpoints=6,
        n_arms=3,
        enrollment=800,
        n_sites=40,
        n_countries=12,
        allocation="RANDOMIZED",
        intervention_model="PARALLEL",
        masking="DOUBLE",
        is_oncology=True,
        is_rare_disease=False,
        therapeutic_area="Oncology",
    )
    base.update(over)
    return StudyFeatures(**base)  # type: ignore


def test_models_present() -> None:
    if not _HAS:
        pytest.skip("no module_models.json baked")
    assert set(_MODELS["modules"]) == {"elig", "design", "outcomes", "arms", "conditions", "descr"}  # type: ignore


def test_predictions_valid_and_sorted() -> None:
    if not _HAS:
        pytest.skip("no module_models.json baked")
    risks = predict_module_risks(_mk())
    assert len(risks) == 6
    assert all(0.0 <= r.probability <= 1.0 for r in risks)
    probs = [r.probability for r in risks]
    assert probs == sorted(probs, reverse=True)


def test_deterministic() -> None:
    if not _HAS:
        pytest.skip("no module_models.json baked")
    a = [r.as_dict() for r in predict_module_risks(_mk())]
    b = [r.as_dict() for r in predict_module_risks(_mk())]
    assert a == b


def test_leakage_mitigation_drops_self_features() -> None:
    if not _HAS:
        pytest.skip("no module_models.json baked")
    mods = _MODELS["modules"]  # type: ignore
    assert "n_eligibility_criteria" not in mods["elig"]["used_features"]
    assert "n_endpoints" not in mods["outcomes"]["used_features"]
    assert "n_arms" not in mods["arms"]["used_features"]
    for f in ("is_crossover", "is_factorial", "high_masking"):
        assert f not in mods["design"]["used_features"]
    for f in ("is_oncology", "is_rare"):
        assert f not in mods["conditions"]["used_features"]


def test_models_beat_chance_on_record() -> None:
    if not _HAS:
        pytest.skip("no module_models.json baked")
    for m in _MODELS["modules"].values():  # type: ignore
        assert m["auc"] > 0.55


def test_no_models_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    import apex_trials.modules as mod

    monkeypatch.setattr(mod, "_MODELS", None)
    assert mod.predict_module_risks(_mk()) == ()


def test_text_features_inference() -> None:
    if not _HAS:
        pytest.skip("no module_models.json baked")
    r_no_text = predict_module_risks(_mk())
    r_text_1 = predict_module_risks(
        _mk(), eligibility_text="Patient must have cancer.", brief_summary_text="Oncology trial."
    )
    r_text_2 = predict_module_risks(
        _mk(), eligibility_text="Patient must have cancer.", brief_summary_text="Oncology trial."
    )
    assert len(r_text_1) == 6
    assert [r.as_dict() for r in r_text_1] == [r.as_dict() for r in r_text_2]
    assert [r.probability for r in r_no_text] != [r.probability for r in r_text_1]


def test_tfidf_pure_sklearn_equivalence() -> None:
    if not _HAS:
        pytest.skip("no module_models.json baked")
    pytest.importorskip(
        "sklearn",
        reason="sklearn no instalado — solo es oráculo de referencia para esta prueba, no una dependencia de runtime de apex_trials",
    )
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer

    from apex_trials.modules import _transform_pure

    elig_model = _MODELS["modules"]["elig"]  # type: ignore
    vocab = elig_model["tfidf_vocab"]
    idf = elig_model["tfidf_idf"]
    sample_text = "This is a brief summary of a clinical trial for rare disease, focusing on oncology patients."
    vec_pure = _transform_pure(sample_text, vocab, idf)
    vec_sk = TfidfVectorizer(vocabulary=vocab, stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    vec_sk.idf_ = np.array(idf)
    X_sk = vec_sk.transform([sample_text]).toarray()[0]
    diff = np.abs(np.array(vec_pure) - X_sk)
    assert np.max(diff) < 1e-09, f"Pure TF-IDF mismatch with sklearn: max diff {np.max(diff)}"
