---
id: e95ee307-300e-4b06-9ef3-e8f7eec61a6a
domain: CRYPTOGRAPHY
name: "MERKLE_TREE_ROOT"
exergy_cost: 5.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:d67a116a
---

# MERKLE_TREE_ROOT

## Causal Invariant
```text
R = MerkleTree(L_1, ..., L_n)
```

## Description
Compute the root hash of a Merkle tree from a list of leaves.
