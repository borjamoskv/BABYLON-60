---
id: 17eedcdc-2e1c-40e4-ab41-bc3a85278d27
domain: BFT_CONSENSUS
name: "BFT_SYNC_CATCHUP_COMPLETE"
exergy_cost: 0.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:2136ed2c
---

# BFT_SYNC_CATCHUP_COMPLETE

## Causal Invariant
```text
ReplicaState transits from SYNCING to ACTIVE
```

## Description
Transitions replica back to active consensus participation.
