---
id: fd6a3810-c66f-442b-ac19-22a61d519456
domain: CRYPTOGRAPHY
name: "KEY_EXCHANGE_X25519"
exergy_cost: 5.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:9088a7f1
---

# KEY_EXCHANGE_X25519

## Causal Invariant
```text
K = X25519(a, P_b) = a P_b
```

## Description
Perform key exchange using the X25519 elliptic curve.
