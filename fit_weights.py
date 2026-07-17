"""fit_weights.py — learn per-driver mixing weights from ground-truth amendments.

Approach (interpretable + deterministic):
  - Features = each driver's band FRACTION in [0,1] (points / max) from the existing
    transparent engine. We do NOT relearn the thresholds, only how the 8 drivers mix.
  - Target   = actual substantive amendment count (public ground-truth).
  - Fit      = non-negative least squares (NNLS) on a variance-stabilized target,
               so every driver can only ADD risk (keeps the "more complexity = more
               risk" contract). Coefficients normalized to importances that sum to 1.
  - Score    = 100 * Σ importance_i * fraction_i   (drop-in for the hand-tuned score).
  - Calibrate= isotonic map score -> expected substantive amendments (monotone).

Honesty: fit on TRAIN only, all metrics reported on a held-out TEST split, plus
5-fold CV. A Poisson GLM on raw features is fit purely as a ceiling comparison.

Output: fitted_weights.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import nnls
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import PoissonRegressor
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from apex_trials.features import StudyFeatures  # noqa: E402
from apex_trials.risk_engine import assess  # noqa: E402

SEED = 42
DRIVER_NAMES = [
    "Eligibility complexity", "Endpoint burden", "Arm multiplicity", "Enrollment scale",
    "Geographic spread", "Phase baseline", "Design complexity", "Therapeutic-area baseline",
    "Site feasibility",
]
_SF_FIELDS = set(StudyFeatures.__dataclass_fields__.keys())


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ar = np.argsort(np.argsort(a)).astype(float)
    br = np.argsort(np.argsort(b)).astype(float)
    ar -= ar.mean()
    br -= br.mean()
    denom = np.sqrt((ar**2).sum() * (br**2).sum())
    return float((ar * br).sum() / denom) if denom else 0.0


def load() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rows = json.loads(Path("dataset.json").read_text())
    frac, raw, hand, y = [], [], [], []
    for r in rows:
        sf = StudyFeatures(**{k: r[k] for k in _SF_FIELDS if k in r})
        a = assess(sf, mode="hand")
        fr = [rule.points / rule.max_points if rule.max_points else 0.0 for rule in a.fired_rules]
        frac.append(fr)
        hand.append(a.score)
        phase_ord = {"EARLY_PHASE1": 1, "PHASE1": 1, "PHASE2": 2, "PHASE3": 3, "PHASE4": 1.5}.get(sf.phase, 0)
        raw.append([
            sf.n_eligibility_criteria, sf.n_primary_endpoints + sf.n_secondary_endpoints,
            sf.n_arms, np.log1p(sf.enrollment), sf.n_countries, phase_ord,
            float("CROSSOVER" in sf.intervention_model.upper()),
            float("FACTORIAL" in sf.intervention_model.upper()),
            float(sf.masking.upper() in ("TRIPLE", "QUADRUPLE")),
            float(sf.is_oncology), float(sf.is_rare_disease),
            sf.enrollment_velocity,
        ])
        y.append(r["target_substantive"])
    return np.array(frac), np.array(raw), np.array(hand, float), np.array(y, float)


def main() -> None:
    frac, raw, hand, y = load()
    n = len(y)
    idx = np.arange(n)
    tr, te = train_test_split(idx, test_size=0.25, random_state=SEED)
    print(f"dataset n={n}  train={len(tr)}  test={len(te)}  mean_target={y.mean():.2f}")

    # --- NNLS on band fractions (variance-stabilized target) --------------------
    yt = np.sqrt(y)  # stabilize count variance
    beta, _ = nnls(frac[tr], yt[tr])
    importances = beta / beta.sum() if beta.sum() > 0 else np.ones(len(beta)) / len(beta)
    fitted_score_te = 100.0 * frac[te] @ importances
    fitted_score_tr = 100.0 * frac[tr] @ importances

    rho_hand = spearman(hand[te], y[te])
    rho_fit = spearman(fitted_score_te, y[te])

    # --- 5-fold CV for the NNLS-band model --------------------------------------
    cv = KFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_scores = []
    for f_tr, f_te in cv.split(frac):
        b, _ = nnls(frac[f_tr], yt[f_tr])
        imp = b / b.sum() if b.sum() > 0 else np.ones(len(b)) / len(b)
        cv_scores.append(spearman(100.0 * frac[f_te] @ imp, y[f_te]))
    cv_scores_arr = np.array(cv_scores)

    # --- Poisson GLM on raw features (ceiling comparison) -----------------------
    sc = StandardScaler().fit(raw[tr])
    pois = PoissonRegressor(alpha=1e-3, max_iter=500).fit(sc.transform(raw[tr]), y[tr])
    rho_pois = spearman(pois.predict(sc.transform(raw[te])), y[te])

    # --- Isotonic calibration: fitted score -> expected substantive amendments ---
    iso = IsotonicRegression(out_of_bounds="clip").fit(fitted_score_tr, y[tr])
    pred_te = iso.predict(fitted_score_te)
    mae_fit = float(np.abs(pred_te - y[te]).mean())
    mae_base = float(np.abs(y[tr].mean() - y[te]).mean())
    # isotonic knots (compact) for portable calibration
    xs = np.linspace(0, 100, 21)
    iso_curve = [[float(x), float(iso.predict([x])[0])] for x in xs]

    print("\n=== HELD-OUT TEST (n={}) ===".format(len(te)))
    print(f"  Spearman  hand-tuned prior : {rho_hand:.3f}")
    print(f"  Spearman  NNLS-band fitted : {rho_fit:.3f}   (Δ {rho_fit-rho_hand:+.3f})")
    print(f"  Spearman  Poisson raw (ceil): {rho_pois:.3f}")
    print(f"  CV Spearman NNLS-band      : {cv_scores_arr.mean():.3f} ± {cv_scores_arr.std():.3f}")
    print(f"  Isotonic MAE (amendments)  : {mae_fit:.3f}  vs predict-mean {mae_base:.3f}  "
          f"({100*(mae_base-mae_fit)/mae_base:+.1f}%)")

    print("\n=== LEARNED DRIVER IMPORTANCES (NNLS, sum=1) ===")
    order = np.argsort(-importances)
    for i in order:
        print(f"  {DRIVER_NAMES[i]:<28} {importances[i]:.3f}")

    temporal_metrics = {}
    temporal_report_path = Path("temporal_report.json")
    if temporal_report_path.exists():
        try:
            tr_data = json.loads(temporal_report_path.read_text(encoding="utf-8"))
            agg_t = tr_data.get("aggregate", {})
            temporal_metrics = {
                "temporal_cutoff": tr_data.get("cutoff", "2019-01-01"),
                "spearman_temporal": agg_t.get("spearman_temporal", 0.0),
                "mae_temporal": agg_t.get("mae_temporal", 0.0),
                "mae_base_temporal": agg_t.get("mae_base_temporal", 0.0),
                "macro_auc_temporal": tr_data.get("macro_auc_temporal", 0.0),
                "macro_auc_random": tr_data.get("macro_auc_random", 0.0),
            }
        except Exception:
            pass

    out = {
        "model_version": "apex-amendment-risk/2.0.0-fitted",
        "seed": SEED,
        "n_total": n, "n_train": int(len(tr)), "n_test": int(len(te)),
        "driver_order": DRIVER_NAMES,
        "importances": [round(float(x), 6) for x in importances],
        "isotonic_curve": iso_curve,
        "metrics": {
            "spearman_hand": round(rho_hand, 4),
            "spearman_fitted": round(rho_fit, 4),
            "spearman_poisson_raw": round(rho_pois, 4),
            "cv_spearman_mean": round(float(cv_scores_arr.mean()), 4),
            "cv_spearman_std": round(float(cv_scores_arr.std()), 4),
            "isotonic_mae": round(mae_fit, 4),
            "baseline_mae": round(mae_base, 4),
            **temporal_metrics
        },
    }
    Path("fitted_weights.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    pkg_path = Path("apex_trials/fitted_weights.json")
    if pkg_path.parent.exists():
        pkg_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\nsaved -> fitted_weights.json and apex_trials/fitted_weights.json")


if __name__ == "__main__":
    main()
