---
id: e78b9922-0f4c-404e-9eb7-a365b58a6f15
domain: CRYPTOGRAPHY
name: "MULTI_SIGNATURE_VERIFY"
exergy_cost: 15.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:20b01da5
---

# MULTI_SIGNATURE_VERIFY

## Causal Invariant
```text
b = Verify_{MS}(\{pk_1, ..., pk_n\}, M, \Sigma) \in \{0,1\}
```

## Description
Verify a multi-signature against a set of public keys.
