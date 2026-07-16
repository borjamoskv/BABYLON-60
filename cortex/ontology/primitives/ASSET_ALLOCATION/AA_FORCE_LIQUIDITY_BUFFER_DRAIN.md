---
id: 4df530ee-8c66-44f1-a26b-0ba242503349
domain: ASSET_ALLOCATION
name: "AA_FORCE_LIQUIDITY_BUFFER_DRAIN"
exergy_cost: 29.31
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:4a98bc43
---

# AA_FORCE_LIQUIDITY_BUFFER_DRAIN

## Causal Invariant
```text
Cash_t -> Repo_{t+1}
```

## Description
Force operation: Sweeps excess cash into overnight repo for yield extraction.
