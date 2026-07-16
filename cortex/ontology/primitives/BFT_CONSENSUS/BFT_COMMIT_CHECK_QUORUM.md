---
id: 2335cf02-983a-478e-9728-2ef1759c1cdb
domain: BFT_CONSENSUS
name: "BFT_COMMIT_CHECK_QUORUM"
exergy_cost: 0.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:2a9144e7
---

# BFT_COMMIT_CHECK_QUORUM

## Causal Invariant
```text
Count(CommitMap) >= 2f + 1
```

## Description
Checks if COMMIT votes reach 2f+1 threshold.
