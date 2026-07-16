---
id: 85151d34-15e9-47b3-8922-c4aee060fc66
domain: CRYPTOGRAPHY
name: "ENCRYPT_SYMMETRIC"
exergy_cost: 2.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:58f837af
---

# ENCRYPT_SYMMETRIC

## Causal Invariant
```text
C_{payload} = E_k(P_{payload})
```

## Description
Perform symmetric encryption on a plaintext payload using an established key.
