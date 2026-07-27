<!-- C5-REAL EXERGY CERTIFIED -->
<p align="center"><strong>APEX·TRIALS</strong> — deterministic, auditable clinical-trial amendment-risk copilot</p>
<p align="center"><sub>cortex-persist substrate · ClinicalTrials.gov API v2 · C5-REAL · INDUSTRIAL NOIR 2026</sub></p>

---

## The wedge (why this beats a black box on ONE axis)

Biorce/Aika owns the data moat (~1M curated trials, enterprise sales, $60M). We do
**not** compete there. We compete where a regulated sponsor actually feels pain:
**provable, reproducible, tamper-evident decisions.**

A clinical trial's regulator (FDA 21 CFR Part 11 §11.10(e)) requires a
*computer-generated, time-stamped, independently verifiable* audit trail of every
system-produced decision. A recommendation engine that emits a PDF does not satisfy
that by construction. **APEX-TRIALS does**: every risk score is committed to the
BABYLON-60 / cortex-persist hash-chain, with the exact firing rules as `causal_taint`,
reproducible byte-for-byte from the protocol input.

Three properties Biorce does not expose:

| Property | Mechanism | Proof |
|:--|:--|:--|
| **Determinism** | Pure feature function → weighted rules | same protocol JSON → same score → same SHA3-256 hash |
| **Auditability** | cortex-persist hash-chain (`causal_taint`, Lamport, uuid5) | `apex verify` recomputes the whole chain; tampering breaks it |
| **Falsifiability** | Public version-history ground-truth | `apex backtest` — Spearman ρ(score, real amendments) |

The amendment-risk signal itself is built on a source Biorce's marketing ignores:
the **public protocol version history** (`/api/int/studies/{nct}/history`), whose
`moduleLabels` let us separate a *substantive* protocol amendment
(Eligibility / Study Design / Arms / Outcomes) from an administrative update — the
real-world label the model is validated against.

## Integration with Teorema-Robinson-Moskv

`apex_trials.ledger.AmendmentLedger` implements the exact cortex-persist entry
contract — `{ id: uuid5, prev_hash: sha3_256, payload, causal_taint, lamport_t,
agent_id }`, SQLite WAL, single-writer, verified-on-read — so it is **drop-in
contract-compatible** with `babylon60.bft.ledger_actor`. The hash covers only the
deterministic decision content (never wall-clock), preserving byte-for-byte
reproducibility while a sidecar `created_at` column supplies Part 11 provenance.

## Install & run

```bash
cd apex_trials
pip install click            # only hard dep; stdlib otherwise
export PYTHONPATH=.

python -m apex_trials.cli score    NCT01245062            # score + commit to ledger
python -m apex_trials.cli report   NCT01245062 -o out.html --calibrate melanoma
python -m apex_trials.cli backtest --condition cancer -n 40
python -m apex_trials.cli verify                          # verify the hash-chain
python -m apex_trials.cli search  "breast cancer" --phase 3
```

Python API:

```python
from apex_trials import CtGovClient, HttpCache, AmendmentLedger, Copilot

cop = Copilot(CtGovClient(cache=HttpCache()), AmendmentLedger("master_ledger.db"))
res = cop.score("NCT01245062")
print(res.assessment.tier, res.assessment.score)   # HIGH 68
print(res.ledger_entry.entry_hash)                 # tamper-evident anchor
print(res.history.n_substantive)                   # 8 real amendments on record
```

## Model (transparent by construction)

Eight first-principles complexity drivers, each firing a named rule with an explicit
threshold and evidence value (max 114 raw → normalized 0–100 → LOW/MODERATE/HIGH/CRITICAL):

`eligibility ≤30 · endpoints ≤18 · arms ≤10 · enrollment ≤12 · geography ≤14 · phase ≤10 · design ≤10 · therapeutic-area ≤6`

Grounded in the public amendment literature (Tufts CSDD; FDA/EMA deviation reports):
over-specified eligibility, endpoint proliferation, multi-arm designs, large
multinational enrollment, and late-phase / oncology / rare-disease baselines are the
recurring amendment drivers. Weights are a starting prior — **not** fit to any cohort —
and every one is visible in `risk_engine.py` for a sponsor to retune.

## Validation (C5-REAL, against public ground-truth)

The mixing weights are fit on a corpus of **8,000 completed interventional trials**
(`build_dataset.py`), each labeled with its true substantive-amendment count from the
public version history. Fit on 6,000, **held out 2,000**:

```
                         Spearman ρ (held-out)
hand-tuned prior              0.402
NNLS-band fitted              0.416     (+0.014)
Poisson raw (ceiling)         0.436
5-fold CV (fitted)            0.381 ± 0.020

Isotonic calibration MAE = 1.74 amendments  vs  2.02 predict-the-mean   (−13.8%)
```

