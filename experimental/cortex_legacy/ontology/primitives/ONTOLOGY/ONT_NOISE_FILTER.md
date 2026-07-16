---
id: 56792142-a027-425e-8415-a2500f955bd0
domain: ONTOLOGY
name: "ONT_NOISE_FILTER"
exergy_cost: 1.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:40:59.127435:b5dbbc10
---

# ONT_NOISE_FILTER

## Causal Invariant
```text
Signal / (Signal + Noise) > 0.9
```

## Description
Applies a low-pass filter on inbound ontological updates, dropping stochastic fluff.
