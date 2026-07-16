---
id: f54311f8-3704-40cb-a3db-2f08e9b6ab04
domain: ASSET_ALLOCATION
name: "AA_TRANSDUCE_LIQUIDITY_BUFFER_DRAIN"
exergy_cost: 48.37
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:de6ce81a
---

# AA_TRANSDUCE_LIQUIDITY_BUFFER_DRAIN

## Causal Invariant
```text
Cash_t -> Repo_{t+1}
```

## Description
Transduce operation: Sweeps excess cash into overnight repo for yield extraction.
