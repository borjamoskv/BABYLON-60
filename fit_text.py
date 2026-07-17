"""fit_text.py — does protocol TEXT improve FORWARD generalization?

Compares structured-only vs structured+TF-IDF on the TEMPORAL split (train ≤2018,
test ≥2019). The TF-IDF vocabulary is fit on TRAIN text only (no vocab leakage).
Both arms share the same final-record text leakage regime, so the DELTA (text's
incremental lift on the temporal test) is a fair, honest measure of text value.

  per-module : ROC-AUC, structured vs structured+text (temporal test)
  aggregate  : Spearman of predicted vs actual count (Ridge on sqrt target)

Output: text_report.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).parent))
from apex_trials.features import StudyFeatures  # noqa: E402

CUTOFF = "2019-01-01"
_SF = set(StudyFeatures.__dataclass_fields__.keys())
RAW = ["n_eligibility_criteria", "n_endpoints", "n_arms", "log_enrollment", "n_countries",
       "phase_ord", "is_crossover", "is_factorial", "high_masking", "is_oncology", "is_rare"]
MODULES = [("elig", "Eligibility", ["n_eligibility_criteria"]),
           ("design", "Study Design", ["is_crossover", "is_factorial", "high_masking"]),
           ("outcomes", "Outcome Measures", ["n_endpoints"]),
           ("arms", "Arms and Interventions", ["n_arms"]),
           ("conditions", "Conditions", ["is_oncology", "is_rare"]),
           ("descr", "Study Description", [])]


def spearman(a, b) -> float:
    ar = np.argsort(np.argsort(a)).astype(float)
    br = np.argsort(np.argsort(b)).astype(float)
    ar -= ar.mean()
    br -= br.mean()
    d = np.sqrt((ar**2).sum() * (br**2).sum())
    return float((ar * br).sum() / d) if d else 0.0


def raw_vec(sf: StudyFeatures):
    po = {"EARLY_PHASE1": 1, "PHASE1": 1, "PHASE2": 2, "PHASE3": 3, "PHASE4": 1.5}.get(sf.phase, 0)
    return [sf.n_eligibility_criteria, sf.n_primary_endpoints + sf.n_secondary_endpoints, sf.n_arms,
            float(np.log1p(sf.enrollment)), sf.n_countries, po,
            float("CROSSOVER" in sf.intervention_model.upper()),
            float("FACTORIAL" in sf.intervention_model.upper()),
            float(sf.masking.upper() in ("TRIPLE", "QUADRUPLE")),
            float(sf.is_oncology), float(sf.is_rare_disease)]


def main() -> None:
    rows = json.loads(Path("dataset.json").read_text())
    mods = {r["nct_id"]: r for r in json.loads(Path("dataset_modules.json").read_text())}
    dates = json.loads(Path("dates.json").read_text())
    texts = json.loads(Path("texts.json").read_text())

    X_list, y_list, when_list, corpus_list, M_list = [], [], [], [], []
    for r in rows:
        nct = r["nct_id"]
        if nct not in dates or nct not in mods or nct not in texts:
            continue
        sf = StudyFeatures(**{k: r[k] for k in _SF})
        X_list.append(raw_vec(sf))
        y_list.append(r["target_substantive"])
        when_list.append(dates[nct])
        t = texts[nct]
        corpus_list.append((t.get("elig", "") + " " + t.get("brief", "")).strip())
        M_list.append([mods[nct][f"amended_{k}"] for k, _, _ in MODULES])

    X = np.array(X_list, float)
    y = np.array(y_list, float)
    when = np.array(when_list)
    M = np.array(M_list, int)
    corpus = np.array(corpus_list, dtype=object)
    n = len(y)
    idx = np.arange(n)
    tr, te = idx[when < CUTOFF], idx[when >= CUTOFF]
    print(f"n={n}  temporal train={len(tr)} (≤2018)  test={len(te)} (≥2019)")

    # TF-IDF vocab fit on TRAIN only
    vec = TfidfVectorizer(max_features=800, stop_words="english", ngram_range=(1, 2),
                          min_df=5, sublinear_tf=True)
    Ttr = vec.fit_transform(corpus[tr].tolist())
    Tte = vec.transform(corpus[te].tolist())
    print(f"TF-IDF vocab (train-fit): {len(vec.vocabulary_)} terms")

    def std(cols, tr_i, te_i):
        mu = cols[tr_i].mean(axis=0)
        sd = cols[tr_i].std(axis=0)
        sd[sd == 0] = 1.0
        return (cols[tr_i]-mu)/sd, (cols[te_i]-mu)/sd

    print("\n=== PER-MODULE ROC-AUC (temporal test): structured vs +text ===")
    print(f"{'module':<24}{'struct':>9}{'+text':>9}{'Δ':>8}")
    rep = {}
    ds, dt = [], []
    for j, (key, label, drop) in enumerate(MODULES):
        use = [i for i, f in enumerate(RAW) if f not in drop]
        Xs_tr, Xs_te = std(X[:, use], tr, te)
        ycol = M[:, j]
        if len(np.unique(ycol[te])) < 2:
            continue
        a_s = roc_auc_score(ycol[te], LogisticRegression(max_iter=1000).fit(Xs_tr, ycol[tr]).predict_proba(Xs_te)[:, 1])
        Xc_tr = hstack([csr_matrix(Xs_tr), Ttr]).tocsr()
        Xc_te = hstack([csr_matrix(Xs_te), Tte]).tocsr()
        a_c = roc_auc_score(ycol[te], LogisticRegression(max_iter=1000).fit(Xc_tr, ycol[tr]).predict_proba(Xc_te)[:, 1])
        rep[key] = {"label": label, "auc_struct": round(a_s, 4), "auc_text": round(a_c, 4), "delta": round(a_c-a_s, 4)}
        ds.append(a_s)
        dt.append(a_c)
        print(f"{label:<24}{a_s:>9.3f}{a_c:>9.3f}{a_c-a_s:>+8.3f}")
    print(f"{'macro':<24}{np.mean(ds):>9.3f}{np.mean(dt):>9.3f}{np.mean(dt)-np.mean(ds):>+8.3f}")

    # aggregate count: Ridge on sqrt target, Spearman on temporal test
    Xs_tr, Xs_te = std(X, tr, te)
    yt = np.sqrt(y)
    rho_s = spearman(Ridge(alpha=1.0).fit(Xs_tr, yt[tr]).predict(Xs_te), y[te])
    Xc_tr = hstack([csr_matrix(Xs_tr), Ttr]).tocsr()
    Xc_te = hstack([csr_matrix(Xs_te), Tte]).tocsr()
    rho_c = spearman(Ridge(alpha=1.0).fit(Xc_tr, yt[tr]).predict(Xc_te), y[te])
    print("\n=== AGGREGATE count Spearman (temporal test) ===")
    print(f"  structured : {rho_s:.3f}")
    print(f"  +text      : {rho_c:.3f}   (Δ {rho_c-rho_s:+.3f})")

    out = {"cutoff": CUTOFF, "n_train": int(len(tr)), "n_test": int(len(te)),
           "tfidf_terms": len(vec.vocabulary_),
           "per_module": rep,
           "macro_auc_struct": round(float(np.mean(ds)), 4),
           "macro_auc_text": round(float(np.mean(dt)), 4),
           "aggregate_spearman_struct": round(rho_s, 4),
           "aggregate_spearman_text": round(rho_c, 4)}
    Path("text_report.json").write_text(json.dumps(out, indent=2))
    print("\nsaved -> text_report.json")


if __name__ == "__main__":
    main()
