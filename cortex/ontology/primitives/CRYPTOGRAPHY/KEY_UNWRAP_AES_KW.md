---
id: d77f3fda-4b95-4fb2-98c2-16e58121f22e
domain: CRYPTOGRAPHY
name: "KEY_UNWRAP_AES_KW"
exergy_cost: 4.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:6143123e
---

# KEY_UNWRAP_AES_KW

## Causal Invariant
```text
PlainKey = AES\_UNWRAP(KEK, C) \lor \bot
```

## Description
Unwrap a key using AES Key Wrap.
