---
id: cd223f8a-16b0-49fc-a804-0b3963923972
domain: BFT_CONSENSUS
name: "BFT_CRYPTO_AGGREGATE_SIGS"
exergy_cost: 7.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:cb5caf5d
---

# BFT_CRYPTO_AGGREGATE_SIGS

## Causal Invariant
```text
AggregateSig equals sum of individual sigs
```

## Description
Aggregates BLS signatures into single proof.
