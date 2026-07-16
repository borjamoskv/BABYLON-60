---
id: 7d73e358-69d9-4b1c-9272-9a437b9461e6
domain: BFT_CONSENSUS
name: "BFT_CRYPTO_VERIFY_AGGREGATE"
exergy_cost: 8.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:66c50415
---

# BFT_CRYPTO_VERIFY_AGGREGATE

## Causal Invariant
```text
VerifyAggregate(PubKeys, Payload, AggSig) == TRUE
```

## Description
Verifies compressed multi-signature.
