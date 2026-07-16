---
id: 63c9da33-7c53-4ea8-a218-074bd1c71bef
domain: BFT_CONSENSUS
name: "BFT_COMMIT_PERSIST_LEDGER"
exergy_cost: 5.4
cortex_taint: CORTEX-TAINT:borjamoskv:batch_crystallize:2026-07-16T16:42:12.004135:70673630
---

# BFT_COMMIT_PERSIST_LEDGER

## Causal Invariant
```text
Fsync executed on Ledger.db
```

## Description
Writes final block and state root to WAL SQLite.
