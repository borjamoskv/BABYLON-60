---
id: d9093f57-04fc-4ca9-beba-04189ca30f68
domain: BFT_CONSENSUS
name: "BFT_VIEW_CHANGE_INIT"
exergy_cost: 0.7
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:e0f1d1b0
---

# BFT_VIEW_CHANGE_INIT

## Causal Invariant
```text
NewView == CurrentView + 1
```

## Description
Triggers epoch transition due to timeout.
