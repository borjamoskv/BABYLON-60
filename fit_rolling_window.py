"""fit_rolling_window.py — C5-REAL rolling-window cross-validation for temporal drift.

Simulates production deployment:
For each year Y from 2017 to 2023:
  1. Train on all records completed <= Y
  2. Test on records completed in Y+1
  3. Record Spearman ρ and macro-AUC.

Demonstrates that continuous re-fitting bounds the temporal degradation
observed in the static temporal split (which degrades indefinitely).

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from fit_module_models import FEATURES, MODULES, row_features
from fit_temporal import spearman


def agg_eval(frac_arr: np.ndarray, y_arr: np.ndarray, tr_arr: np.ndarray, te_arr: np.ndarray) -> tuple[float, float, float]:
    from sklearn.metrics import roc_auc_score
    if len(np.unique(y_arr[tr_arr])) < 2 or len(np.unique(y_arr[te_arr])) < 2:
        return 0.5, 0.5, 0.5
    clf = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    clf.fit(frac_arr[tr_arr].reshape(-1, 1), y_arr[tr_arr])
    p_te = clf.predict_proba(frac_arr[te_arr].reshape(-1, 1))[:, 1]
    auc_te = roc_auc_score(y_arr[te_arr], p_te)
    return float(auc_te), float(auc_te), float(auc_te)


def main() -> None:
    ds_path = Path("dataset.json")
    dm_path = Path("dataset_modules.json")

    if not ds_path.exists() or not dm_path.exists():
        print("Missing dataset.json or dataset_modules.json")
        return

    rows = json.loads(ds_path.read_text())
    mod_rows = json.loads(dm_path.read_text())
    
    dates_path = Path("dates.json")
    if not dates_path.exists():
        print("Missing dates.json")
        return
    dates = json.loads(dates_path.read_text())

    # Parse dates and match modules
    nct_to_year: dict[str, int] = {}
    for nct, dt_str in dates.items():
        if dt_str:
            try:
                # dt_str format like '2015-08-31'
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
                nct_to_year[nct] = dt.year
            except ValueError:
                pass

    print(f"Loaded {len(nct_to_year)} studies with valid dates.")

    # Convert mod_rows to arrays
    X_list: list[list[float]] = []
    Y_matrix: list[list[float]] = []
    years: list[int] = []
    target_subs: list[int] = []

    valid_ncts = set()
    mod_by_nct: dict[str, dict] = {mr["nct_id"]: mr for mr in mod_rows}

    for r in rows:
        nct = r["nct_id"]
        if nct not in nct_to_year or nct not in mod_by_nct:
            continue
        mr = mod_by_nct[nct]

        # Extract features
        x_vec = row_features(r)
        
        # Extract binary targets for the 6 modules
        y_vec = []
        for mod_key, _, _ in MODULES:
            y_vec.append(float(mr[f"amended_{mod_key}"]))

        X_list.append(x_vec)
        Y_matrix.append(y_vec)
        years.append(nct_to_year[nct])
        target_subs.append(r.get("target_substantive", 0))
        valid_ncts.add(nct)

    X = np.array(X_list, dtype=float)
    Y = np.array(Y_matrix, dtype=float)
    Y_years = np.array(years, dtype=int)
    Y_subs = np.array(target_subs, dtype=int)

    n = len(valid_ncts)
    print(f"Matrix shape: X={X.shape}, Y={Y.shape}")

    # Rolling window evaluation: Y_train <= y, Y_test == y + 1
    # We will test on years 2016 through 2023
    test_years = sorted(list(set(Y_years)))
    test_years = [y for y in test_years if y >= 2016 and y <= 2024]

    print("\n=== ROLLING WINDOW EVALUATION ===")
    print("Year | N_Train | N_Test | Spearman ρ | Macro-AUC | MAE")
    print("-" * 60)

    overall_preds = np.zeros(n)
    overall_test_mask = np.zeros(n, dtype=bool)

    for ty in test_years:
        tr_mask = (Y_years < ty)
        te_mask = (Y_years == ty)

        n_tr = tr_mask.sum()
        n_te = te_mask.sum()
        if n_tr < 100 or n_te < 10:
            continue

        # Fit isotonic models per module
        te_preds_mod = np.zeros((n_te, len(MODULES)))
        mod_aucs = []

        for i, (mod_key, _, drop_feats) in enumerate(MODULES):
            # Drop features logic
            use_idx = [j for j, feat in enumerate(FEATURES) if feat not in drop_feats]
            if not use_idx:
                continue

            X_mod = X[:, use_idx]
            y_mod = Y[:, i]

            # Fit logistic base model
            clf = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
            clf.fit(X_mod[tr_mask], y_mod[tr_mask])
            p_base_tr = clf.predict_proba(X_mod[tr_mask])[:, 1]
            p_base_te = clf.predict_proba(X_mod[te_mask])[:, 1]

            # Isotonic calibration
            iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip")
            iso.fit(p_base_tr, y_mod[tr_mask])
            p_cal_te = iso.predict(p_base_te)
            
            te_preds_mod[:, i] = p_cal_te
            
            # Eval AUC
            from sklearn.metrics import roc_auc_score
            if len(np.unique(y_mod[te_mask])) > 1:
                auc = roc_auc_score(y_mod[te_mask], p_cal_te)
                mod_aucs.append(auc)

        macro_auc = np.mean(mod_aucs) if mod_aucs else 0.5
        
        # Aggregate prediction for N_substantive
        te_agg_preds = np.sum(te_preds_mod, axis=1) * 1.5  # scalar multiplier for absolute scale
        overall_preds[te_mask] = te_agg_preds
        overall_test_mask |= te_mask
        
        rho = spearman(te_agg_preds, Y_subs[te_mask])
        mae = np.mean(np.abs(te_agg_preds - Y_subs[te_mask]))
        
        print(f"{ty} | {n_tr:7d} | {n_te:6d} | {rho:10.3f} | {macro_auc:9.3f} | {mae:5.3f}")

    # Calculate overall metrics across all rolling windows
    final_rho = spearman(overall_preds[overall_test_mask], Y_subs[overall_test_mask])
    final_mae = np.mean(np.abs(overall_preds[overall_test_mask] - Y_subs[overall_test_mask]))
    
    print("-" * 60)
    print("ROLLING WINDOW AGGREGATE (Across all tested years):")
    print(f"  Spearman ρ : {final_rho:.3f}")
    print(f"  MAE        : {final_mae:.3f}")

if __name__ == "__main__":
    main()
