---
id: 89d1fa6b-bd6e-40f2-91b7-1a0a5328ab89
domain: METACOGNITION
name: "Attention_Decay_Audit"
exergy_cost: 22.0
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:41:17.248676:1633717a
---

# Attention_Decay_Audit

## Causal Invariant
```text
Salience(t) > Salience(t+1)
```

## Description
Audits the loss of token salience across the context window.
