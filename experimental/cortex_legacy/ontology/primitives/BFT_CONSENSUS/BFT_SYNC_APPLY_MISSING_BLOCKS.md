---
id: 6efce5c8-df28-4e70-b618-85ba8697f794
domain: BFT_CONSENSUS
name: "BFT_SYNC_APPLY_MISSING_BLOCKS"
exergy_cost: 18.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:1db4ca87
---

# BFT_SYNC_APPLY_MISSING_BLOCKS

## Causal Invariant
```text
Local.Height synchronized to Peer.Height
```

## Description
Executes state transition for missing blocks.
