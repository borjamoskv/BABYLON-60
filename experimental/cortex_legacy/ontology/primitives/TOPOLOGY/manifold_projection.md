---
id: 9ff27d7f-61d4-4f2f-8b6e-4ba99c66b63c
domain: TOPOLOGY
name: "manifold_projection"
exergy_cost: 12.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:40:57.329856:888e96ff
---

# manifold_projection

## Causal Invariant
```text
dim(M_in) > dim(M_out) && dist_local(x,y) == dist_local(P(x),P(y))
```

## Description
Projects high-dimensional state space onto a lower-dimensional manifold while preserving local geodesic invariants.
