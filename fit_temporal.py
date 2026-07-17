"""fit_temporal.py — P0: does the model generalize FORWARD, or only interpolate?

Splits the corpus by registration date (train ≤ CUTOFF, test > CUTOFF) and re-runs
the same pipeline as the random split, so the two are directly comparable:

  - aggregate : NNLS-band mixing + isotonic calibration → Spearman, MAE on test
  - per-module: logistic (leakage-mitigated) → ROC-AUC on test

Confound disclosed: trials registered later have had less time to accrue amendments,
so the test target mean is lower. Spearman (rank) is robust to that global shift;
calibration MAE is not, and is reported with the confound noted.

Output: temporal_report.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import nnls
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent))
from apex_trials.features import StudyFeatures  # noqa: E402
from apex_trials.risk_engine import assess  # noqa: E402

SEED = 42
CUTOFF = "2019-01-01"
_SF = set(StudyFeatures.__dataclass_fields__.keys())
RAW_FEATURES = ["n_eligibility_criteria", "n_endpoints", "n_arms", "log_enrollment",
                "n_countries", "phase_ord", "is_crossover", "is_factorial",
                "high_masking", "is_oncology", "is_rare"]
MODULES = [("elig", "Eligibility", ["n_eligibility_criteria"]),
           ("design", "Study Design", ["is_crossover", "is_factorial", "high_masking"]),
           ("outcomes", "Outcome Measures", ["n_endpoints"]),
           ("arms", "Arms and Interventions", ["n_arms"]),
           ("conditions", "Conditions", ["is_oncology", "is_rare"]),
           ("descr", "Study Description", [])]


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ar = np.argsort(np.argsort(a)).astype(float); br = np.argsort(np.argsort(b)).astype(float)
    ar -= ar.mean(); br -= br.mean()
    d = np.sqrt((ar**2).sum() * (br**2).sum())
    return float((ar * br).sum() / d) if d else 0.0


def raw_vec(sf: StudyFeatures) -> list[float]:
    phase_ord = {"EARLY_PHASE1": 1, "PHASE1": 1, "PHASE2": 2, "PHASE3": 3, "PHASE4": 1.5}.get(sf.phase, 0)
    return [sf.n_eligibility_criteria, sf.n_primary_endpoints + sf.n_secondary_endpoints,
            sf.n_arms, float(np.log1p(sf.enrollment)), sf.n_countries, phase_ord,
            float("CROSSOVER" in sf.intervention_model.upper()),
            float("FACTORIAL" in sf.intervention_model.upper()),
            float(sf.masking.upper() in ("TRIPLE", "QUADRUPLE")),
            float(sf.is_oncology), float(sf.is_rare_disease)]


def agg_eval(frac, y, tr, te):
    beta, _ = nnls(frac[tr], np.sqrt(y[tr]))
    imp = beta / beta.sum() if beta.sum() > 0 else np.ones(frac.shape[1]) / frac.shape[1]
    s_tr = 100.0 * frac[tr] @ imp
    s_te = 100.0 * frac[te] @ imp
    rho = spearman(s_te, y[te])
    iso = IsotonicRegression(out_of_bounds="clip").fit(s_tr, y[tr])
    mae = float(np.abs(iso.predict(s_te) - y[te]).mean())
    mae_base = float(np.abs(y[tr].mean() - y[te]).mean())
    return rho, mae, mae_base


def module_auc(X, ycol, drop, tr, te):
    use = [i for i, f in enumerate(RAW_FEATURES) if f not in drop]
    Xu = X[:, use]
    mu = Xu[tr].mean(axis=0); sd = Xu[tr].std(axis=0); sd[sd == 0] = 1.0
    clf = LogisticRegression(max_iter=1000).fit((Xu[tr]-mu)/sd, ycol[tr])
    if len(np.unique(ycol[te])) < 2:
        return float("nan")
    return roc_auc_score(ycol[te], clf.predict_proba((Xu[te]-mu)/sd)[:, 1])


def main() -> None:
    rows = json.loads(Path("dataset.json").read_text())
    mod_rows = {r["nct_id"]: r for r in json.loads(Path("dataset_modules.json").read_text())}
    dates = json.loads(Path("dates.json").read_text())

    frac, raw, y, when, mlabels = [], [], [], [], []
    for r in rows:
        nct = r["nct_id"]
        if nct not in dates or nct not in mod_rows:
            continue
        sf = StudyFeatures(**{k: r[k] for k in _SF})
        a = assess(sf)
        frac.append([ru.points / ru.max_points if ru.max_points else 0.0 for ru in a.fired_rules])
        raw.append(raw_vec(sf))
        y.append(r["target_substantive"])
        when.append(dates[nct])
        mr = mod_rows[nct]
        mlabels.append([mr[f"amended_{k}"] for k, _, _ in MODULES])

    frac = np.array(frac); raw = np.array(raw); y = np.array(y, float)
    when = np.array(when); M = np.array(mlabels, int)
    n = len(y)
    idx = np.arange(n)

    tmask = when < CUTOFF
    tr_t, te_t = idx[tmask], idx[~tmask]
    tr_r, te_r = train_test_split(idx, test_size=len(te_t) / n, random_state=SEED)

    print(f"n={n}  cutoff={CUTOFF}")
    print(f"  temporal:  train={len(tr_t)} (≤2018)  test={len(te_t)} (≥2019)")
    print(f"  target mean: train={y[tr_t].mean():.2f}  test={y[te_t].mean():.2f}  "
          f"(confound: newer trials, less elapsed time -> fewer amendments)")

    # aggregate
    rho_t, mae_t, base_t = agg_eval(frac, y, tr_t, te_t)
    rho_r, mae_r, base_r = agg_eval(frac, y, tr_r, te_r)
    print("\n=== AGGREGATE (Spearman ρ, higher=better) ===")
    print(f"  random split : ρ={rho_r:.3f}   MAE={mae_r:.3f} (base {base_r:.3f})")
    print(f"  TEMPORAL     : ρ={rho_t:.3f}   MAE={mae_t:.3f} (base {base_t:.3f})")
    print(f"  Δρ (temporal - random): {rho_t - rho_r:+.3f}")

    # per-module
    print("\n=== PER-MODULE ROC-AUC (temporal vs random) ===")
    print(f"{'module':<24}{'random':>9}{'temporal':>10}{'Δ':>8}")
    rand_aucs, temp_aucs = [], []
    per_mod = {}
    for j, (key, label, drop) in enumerate(MODULES):
        ar = module_auc(raw, M[:, j], drop, tr_r, te_r)
        at = module_auc(raw, M[:, j], drop, tr_t, te_t)
        rand_aucs.append(ar); temp_aucs.append(at)
        per_mod[key] = {"label": label, "auc_random": round(ar, 4), "auc_temporal": round(at, 4)}
        print(f"{label:<24}{ar:>9.3f}{at:>10.3f}{at-ar:>+8.3f}")
    print(f"{'macro':<24}{np.mean(rand_aucs):>9.3f}{np.mean(temp_aucs):>10.3f}{np.mean(temp_aucs)-np.mean(rand_aucs):>+8.3f}")

    out = {
        "cutoff": CUTOFF, "n": n, "n_train": int(len(tr_t)), "n_test": int(len(te_t)),
        "target_mean_train": round(float(y[tr_t].mean()), 3),
        "target_mean_test": round(float(y[te_t].mean()), 3),
        "aggregate": {
            "spearman_random": round(rho_r, 4), "spearman_temporal": round(rho_t, 4),
            "mae_temporal": round(mae_t, 4), "mae_base_temporal": round(base_t, 4),
        },
        "per_module": per_mod,
        "macro_auc_random": round(float(np.mean(rand_aucs)), 4),
        "macro_auc_temporal": round(float(np.mean(temp_aucs)), 4),
    }
    Path("temporal_report.json").write_text(json.dumps(out, indent=2))
    print("\nsaved -> temporal_report.json")


if __name__ == "__main__":
    main()
