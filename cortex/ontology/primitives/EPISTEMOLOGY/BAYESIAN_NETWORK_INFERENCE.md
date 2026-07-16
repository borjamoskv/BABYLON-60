---
id: e856013a-8902-4dd8-8e62-a42871248e08
domain: EPISTEMOLOGY
name: "BAYESIAN_NETWORK_INFERENCE"
exergy_cost: 0.3
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:41:43.937503:0a682406
---

# BAYESIAN_NETWORK_INFERENCE

## Causal Invariant
```text
P(X_1...X_n) = \prod P(X_i | Pa(X_i))
```

## Description
Propagates probability updates through a directed acyclic graph of conditional dependencies.
