"""fit_module_models.py — per-module amendment classifiers (structured + TF-IDF text features).

Trains one logistic regression model per substantive module to predict P(module will be amended).
Uses 11 structured design features plus TF-IDF features from eligibility criteria and brief summary text.
Each target drops its self-referential structured feature(s) to prevent leakage:
  Eligibility            -> drop n_eligibility_criteria
  Outcome Measures       -> drop n_endpoints
  Arms and Interventions -> drop n_arms
  Study Design           -> drop crossover/factorial/high_masking flags
  Conditions             -> drop is_oncology/is_rare
  Study Description      -> (keep all)

Features are fiteed on 75% train, metrics evaluated on 25% held-out.
TF-IDF vocabulary is fiteed only on train text (no vocabulary leakage).
Exports standardized coefficients, intercept, TF-IDF vocabulary, and IDF weights to module_models.json
for deterministic, dependency-free inference at runtime (Option B: pure Python TF-IDF).

Output: module_models.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, str(Path(__file__).parent))
from apex_trials.features import StudyFeatures  # noqa: E402

SEED = 42
FEATURES = ["n_eligibility_criteria", "n_endpoints", "n_arms", "log_enrollment",
            "n_countries", "phase_ord", "is_crossover", "is_factorial",
            "high_masking", "is_oncology", "is_rare"]
MODULES = [
    ("elig", "Eligibility", ["n_eligibility_criteria"]),
    ("design", "Study Design", ["is_crossover", "is_factorial", "high_masking"]),
    ("outcomes", "Outcome Measures", ["n_endpoints"]),
    ("arms", "Arms and Interventions", ["n_arms"]),
    ("conditions", "Conditions", ["is_oncology", "is_rare"]),
    ("descr", "Study Description", []),
]
_SF = set(StudyFeatures.__dataclass_fields__.keys())


def row_features(r: dict) -> list[float]:
    sf = StudyFeatures(**{k: r[k] for k in _SF if k in r})
    phase_ord = {"EARLY_PHASE1": 1, "PHASE1": 1, "PHASE2": 2, "PHASE3": 3, "PHASE4": 1.5}.get(sf.phase, 0)
    return [
        sf.n_eligibility_criteria, sf.n_primary_endpoints + sf.n_secondary_endpoints,
        sf.n_arms, float(np.log1p(sf.enrollment)), sf.n_countries, phase_ord,
        float("CROSSOVER" in sf.intervention_model.upper()),
        float("FACTORIAL" in sf.intervention_model.upper()),
        float(sf.masking.upper() in ("TRIPLE", "QUADRUPLE")),
        float(sf.is_oncology), float(sf.is_rare_disease),
    ]


def main() -> None:
    rows = json.loads(Path("dataset_modules.json").read_text())
    texts = json.loads(Path("texts.json").read_text())
    
    # Extract structured features and text corpus
    X = np.array([row_features(r) for r in rows], dtype=float)
    corpus_list = []
    for r in rows:
        nct = r["nct_id"]
        t = texts.get(nct, {})
        corpus_list.append((t.get("elig", "") + " " + t.get("brief", "")).strip())
    corpus = np.array(corpus_list, dtype=object)
    
    n = len(rows)
    idx_all = np.arange(n)

    models: dict[str, dict] = {}
    print(f"n={n}  structured_features={len(FEATURES)}\n")
    print(f"{'module':<24}{'base':>7}{'AUC':>8}{'PR-AUC':>8}{'CV-AUC':>9}")
    
    for key, label, drop in MODULES:
        y = np.array([r[f"amended_{key}"] for r in rows], dtype=int)
        use_idx = [i for i, f in enumerate(FEATURES) if f not in drop]
        Xu = X[:, use_idx]

        tr, te = train_test_split(idx_all, test_size=0.25, random_state=SEED, stratify=y)
        
        # Standardize structured features
        mu = Xu[tr].mean(axis=0)
        sd = Xu[tr].std(axis=0)
        sd[sd == 0] = 1.0
        Ztr = (Xu[tr] - mu) / sd
        Zte = (Xu[te] - mu) / sd

        # Fit TF-IDF on train set only (to avoid leakage)
        vec = TfidfVectorizer(max_features=800, stop_words="english", ngram_range=(1, 2),
                              min_df=5, sublinear_tf=True)
        Ttr = vec.fit_transform(corpus[tr].tolist())
        Tte = vec.transform(corpus[te].tolist())

        # Combine structured + text
        Ztr_comb = hstack([csr_matrix(Ztr), Ttr]).tocsr()
        Zte_comb = hstack([csr_matrix(Zte), Tte]).tocsr()

        clf = LogisticRegression(max_iter=1000, C=1.0).fit(Ztr_comb, y[tr])
        p_te = clf.predict_proba(Zte_comb)[:, 1]
        auc = roc_auc_score(y[te], p_te)
        pr = average_precision_score(y[te], p_te)
        base = float(y.mean())

        # Stratified 5-Fold Cross Validation (with nested TF-IDF fitting to prevent fold leaks)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        cv_aucs = []
        for f_tr, f_te in cv.split(Xu, y):
            m2 = Xu[f_tr].mean(axis=0)
            s2 = Xu[f_tr].std(axis=0)
            s2[s2 == 0] = 1.0
            Ztr_cv = (Xu[f_tr] - m2) / s2
            Zte_cv = (Xu[f_te] - m2) / s2

            vec_cv = TfidfVectorizer(max_features=800, stop_words="english", ngram_range=(1, 2),
                                  min_df=5, sublinear_tf=True)
            Ttr_cv = vec_cv.fit_transform(corpus[f_tr].tolist())
            Tte_cv = vec_cv.transform(corpus[f_te].tolist())

            Ztr_cv_comb = hstack([csr_matrix(Ztr_cv), Ttr_cv]).tocsr()
            Zte_cv_comb = hstack([csr_matrix(Zte_cv), Tte_cv]).tocsr()

            c2 = LogisticRegression(max_iter=1000, C=1.0).fit(Ztr_cv_comb, y[f_tr])
            cv_aucs.append(roc_auc_score(y[f_te], c2.predict_proba(Zte_cv_comb)[:, 1]))
        cv_auc = float(np.mean(cv_aucs))

        print(f"{label:<24}{base:>7.3f}{auc:>8.3f}{pr:>8.3f}{cv_auc:>9.3f}")
        
        # Split coefficients back into structured and text components
        n_struct = len(use_idx)
        coef_struct = [round(float(x), 6) for x in clf.coef_[0][:n_struct]]
        coef_text = [round(float(x), 6) for x in clf.coef_[0][n_struct:]]
        
        # Convert TF-IDF vocab keys and values to standard python types
        vocab_native = {str(k): int(v) for k, v in vec.vocabulary_.items()}
        idf_native = [round(float(x), 6) for x in vec.idf_]

        models[key] = {
            "label": label,
            "used_features": [FEATURES[i] for i in use_idx],
            "mean": [round(float(x), 6) for x in mu],
            "std": [round(float(x), 6) for x in sd],
            "coef": coef_struct,
            "intercept": round(float(clf.intercept_[0]), 6),
            "tfidf_vocab": vocab_native,
            "tfidf_idf": idf_native,
            "text_coef": coef_text,
            "base_rate": round(base, 4),
            "auc": round(float(auc), 4),
            "pr_auc": round(float(pr), 4),
            "cv_auc": round(cv_auc, 4),
        }

    out = {
        "model_version": "apex-module-risk-text/1.0.0",
        "seed": SEED,
        "n_total": n,
        "feature_order": FEATURES,
        "modules": models,
    }
    # Save directly in the apex_trials path so modules.py can load it
    out_path = Path(__file__).parent / "apex_trials" / "module_models.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    
    macro_auc = float(np.mean([m["auc"] for m in models.values()]))
    print(f"\nmacro-AUC (held-out combined): {macro_auc:.3f}")
    print(f"saved -> {out_path}")


if __name__ == "__main__":
    main()
