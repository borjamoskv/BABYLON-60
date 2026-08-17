# METRICS.md — Frozen Operational Metric Definitions

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  

This document specifies the operational mathematical definitions for all metrics evaluated within the Teorema Robinson-Moskv framework.

---

## 1. Frozen Coverage Specification

```yaml
coverage:
  unit: benchmark_item
  success_predicate: EXACTLY_DEFINED
  denominator: FIXED
  duplicate_policy: FIXED
  invalid_output_policy: FIXED
  timeout_policy: FIXED
  partial_credit: FORBIDDEN
```

### Operational Formula for Coverage

For a fixed benchmark suite $\mathcal{B} = \{x_1, x_2, \dots, x_N\}$ of size $N = |\mathcal{B}|$:

$$\text{Coverage}(A) = \frac{1}{N} \sum_{i=1}^{N} \mathbb{I}\Big( \text{Eval}(A, x_i) = \text{SUCCESS} \Big)$$

Where:
- **`unit`**: Standard benchmark task item $x_i$.
- **`success_predicate`**: Boolean evaluation oracle returning $1$ if and only if state invariants and domain success conditions are fully satisfied, and $0$ otherwise.
- **`denominator`**: Total number of pre-registered tasks $N$. Never adjusted post-hoc.
- **`duplicate_policy`**: Duplicate solutions or repeated step execution within a task yield zero additional score.
- **`invalid_output_policy`**: Syntactically or semantically malformed outputs evaluate strictly to $0$ (`FAILURE`).
- **`timeout_policy`**: Tasks exceeding step or time limits evaluate strictly to $0$ (`TIMEOUT_FAILURE`).
- **`partial_credit`**: `FORBIDDEN`. Binary indicator function $\mathbb{I} \in \{0, 1\}$ only.

---

## 2. Metric Taxonomy & Formalization

```text
+-----------------------------------------------------------------------+
|                             METRICS                                   |
+-----------------------------------------------------------------------+
  |-- Coverage   : Ratio of binary task completions over fixed N
  |-- Validity   : Proportion of trace steps adhering to SafeState invariant
  |-- Cost       : Total token expenditure and step count per solved task
  |-- Latency    : Wall-clock duration per trace step and task execution
  |-- Regression : Proportion of previously solved tasks failed by treatment
  |-- Diversity  : Entropy of state space trajectories explored
```

### 2.1 Validity ($\mathcal{V}$)
The proportion of executed trace steps that preserve the formal safety invariant:

$$\mathcal{V}(A) = \frac{\sum_{i=1}^{N} \sum_{t=1}^{T_i} \mathbb{I}\big(s_{i, t} \in \mathcal{S}_{\text{safe}}\big)}{\sum_{i=1}^{N} T_i}$$

### 2.2 Cost ($\mathcal{C}$)
Normalized resource consumption per task item:

$$\mathcal{C}_{\text{tokens}}(A) = \frac{1}{N} \sum_{i=1}^{N} \text{Tokens}(A, x_i), \qquad \mathcal{C}_{\text{steps}}(A) = \frac{1}{N} \sum_{i=1}^{N} \text{Steps}(A, x_i)$$

### 2.3 Latency ($\mathcal{L}$)
Mean execution duration across benchmark task items:

$$\mathcal{L}(A) = \frac{1}{N} \sum_{i=1}^{N} \text{WallClockTimeMs}(A, x_i)$$

### 2.4 Regression ($\mathcal{R}$)
Proportion of benchmark items solved by Control $C$ but failed by Treatment $D$:

$$\mathcal{R}(D \mid C) = \frac{\sum_{i=1}^{N} \mathbb{I}\big(\text{Eval}(C, x_i) = 1 \;\land\; \text{Eval}(D, x_i) = 0\big)}{\sum_{i=1}^{N} \mathbb{I}\big(\text{Eval}(C, x_i) = 1\big)}$$

### 2.5 Diversity ($\mathcal{D}$)
Shannon entropy over the discrete state-hash frequency distribution $\mathbf{p}$:

$$\mathcal{D}(A) = -\sum_{k=1}^{K} p_k \log_2 p_k$$

---

## 3. Strict Metric Isolation Rule

> No single metric may be silently substituted for or merged into another. Specifically, a reduction in Cost or Latency **cannot** compensate for a drop in Coverage, nor can Validity replace Coverage proof obligations.
