---
id: 36b704f3-8a34-403a-9c6f-7cb913ac155d
domain: CRYPTOGRAPHY
name: "BLIND_SIGNATURE_SIGN"
exergy_cost: 5.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:d468d4ff
---

# BLIND_SIGNATURE_SIGN

## Causal Invariant
```text
\sigma' = Sign(K_{priv}, M')
```

## Description
Sign a blinded message.
