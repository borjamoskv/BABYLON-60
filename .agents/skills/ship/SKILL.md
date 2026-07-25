---
name: ship
description: Payload Delivery & Ledger Append. Delivers ETHOS-validated invariants to the BFT SQLite Ledger.
---

# /ship Protocol
Delivers validated payloads to the BFT Ledger via `cortex-cmd ship`.
Appends to `babylon60_ide.db` with WAL mode and issues Git Sentinel commits.
