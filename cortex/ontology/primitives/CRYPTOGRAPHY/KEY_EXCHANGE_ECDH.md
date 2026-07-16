---
id: 8710cc56-b7eb-48f7-bf98-7bc121036462
domain: CRYPTOGRAPHY
name: "KEY_EXCHANGE_ECDH"
exergy_cost: 10.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:48c47caa
---

# KEY_EXCHANGE_ECDH

## Causal Invariant
```text
Z = ECDH(d_A, Q_B) = d_A Q_B = d_B Q_A
```

## Description
Perform Elliptic Curve Diffie-Hellman key exchange.
