---
id: fea87396-238f-44b2-98c3-0b0ba6cbaa5c
domain: BFT_CONSENSUS
name: "BFT_SLASHING_VALIDATOR_EVICT"
exergy_cost: 1.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:af0ee859
---

# BFT_SLASHING_VALIDATOR_EVICT

## Causal Invariant
```text
ActiveSet.Size == ActiveSet.Size - 1
```

## Description
Removes Byzantine node from active validator set.
