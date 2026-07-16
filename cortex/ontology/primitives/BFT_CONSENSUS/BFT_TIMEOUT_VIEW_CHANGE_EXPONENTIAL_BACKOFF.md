---
id: 7f43a997-c679-4583-ab08-bf6f197b802e
domain: BFT_CONSENSUS
name: "BFT_TIMEOUT_VIEW_CHANGE_EXPONENTIAL_BACKOFF"
exergy_cost: 0.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:51182a6e
---

# BFT_TIMEOUT_VIEW_CHANGE_EXPONENTIAL_BACKOFF

## Causal Invariant
```text
TimeoutDuration = TimeoutDuration * 2
```

## Description
Increases timeout duration upon successive failures.
