---
id: b1fdd30d-782f-4a49-bd03-f466e726b2de
domain: BFT_CONSENSUS
name: "BFT_PROPOSAL_VERIFY_HEIGHT"
exergy_cost: 0.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:34a809ec
---

# BFT_PROPOSAL_VERIFY_HEIGHT

## Causal Invariant
```text
Proposal.Height == Local.Height + 1
```

## Description
Checks proposal height monotonicity.
