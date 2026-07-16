---
id: cb7ca2af-f8ab-4d57-8c06-72f4dbea9282
domain: CRYPTOGRAPHY
name: "KEY_WRAP_AES_KW"
exergy_cost: 4.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:a16318c9
---

# KEY_WRAP_AES_KW

## Causal Invariant
```text
C = AES\_KW(KEK, PlainKey)
```

## Description
Wrap a key using AES Key Wrap.
