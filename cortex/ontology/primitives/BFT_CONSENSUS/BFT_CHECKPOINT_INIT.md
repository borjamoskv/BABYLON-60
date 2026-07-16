---
id: d4df8838-66d6-4179-9b92-cef00ae168ea
domain: BFT_CONSENSUS
name: "BFT_CHECKPOINT_INIT"
exergy_cost: 1.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:eaf6a72b
---

# BFT_CHECKPOINT_INIT

## Causal Invariant
```text
Height % CheckpointInterval == 0
```

## Description
Creates periodic state checkpoint proposal.
