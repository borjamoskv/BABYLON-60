---
id: f5aa6111-666f-44e9-93cd-d2b73f113905
domain: BFT_CONSENSUS
name: "BFT_SLASHING_DETECT_EQUIVOCATION"
exergy_cost: 1.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:9ab60698
---

# BFT_SLASHING_DETECT_EQUIVOCATION

## Causal Invariant
```text
Hash(Vote1) != Hash(Vote2) AND Vote1.Height == Vote2.Height
```

## Description
Detects two distinct signatures for same height and view.
