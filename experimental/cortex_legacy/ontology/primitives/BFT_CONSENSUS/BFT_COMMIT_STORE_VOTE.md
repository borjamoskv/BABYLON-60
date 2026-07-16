---
id: 675bf182-62ba-4af2-9753-ad87cb0b06cc
domain: BFT_CONSENSUS
name: "BFT_COMMIT_STORE_VOTE"
exergy_cost: 1.2
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:bdbe27fb
---

# BFT_COMMIT_STORE_VOTE

## Causal Invariant
```text
CommitMap[PeerId] == Vote
```

## Description
Logs verified COMMIT vote.
