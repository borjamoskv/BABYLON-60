---
id: 9e002c95-b6b0-4fed-92fc-5221b0e965f6
domain: ASSET_ALLOCATION
name: "AA_COLLAPSE_LIQUIDITY_BUFFER_DRAIN"
exergy_cost: 32.14
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:67315d7b
---

# AA_COLLAPSE_LIQUIDITY_BUFFER_DRAIN

## Causal Invariant
```text
Cash_t -> Repo_{t+1}
```

## Description
Collapse operation: Sweeps excess cash into overnight repo for yield extraction.
