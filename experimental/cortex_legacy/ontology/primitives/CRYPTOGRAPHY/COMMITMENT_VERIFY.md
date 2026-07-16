---
id: 717b5342-cec6-42e3-a776-f2b411efd2d5
domain: CRYPTOGRAPHY
name: "COMMITMENT_VERIFY"
exergy_cost: 2.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:3c9ca536
---

# COMMITMENT_VERIFY

## Causal Invariant
```text
b = VerifyCommit(C, v, r) \in \{0,1\}
```

## Description
Verify a cryptographic commitment given the value and opening factor.
