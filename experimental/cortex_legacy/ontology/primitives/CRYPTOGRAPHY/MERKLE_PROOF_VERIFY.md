---
id: ae3f6015-2dca-49c2-81fc-cf838d0df751
domain: CRYPTOGRAPHY
name: "MERKLE_PROOF_VERIFY"
exergy_cost: 1.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:cf0b367e
---

# MERKLE_PROOF_VERIFY

## Causal Invariant
```text
b = VerifyMerkleProof(R, L_i, \pi) \in \{0,1\}
```

## Description
Verify a Merkle proof against a root hash.
