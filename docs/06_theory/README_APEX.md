# 🧪 APEX TRIALS (`docs/06_theory/README_APEX.md`)

[![FDA Compliance](https://img.shields.io/badge/FDA-21_CFR_Part_11-blue?style=for-the-badge)](https://www.fda.gov/)
[![Data Source](https://img.shields.io/badge/Data-ClinicalTrials.gov_API_v2-purple?style=for-the-badge)](https://clinicaltrials.gov/)
[![Causal Ledger](https://img.shields.io/badge/Ledger-Tamper--Evident_HashChain-brightgreen?style=for-the-badge)](../../babylon60/bft/README.md)

**APEX TRIALS** is a deterministic, auditable clinical-trial amendment-risk copilot built on the BABYLON-60 Ledger substrate.

---

## 🎯 The Wedge (Why This Beats a Black Box)

Biorce/Aika owns the data moat (~1M curated trials, enterprise sales, $60M). We do **not** compete there. We compete where a regulated sponsor actually feels pain: **provable, reproducible, tamper-evident decisions.**

A clinical trial's regulator (FDA 21 CFR Part 11 §11.10(e)) requires a *computer-generated, time-stamped, independently verifiable* audit trail of every system-produced decision. A recommendation engine that emits a PDF does not satisfy that by construction. **APEX-TRIALS does**: every risk score is committed to the BABYLON-60 hash-chain with exact firing rules as `causal_taint`, reproducible byte-for-byte from the protocol input.

Three properties black-box models do not expose:

| Property | Mechanism | Proof |
| :--- | :--- | :--- |
| **Determinism** | Pure feature function $\to$ weighted rules | Same protocol JSON $\to$ same score $\to$ same SHA3-256 hash |
| **Auditability** | Ledger hash-chain (`causal_taint`, Lamport, UUIDv5) | `apex verify` recomputes the whole chain; tampering breaks it |
| **Falsifiability** | Public version-history ground-truth | `apex backtest` — Spearman $\rho$(score, real amendments) |

The amendment-risk signal itself is built on a source public protocol version history (`/api/int/studies/{nct}/history`), whose `moduleLabels` separate a *substantive* protocol amendment (Eligibility / Study Design / Arms / Outcomes) from an administrative update.

---

## 🔬 Integration with Causal Motor Substrate

`apex_trials.ledger.AmendmentLedger` implements the exact entry contract:
`{ id: uuid5, prev_hash: sha3_256, payload, causal_taint, lamport_t, agent_id }`, SQLite WAL, single-writer, verified-on-read — making it **drop-in contract-compatible** with `babylon60.bft.ledger_actor`. The hash covers only deterministic decision content (never wall-clock), preserving byte-for-byte reproducibility while a sidecar `created_at` column supplies Part 11 provenance.

---

## 🚀 Install & Run

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

---

## 📊 Model & Validation Metrics

Eight first-principles complexity drivers, each firing a named rule with explicit thresholds and evidence values (max 114 raw $\to$ normalized 0–100 $\to$ LOW/MODERATE/HIGH/CRITICAL):

`eligibility ≤30 · endpoints ≤18 · arms ≤10 · enrollment ≤12 · geography ≤14 · phase ≤10 · design ≤10 · therapeutic-area ≤6`

Fit on 6,000 completed interventional trials, **held out 2,000**:

```
                         Spearman ρ (held-out)
hand-tuned prior              0.402
NNLS-band fitted              0.416     (+0.014)
Poisson raw (ceiling)         0.436
5-fold CV (fitted)            0.381 ± 0.020

Isotonic calibration MAE = 1.74 amendments  vs  2.02 predict-the-mean   (−13.8%)
```

Learned importances (`fitted_weights.json`):

```
eligibility 0.195 · enrollment 0.172 · design 0.128 · endpoints 0.127
phase 0.124 · therapeutic-area 0.116 · geography 0.070 · arms 0.069
```

---

## 📈 Amendment Surface Prediction

Predicts **which** substantive module a protocol will amend across six leakage-mitigated logistic models:

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

---

<sub>Titular Civil: Borja Fernández Angulo · AKA Borja Motor Causal (`borjamoskv`) · Data © ClinicalTrials.gov (Public Domain)</sub>
