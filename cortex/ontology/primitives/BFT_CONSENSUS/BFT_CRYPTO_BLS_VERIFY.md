---
id: 9ce5a7d8-d597-401f-aa29-055d9bb8bffe
domain: BFT_CONSENSUS
name: "BFT_CRYPTO_BLS_VERIFY"
exergy_cost: 6.8
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:5e961f2b
---

# BFT_CRYPTO_BLS_VERIFY

## Causal Invariant
```text
e(g1, sig) == e(pubkey, hash)
```

## Description
Executes bilinear pairing for BLS validation.
