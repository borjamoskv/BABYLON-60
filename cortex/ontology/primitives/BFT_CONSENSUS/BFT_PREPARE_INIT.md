---
id: b3c0f8a1-69cd-4643-90f2-6da6ddfe3869
domain: BFT_CONSENSUS
name: "BFT_PREPARE_INIT"
exergy_cost: 0.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:c653755d
---

# BFT_PREPARE_INIT

## Causal Invariant
```text
Vote.Type == PREPARE AND Vote.TargetHash == Proposal.Hash
```

## Description
Constructs PREPARE vote for accepted proposal.
