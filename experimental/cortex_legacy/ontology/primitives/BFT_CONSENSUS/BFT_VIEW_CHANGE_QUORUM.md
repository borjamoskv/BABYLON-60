---
id: dfa79cfe-8e02-4133-aee2-27d509b848f8
domain: BFT_CONSENSUS
name: "BFT_VIEW_CHANGE_QUORUM"
exergy_cost: 0.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:7ced469c
---

# BFT_VIEW_CHANGE_QUORUM

## Causal Invariant
```text
Count(ViewChangeMap) >= 2f + 1
```

## Description
Verifies 2f+1 VIEW_CHANGE messages.
