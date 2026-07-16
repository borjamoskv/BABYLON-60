---
id: 118182a2-13a8-48b4-ae2b-081150652d9e
domain: BFT_CONSENSUS
name: "BFT_COMMIT_EXECUTE_STATE"
exergy_cost: 8.5
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:a88968e9
---

# BFT_COMMIT_EXECUTE_STATE

## Causal Invariant
```text
StateRoot == Hash(Execute(Block.Txs))
```

## Description
Applies block transactions to deterministic state machine.
