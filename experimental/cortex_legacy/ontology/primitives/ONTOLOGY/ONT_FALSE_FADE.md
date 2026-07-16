---
id: ab78a960-471c-4197-b0d1-ab55aa12b0f2
domain: ONTOLOGY
name: "ONT_FALSE_FADE"
exergy_cost: 0.8
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:40:59.127435:50eadb65
---

# ONT_FALSE_FADE

## Causal Invariant
```text
W(t+1) = W(t) * decay(F)
```

## Description
Gradually decays the weight of nodes that fail periodic falsification checks.
