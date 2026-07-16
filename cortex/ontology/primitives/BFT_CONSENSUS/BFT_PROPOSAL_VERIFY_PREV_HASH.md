---
id: 28d5c6dd-abca-4aff-801f-d2f08fc15882
domain: BFT_CONSENSUS
name: "BFT_PROPOSAL_VERIFY_PREV_HASH"
exergy_cost: 0.3
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:523918c6
---

# BFT_PROPOSAL_VERIFY_PREV_HASH

## Causal Invariant
```text
Proposal.PrevHash == Local.LastBlockHash
```

## Description
Enforces hash chain continuity.
