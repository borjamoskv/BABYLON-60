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

Pooled cohort (cancer + diabetes + heart-failure, n=75 completed trials):

```
Spearman ρ(score, actual substantive amendments) = 0.30
LOW      mean actual amendments = 1.87
MODERATE mean actual amendments = 3.14
HIGH     mean actual amendments = 5.50
```

Positive rank-ordering from a zero-training prior, fully auditable. Not a claim of
trained accuracy — the value is the reproducible, verifiable framework; accuracy is a
tuning/back-testing exercise the harness already supports.

## Roadmap (real moat, if pursued)

1. Fit the weights via isotonic/logistic regression on the full ~560k-record history corpus (the harness is ready; only the fit is missing).
2. Per-driver amendment *cause* prediction (which module will change), not just aggregate risk.
3. Site-feasibility scoring from `contactsLocationsModule` enrollment velocity.
4. Swap the standalone ledger for the live `babylon60.bft.ledger_actor` + Git Sentinel.

---
<sub>Titular Civil: Borja Fernández Angulo · AKA Borja Moskv (<code>borjamoskv</code>) · data © ClinicalTrials.gov (public domain)</sub>
