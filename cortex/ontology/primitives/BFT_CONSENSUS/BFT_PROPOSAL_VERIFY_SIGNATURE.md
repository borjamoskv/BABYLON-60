---
id: 5c0ca87d-dc2a-46a8-833e-780001348f08
domain: BFT_CONSENSUS
name: "BFT_PROPOSAL_VERIFY_SIGNATURE"
exergy_cost: 2.1
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:1b6d228d
---

# BFT_PROPOSAL_VERIFY_SIGNATURE

## Causal Invariant
```text
Verify(PubKey, Hash, Sig) == TRUE
```

## Description
Validates cryptographic signature of received proposal.
