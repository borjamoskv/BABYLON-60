---
id: 9a02e6f1-0186-49e6-b88a-7b8565a9a002
domain: BFT_CONSENSUS
name: "BFT_PROPOSAL_ACCEPT"
exergy_cost: 0.6
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:23d52ec0
---

# BFT_PROPOSAL_ACCEPT

## Causal Invariant
```text
Local.LockedProposal == Proposal
```

## Description
Locks proposal in local consensus engine for voting.
