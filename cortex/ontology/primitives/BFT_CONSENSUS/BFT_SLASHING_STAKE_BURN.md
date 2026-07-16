---
id: 74dd2936-84f1-43a4-bf63-c39d8118f68f
domain: BFT_CONSENSUS
name: "BFT_SLASHING_STAKE_BURN"
exergy_cost: 3.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:cf2f275e
---

# BFT_SLASHING_STAKE_BURN

## Causal Invariant
```text
Validator.Stake == 0
```

## Description
Destroys stake of Byzantine validator.
