---
id: f2c6f5da-4630-40eb-8632-d2afc52c8a92
domain: BFT_CONSENSUS
name: "BFT_SYNC_PEER_DISCONNECT_BYZANTINE"
exergy_cost: 0.8
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:5cb3eb05
---

# BFT_SYNC_PEER_DISCONNECT_BYZANTINE

## Causal Invariant
```text
Socket.Close() invoked
```

## Description
Severs connection with peer supplying invalid sync data.
