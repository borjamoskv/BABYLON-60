# EPISTEMIC_LOCKS.md — Master Index & Governance Specification

> **STATUS: FROZEN / NORMATIVE MASTER INDEX v2.1.0**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Verification CLI**: `python3 scripts/verify_epistemic_locks.py`  

This master document serves as the central index and entry point for the **15 frozen epistemic, contractual, and experimental governance locks** established for the **Teorema Robinson-Moskv** architecture.

---

## 1. The 3-Way Epistemic Separation Firewall

To prevent circular reasoning or false equivalence, the architecture strictly decouples three distinct levels of truth:

```text
+-----------------------------------------------------------------------------------+
|                            LEVEL 1: CRYPTOGRAPHIC TRUTH                           |
|                    "This artifact hash has not been modified"                     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                             LEVEL 2: FORMAL TRUTH                                 |
|             "Lean 4 proves reachability inclusion under bridge axioms"             |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                            LEVEL 3: EMPIRICAL RESULT                              |
|           "Paired McNemar test yielded p < 0.05 on benchmark task set B"          |
+-----------------------------------------------------------------------------------+
```

> **FIREWALL INVARIANT**: No single level (Cryptographic, Formal, or Empirical) can be automatically converted into `"THE THEOREM IS TRUE IN THE WORLD"`. The system enforces empirical falsability at all times.

---

## 2. Claim-to-Verdict Chain of Custody (LOCK-15)

```text
CLAIM -> FORMAL_CLAIM -> TEST -> RUN_ID -> RAW_DATA -> STATISTIC -> DECISION -> VERDICT
```

---

## 3. Catalog of 15 Frozen Lock Files

| Lock ID | Filename | Primary Role | Status |
|---|---|---|---|
| **LOCK-01** | [FORMAL_CLAIMS.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/FORMAL_CLAIMS.md) | Boundary of Lean 4 proofs vs assumptions vs empirical claims vs non-claims | **FROZEN** |
| **LOCK-02** | [ASSUMPTIONS.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/ASSUMPTIONS.md) | 4-tier bridge axioms (Formal $\to$ Model $\to$ Runtime $\to$ Experiment) | **FROZEN** |
| **LOCK-03** | [TRACE_CONTRACT_v1.0.0.json](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/TRACE_CONTRACT_v1.0.0.json) | Normative JSON Schema (RFC 8785, SHA-256) enforcing runtime authority limits | **FROZEN** |
| **LOCK-04** | [BENCHMARK_PROTOCOL_v1.0.0.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/BENCHMARK_PROTOCOL_v1.0.0.md) | Preregistered experimental protocol with exact one-sided McNemar test ($\alpha=0.05$) | **FROZEN** |
| **LOCK-05** | [RANDOMIZATION_PROTOCOL.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/RANDOMIZATION_PROTOCOL.md) | Deterministic ChaCha20 seed generation, arm interleaving, zero retries, fixed sample size | **FROZEN** |
| **LOCK-06** | [METRICS.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/METRICS.md) | Operational mathematical formulas for Coverage (zero partial credit) and secondary metrics | **FROZEN** |
| **LOCK-07** | [FALSIFICATION_RULES.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/FALSIFICATION_RULES.md) | Popperian kill conditions ($D \le C$ or $p \ge 0.05$) and $p$-value epistemic guardrails | **FROZEN** |
| **LOCK-08** | [REPRODUCIBILITY_LOCK.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/REPRODUCIBILITY_LOCK.md) | Full environment pins and 6-stage cryptographic provenance hash chain | **FROZEN** |
| **LOCK-09** | [THREAT_MODEL.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/THREAT_MODEL.md) | Catalog of 14 systemic & experimental threats and mitigation matrix | **FROZEN** |
| **LOCK-10** | [THEOREM_EMPIRICAL_BRIDGE.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/THEOREM_EMPIRICAL_BRIDGE.md) | Central epistemic firewall equation and 6-stage derivation ladder | **FROZEN** |
| **LOCK-11** | [PROVENANCE_LOCK.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/PROVENANCE_LOCK.md) | Cryptographic data origin, ISO 8601 UTC timestamps, and Merkle custody chain | **FROZEN** |
| **LOCK-12** | [EXECUTION_LOCK.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/EXECUTION_LOCK.md) | Attestation linking results to clean git commit SHA, binary hashes, and code entrypoints | **FROZEN** |
| **LOCK-13** | [ENVIRONMENT_LOCK.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/ENVIRONMENT_LOCK.md) | Pinning of Python, Lean 4, Rust, OS, CPU microarchitecture, and lockfile digests | **FROZEN** |
| **LOCK-14** | [STATISTICAL_DECISION_LOCK.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/STATISTICAL_DECISION_LOCK.md) | Pre-registered parameter locks ($\alpha=0.05$, exact McNemar, fixed sample size) | **FROZEN** |
| **LOCK-15** | [CLAIM_TRACEABILITY_LOCK.md](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/CLAIM_TRACEABILITY_LOCK.md) | 8-stage Claim Traceability DAG linking assertion to raw evidence and verdict | **FROZEN** |

---

## 4. Automated Verification & Security Audits

```bash
python3 scripts/verify_epistemic_locks.py
pytest tests/test_epistemic_tamper_resistance.py
```
