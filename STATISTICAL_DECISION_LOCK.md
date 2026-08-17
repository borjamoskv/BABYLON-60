# STATISTICAL_DECISION_LOCK.md — Frozen Statistical Decision Rules (LOCK-14)

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Lock Identifier**: LOCK-14  

This document formalizes the pre-registered statistical decision framework, parameter locks, and hypothesis testing rules.

---

## 1. Frozen Statistical Decision Schema

```yaml
statistical_decision_lock:
  version: "1.0.0"
  primary_test:
    name: "exact_one_sided_mcnemar"
    treatment_arm: "D"
    control_arm: "C"
    alpha: 0.05
    sidedness: "one_sided_greater"
  multiple_testing_policy:
    primary_has_precedence: true
    secondary_exploratory_only: true
  stopping_rule: "FIXED_SAMPLE_SIZE"
```

---

## 2. Decision Rules & Invariance

1. **Parameter Lock**: $\alpha = 0.05$ is frozen. Any post-hoc modification to significance thresholds is forbidden.
2. **Test Invariance**: The primary test is locked to exact one-sided McNemar binomial evaluation on paired samples.
3. **No Adaptive Stopping**: Execution cannot stop early based on intermediate $p$-value monitoring. Sample size $N$ is fixed.
