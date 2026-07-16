---
id: c31bfcc2-e588-46ae-8565-03747ed2f293
domain: BFT_CONSENSUS
name: "BFT_PROPOSAL_BROADCAST"
exergy_cost: 3.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:8369d474
---

# BFT_PROPOSAL_BROADCAST

## Causal Invariant
```text
Network egress queue contains N-1 deterministic packets
```

## Description
Transmits signed proposal to N-1 replica nodes.