Honest read: fitting buys a **marginal ranking gain** but a **meaningful calibration
gain** — the model now forecasts the *actual number* of substantive amendments (score
30 → ~3.1, 50 → ~6.3), 13.8% better than the naive baseline on held-out data. It also
**corrected the prior**: geography was over-weighted (0.12 → 0.07), enrollment
(0.11 → 0.17) and therapeutic area (0.05 → 0.12) under-weighted; eligibility stays #1
(0.20).

Learned importances (`fitted_weights.json`, non-negative, sum = 1):

```
eligibility 0.195 · enrollment 0.172 · design 0.128 · endpoints 0.127
phase 0.124 · therapeutic-area 0.116 · geography 0.070 · arms 0.069
```

Calibration is dense-region reliable (≈99.9% of trials score <60); the extreme tail
(score ≥60, ~0.3% of trials) is small-n and high-variance — forecasts there say
"expect many" but the exact count is uncertain. Everything remains deterministic and
ledger-anchored: the `causal_taint` records which model version produced each decision.

### Forward generalization (temporal split — the honest number)

The metrics above are a *random* split (interpolation). Under a **temporal** split
(train on trials registered ≤2018, predict on ≥2019 — `fit_temporal.py`), performance
degrades: aggregate Spearman **0.41 → 0.28**, per-module macro-AUC **0.68 → 0.61**.
Signal survives (positive ρ, every module AUC > 0.58) but is **modest** — the honest
figure to quote for deployment is the *forward* one, ρ≈0.28, not the in-regime 0.41.
(Confound disclosed: newer trials have accrued fewer amendments, target mean 3.0 → 1.6;
Spearman is robust to that shift, MAE is not.) See
`AUDITORIA_APEX_TRIALS_TEMPORAL_2026-07-17.md`. Deployment practice: validate temporally
(done), train the final model on the full corpus (shipped), and re-fit on a rolling
window to counter temporal drift.

Set `mode="hand"` in `assess()` (or delete `apex_trials/fitted_weights.json`) to fall
back to the transparent first-principles prior.

## Amendment surface — which module will change

Beyond the aggregate score, APEX predicts **which** substantive module a protocol will
amend. Six leakage-mitigated logistic models (`fit_module_models.py` →
`module_models.json`), one per module, each trained *without* its own self-referential
feature (the eligibility model never sees the final eligibility count, etc.), on the
same 8k-trial corpus with per-module labels (`build_module_labels.py`):

```
module                  base   held-out AUC   PR-AUC
Study Design            0.766     0.689        0.875
Arms and Interventions  0.373     0.674        0.583
Eligibility             0.330     0.669        0.529
Outcome Measures        0.471     0.662        0.650
Conditions              0.171     0.647        0.285
Study Description       0.316     0.643        0.483
macro-AUC (held-out) = 0.664   ·   CV-AUC tracks held-out within ±0.01
```

Modest but real, stable signal — every module beats chance from design features alone,
leakage-mitigated. Runtime inference is a dependency-free standardize + sigmoid, fully
deterministic. `predict_module_risks(features)` returns each module's P(amendment),
base rate, and lift; the report renders it as a ranked surface with base-rate ticks.

```python
from apex_trials import CtGovClient, HttpCache, AmendmentLedger, Copilot
res = Copilot(CtGovClient(cache=HttpCache()), AmendmentLedger()).score("NCT01245062")
for m in res.module_risks:
    print(f"{m.label:<24} {m.probability:.0%}  ({m.lift:.2f}× base)")
# Study Design 100% · Outcome Measures 100% · Eligibility 94% · Arms 92% ...
```

## Roadmap (real moat, if pursued)

1. ~~Fit the aggregate weights against the history corpus.~~ **Done** — NNLS-band + isotonic on 8k trials (`fit_weights.py`).
2. ~~Per-module amendment *cause* prediction.~~ **Done** — 6 leakage-mitigated logistic models, macro-AUC 0.664 held-out (`fit_module_models.py`).
2b. ~~Protocol text features vs temporal drift.~~ **Validated** — TF-IDF recovers ~half the temporal degradation (macro-AUC 0.612→0.647, agg ρ 0.290→0.333; `fit_text.py`, `APEX_TEXT_FEATURES_2026-07-17.md`). Runtime integration pending a byte-exact equivalence test (Option B) — see the doc.
3. Scale both corpora toward the full ~560k records; add temporal splits (train on pre-2020, test on post) to prove the model generalizes forward.
4. Site-feasibility scoring from `contactsLocationsModule` enrollment velocity.
5. Swap the standalone ledger for the live `babylon60.bft.ledger_actor` + Git Sentinel.

---
<sub>Titular Civil: Borja Fernández Angulo · AKA Borja Moskv (<code>borjamoskv</code>) · data © ClinicalTrials.gov (public domain)</sub>
