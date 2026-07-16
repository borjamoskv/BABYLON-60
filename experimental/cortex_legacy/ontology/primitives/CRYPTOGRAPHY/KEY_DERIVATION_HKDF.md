---
id: 80a61d12-5824-4a8d-9001-81b896f3e617
domain: CRYPTOGRAPHY
name: "KEY_DERIVATION_HKDF"
exergy_cost: 1.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:39:25.206640:0057da51
---

# KEY_DERIVATION_HKDF

## Causal Invariant
```text
K = HKDF_{extract\_and\_expand}(salt, IKM, info, L)
```

## Description
Derive cryptographic keys from input keying material using HKDF.
