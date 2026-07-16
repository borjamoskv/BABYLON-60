---
id: a05b63c4-ee27-4472-9124-76f650764a8a
domain: CRYPTOGRAPHY
name: "HASH_SHA1_UNSAFE"
exergy_cost: 0.8
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:c6fc250a
---

# HASH_SHA1_UNSAFE

## Causal Invariant
```text
H = SHA1(P)
```

## Description
Compute the SHA-1 hash of a payload (Unsafe, for legacy support only).
