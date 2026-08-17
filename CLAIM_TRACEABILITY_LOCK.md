# CLAIM_TRACEABILITY_LOCK.md — Frozen Claim-to-Verdict Hash-Bound DAG Lock (LOCK-15)

> **STATUS: FROZEN / NORMATIVE v2.1**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Lock Identifier**: LOCK-15  

This document formalizes the explicit 8-stage Claim Traceability Directed Acyclic Graph (DAG), establishing a cryptographically hash-bound chain-of-custody that links any scientific assertion to its raw evidence and mathematical verdict.

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

## 2. Core Epistemic Invariants of LOCK-15

To prevent silent edge-rewiring or payload tampering attacks, every execution trace path must satisfy the three mathematical invariants:

$$\begin{aligned}
1.\;& \forall \text{verdict } V, \;\exists! \text{ path } \Big( \text{CLAIM} \to \text{FORMAL\_CLAIM} \to \text{TEST} \to \text{RUN\_ID} \to \text{RAW\_DATA} \to \text{STATISTIC} \to \text{DECISION} \to V \Big) \\
2.\;& \forall \text{edge } E(u, v): \;\text{source}(E) \in \text{DAG} \;\land\; \text{target}(E) \in \text{DAG} \;\land\; \text{edge}(E) \text{ is authorized} \;\land\; H(E) = \text{SHA256}\big(H(u) \parallel H(v)\big) \\
3.\;& \forall \text{node } N: \; H(N) = \text{SHA256}\big(\text{canonical\_payload}(N)\big)
\end{aligned}$$

---

## 3. Edge-Rewiring & Node-Tampering Defense Rules

1. **Node Tampering Defense**: Modifying the payload of any node $N$ alters $H(N)$, instantly invalidating downstream edge hashes $H(E(N, \cdot))$.
2. **Edge Rewiring Defense**: Leaving node payloads untouched while redirecting an edge target (e.g. changing $E(\text{TEST}_A, \text{RUN}_{001})$ to $E(\text{TEST}_A, \text{RUN}_{999})$) alters $H(E)$, causing immediate verification rejection.
3. **Manifest Recalculation Resistance**: The root of trust rests on immutable root hash anchors rather than loose manifest files. Recomputing manifests over modified nodes or rewired edges is detected and blocked by the verifier engine.
