# CLAIM_TRACEABILITY_LOCK.md — Frozen Claim-to-Verdict DAG Lock (LOCK-15)

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Lock Identifier**: LOCK-15  

This document formalizes the explicit 8-stage Claim Traceability Directed Acyclic Graph (DAG) that establishes cryptographically verifiable chain-of-custody linking any scientific assertion to its raw evidence and mathematical verdict.

---

## 1. The 8-Stage Claim Traceability DAG

```text
               +-----------------------------------+
               |               CLAIM               |
               |   (Natural language assertion)    |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |           FORMAL_CLAIM            |
               |    (FORMAL_CLAIMS.md mapping)     |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |               TEST                |
               | (Exact McNemar test specification)|
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |              RUN_ID               |
               | (Unique benchmark suite run UUID) |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |             RAW_DATA              |
               |  (Signed RFC8785 trace payload)   |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |             STATISTIC             |
               |  (Exact calculated p-value & b,c) |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |             DECISION              |
               |  (FALSIFICATION_RULES.md check)   |
               +-----------------------------------+
                                 |
                                 v
               +-----------------------------------+
               |              VERDICT              |
               |    (ACCEPTED / REJECTED status)   |
               +-----------------------------------+
```

---

## 2. DAG Verification Schema

```yaml
claim_traceability_lock:
  version: "1.0.0"
  dag_nodes:
    - CLAIM
    - FORMAL_CLAIM
    - TEST
    - RUN_ID
    - RAW_DATA
    - STATISTIC
    - DECISION
    - VERDICT
  cryptographic_binding:
    hash_chain_required: true
```

---

## 3. Epistemic Chain Breaking Rule

> If any node in the Claim Traceability DAG is altered, missing, unverified, or cryptographically inconsistent with upstream artifacts, the entire claim is marked **INVALID / BROKEN CHAIN** and rejected from public repositories and paper submissions.
