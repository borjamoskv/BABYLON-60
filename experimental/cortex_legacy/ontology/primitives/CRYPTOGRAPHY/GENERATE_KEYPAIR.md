---
id: a3a1d7c2-d7a0-420d-af81-c3481c86b5dc
domain: CRYPTOGRAPHY
name: "GENERATE_KEYPAIR"
exergy_cost: 15.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:0b92538d
---

# GENERATE_KEYPAIR

## Causal Invariant
```text
(K_{pub}, K_{priv}) = Gen(1^\lambda)
```

## Description
Generate an asymmetric keypair (public and private keys).
