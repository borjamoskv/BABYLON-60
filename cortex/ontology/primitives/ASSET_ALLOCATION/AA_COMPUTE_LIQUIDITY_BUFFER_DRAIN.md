---
id: 7d4f8ae0-11aa-41b7-be9d-d70aae62b368
domain: ASSET_ALLOCATION
name: "AA_COMPUTE_LIQUIDITY_BUFFER_DRAIN"
exergy_cost: 41.65
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:e238e340
---

# AA_COMPUTE_LIQUIDITY_BUFFER_DRAIN

## Causal Invariant
```text
Cash_t -> Repo_{t+1}
```

## Description
Compute operation: Sweeps excess cash into overnight repo for yield extraction.
