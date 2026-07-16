---
id: 170f7577-0fd4-4cd1-835d-14cf73f68621
domain: CRYPTOGRAPHY
name: "RING_SIGNATURE_VERIFY"
exergy_cost: 30.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:03f2ec75
---

# RING_SIGNATURE_VERIFY

## Causal Invariant
```text
b = RingVerify(M, R, \sigma) \in \{0,1\}
```

## Description
Verify a ring signature against a set of public keys (the ring).
