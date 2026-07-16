---
id: 3798c22c-705c-4106-87d6-c26c6d1180d4
domain: CRYPTOGRAPHY
name: "HASH_MD5_UNSAFE"
exergy_cost: 0.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:13df511e
---

# HASH_MD5_UNSAFE

## Causal Invariant
```text
H = MD5(P)
```

## Description
Compute the MD5 hash of a payload (Unsafe, for legacy support only).
