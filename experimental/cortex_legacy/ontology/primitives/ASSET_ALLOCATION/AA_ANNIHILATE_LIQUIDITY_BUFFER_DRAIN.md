---
id: c7e5cf50-5540-4cae-a16b-e76056d8fcf6
domain: ASSET_ALLOCATION
name: "AA_ANNIHILATE_LIQUIDITY_BUFFER_DRAIN"
exergy_cost: 31.44
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:31.363305:4513599e
---

# AA_ANNIHILATE_LIQUIDITY_BUFFER_DRAIN

## Causal Invariant
```text
Cash_t -> Repo_{t+1}
```

## Description
Annihilate operation: Sweeps excess cash into overnight repo for yield extraction.
