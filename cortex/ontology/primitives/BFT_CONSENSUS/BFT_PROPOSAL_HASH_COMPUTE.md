---
id: 4dac1acd-716b-49ca-9a16-7fdb1261da6e
domain: BFT_CONSENSUS
name: "BFT_PROPOSAL_HASH_COMPUTE"
exergy_cost: 1.1
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:8fe5ef5b
---

# BFT_PROPOSAL_HASH_COMPUTE

## Causal Invariant
```text
Hash == BLAKE3(Payload) AND Collisions == 0
```

## Description
Calculates BLAKE3 hash of serialized proposal.
