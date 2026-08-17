# FALSIFICATION_RULES.md — Frozen Popperian Falsification Rules

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  

This document specifies the Popperian kill conditions and statistical interpretation guardrails that govern the empirical evaluation of the CTM architecture.

---

## 1. Frozen Falsification Schema

```yaml
primary:
  D_vs_C:
    superiority: one_sided
    alpha: 0.05

kill_conditions:
  - D <= C
  - p >= 0.05

secondary_diagnostics:
  - D <= B
  - D <= F

interpretation:
  p_value:
    does_not_measure:
      - probability_H0_is_true
      - probability_CTM_is_correct
```

---

## 2. Primary Hypothesis Kill Conditions

The primary empirical claim ("CTM provides statistically significant coverage superiority over standard agent baselines") is **INSTANTLY FALSIFIED** if any of the following conditions hold:

1. **`D <= C` (Coverage Non-Superiority)**: The empirical coverage rate of Treatment Arm $D$ is less than or equal to Control Arm $C$ ($\text{Coverage}(D) \le \text{Coverage}(C)$).
2. **`p >= 0.05` (Statistical Insignificance)**: The exact one-sided McNemar test $p$-value comparing $D$ and $C$ is greater than or equal to $\alpha = 0.05$.

### Epistemic Consequence of Primary Falsification
If $D \le C$ or $p \ge 0.05$, the primary hypothesis is declared **DEAD**. No amount of sub-group analysis, post-hoc metric re-weighting, prompt tweaking, or secondary diagnostic success can revive the primary claim.

---

## 3. Secondary Diagnostic Triggers

Secondary diagnostic comparisons serve to isolate structural failure modes when the primary hypothesis is falsified:

1. **`D <= B` (Lack of Reachability Advantage)**: If $D$ does not outperform Budget Baseline $B$, structural reachability filtering provides no benefit over raw compute budget constraints.
2. **`D <= F` (Structural Reachability Breakdown)**: If $D$ does not outperform the Permuted Operator Baseline $F$, formal state space reachability bounds perform no better than random operator pruning.

---

## 4. Epistemic Guardrails on Statistical Interpretation

To prevent false inferences regarding $p$-values and mathematical truth:

1. **$p$-value DOES NOT measure $P(H_0 \text{ is true})$**: A small $p$-value indicates low probability of observing equal or more extreme sample divergence under $H_0$; it does **not** quantify the probability that $H_0$ is true.
2. **$p$-value DOES NOT measure $P(\text{CTM is correct})$**: Statistical rejection of $H_0$ provides empirical evidence for policy superiority on task set $\mathcal{B}$; it does **not** prove mathematical correctness of CTM Lean formal specifications.
