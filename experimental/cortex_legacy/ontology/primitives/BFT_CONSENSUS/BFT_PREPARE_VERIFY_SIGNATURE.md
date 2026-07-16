---
id: 3b8e42c2-6a81-4c16-8f11-a710b32d9e16
domain: BFT_CONSENSUS
name: "BFT_PREPARE_VERIFY_SIGNATURE"
exergy_cost: 2.1
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:2c630da2
---

# BFT_PREPARE_VERIFY_SIGNATURE

## Causal Invariant
```text
Verify(PeerPubKey, VoteHash, VoteSig) == TRUE
```

## Description
Validates peer signature on PREPARE vote.
