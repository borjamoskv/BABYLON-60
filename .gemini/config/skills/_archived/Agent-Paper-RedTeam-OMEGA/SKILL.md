---
name: Agent-Paper-RedTeam-OMEGA
description: C5-REAL Adversarial Audit Protocol for Agent Research Papers. Destroys weak claims via hostile re...
script: scripts/agent__paper__red_team_omega.py
---
# Agent-Paper-RedTeam-OMEGA

```yaml
Execution_Mode: C5-REAL
Objective: Purge weak claims, enforce verifiable engineering.

Epistemology:
  L1: "Faster != Contribution. Speed is ephemeral."
  L2: "100% success = synthetic/overfit. Benchmark != Evidence."
  L3: "Latency reduction requires structural mechanism."
  L4: "Attacks target interpretation (fairness, causal logic)."
  L5: "Deterministic failure > probabilistic success."
  L6: "Reproducibility (P95/P99, raw logs) > rhetoric."

Attack_Pipeline:
  1_Obviousness:
    Target: "Trivial claims (e.g., API > Vision)."
    Enforcement: "Shift to Error Distribution or Failure Semantics."
  2_Fairness:
    Target: "Mismatched comparisons."
    Enforcement: "Explicitly study constraint lifting."
  3_Generalization:
    Target: "Edge cases (Remote DBs, legacy UI)."
    Enforcement: "Confine scope. Add Threats to Validity."
  4_Reproducibility:
    Target: "Missing logs/code."
    Enforcement: "Force Reproducibility Appendix + P50/P95/P99."
  5_Alternative_Hypothesis:
    Target: "H0 (fewer steps) vs H1 (structural)."
    Enforcement: "Fix Planner/Model. Isolate variables."
  6_Epistemic_Determinism:
    Target: "Stochastic failure masking."
    Enforcement: "Anchor random seeds to Ledger Hash. Force live A/B variable toggling."

Reviewer_Simulation:
  Systems: "Attacks benchmark design/fairness."
  Agent: "Attacks generalization limits."
  Engineer: "Attacks reproducibility/code."

Exit_Criteria:
  - "Validate survival against all 5 attacks."
  - "Assert Threats to Validity block."
  - "Assert focus: Deterministic Execution over Probabilistic Success."
```
