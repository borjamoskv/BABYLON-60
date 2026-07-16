---
id: 1698ed57-54ef-4d17-98bb-82b3fa998704
domain: CRYPTOGRAPHY
name: "PQC_DILITHIUM_VERIFY"
exergy_cost: 25.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:8d90bf97
---

# PQC_DILITHIUM_VERIFY

## Causal Invariant
```text
b = Dilithium_{verify}(pk, M, \sigma) \in \{0,1\}
```

## Description
Verify a Dilithium signature.
