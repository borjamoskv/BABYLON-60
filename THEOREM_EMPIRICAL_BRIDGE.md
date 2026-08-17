# THEOREM_EMPIRICAL_BRIDGE.md — Frozen Epistemic Firewall

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  

This document formalizes the fundamental epistemic firewall separating mathematical proof in Lean 4 from statistical empirical inference over experimental benchmark runs.

---

## 1. The Central Epistemic Firewall Equation

$$\boxed{\text{Formal Inclusion} + \text{Runtime Refinement} + \text{Cost Alignment} \;\not\Rightarrow\; \text{Empirical Superiority}}$$

### Fundamental Principle
Mathematical verification in Lean 4 proves structural properties (safety, invariant preservation, bounded reachability inclusion). It **cannot** prove that an agent using CTM will solve more benchmark problems in practice. 

Empirical superiority ($\text{Coverage}(D) > \text{Coverage}(C)$) can **only** be established via controlled experimental evaluation.

---

## 2. The 6-Stage Epistemic Derivation Ladder

```text
+-------------------------------------------------------------+
| STAGE 1: Lean 4 Formal Proof                                |
|  - SafeState_construction                                   |
|  - invariant_preservation                                   |
|  - reachability_inclusion                                   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| STAGE 2: Runtime Refinement                                 |
|  - Execution traces strictly refine abstract Lean specs     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| STAGE 3: Valid Experimental Trace                           |
|  - Serialized according to TRACE_CONTRACT_v1.0.0.json       |
|  - Verified by independent external validator               |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| STAGE 4: Controlled Experiment                              |
|  - Interleaved paired sampling (RANDOMIZATION_PROTOCOL.md)  |
|  - Arms D, C, B, F executed under deterministic PRNG seeds  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| STAGE 5: Exact McNemar Statistical Test                     |
|  - Evaluate paired discordant successes (b vs c)           |
|  - Compute exact one-sided p-value at alpha = 0.05          |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| STAGE 6: Empirical Decision                                 |
|  - Evidence FOR or AGAINST CTM policy advantage             |
+-------------------------------------------------------------+
```

---

## 3. Epistemic Invalidation Rules

1. **Illegitimate Jump Elimination**: Any argument of the form:
   $$\text{Lean 4 Theorem Proved} \implies \text{"CTM Works Empirically"}$$
   is strictly **invalid**.
2. **Reverse Claim Prevention**: Empirical success on benchmark datasets does **not** retroactively validate broken or unverified Lean 4 formal proofs.
3. **Boundary Integrity**: Formal proofs provide safety and reachability guarantees. Controlled experiments provide empirical utility evidence. Neither replaces the other.
