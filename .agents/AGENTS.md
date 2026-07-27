# BABYLON-60 — OPERATIONAL INVARIANTS & SYSTEM RULES

## Project-Scoped Rules & Structural Invariants

### Non-Silent Collision Fail-Fast (BFT Integrity)
- **INV_BFT_04:** SQLite committer functions and persistence layers must never perform silent `INSERT OR IGNORE` on primary key / `mutation_hash` collisions without validating payload equality. If `payload_hash` differs on collision, the engine MUST immediately raise `ValueError("Fail-fast: INV_BFT_04 Collision...")` and abort the transaction.

### Raw 32-Byte OP_RETURN Payload Encoding
- **INV_C5_15:** `L1_sink` Bitcoin `OP_RETURN` script payloads must store the raw 32-byte Merkle root hash (`bytes.fromhex(merkle_root).hex()`) rather than double-ASCII hex strings or truncated 160-bit strings, preserving 100% of the 256-bit commitment in 32 bytes on-chain.

### Sovereign Dual-Licensing Invariant
- **INV_C5_17:** Every component, service, model, database, app, and subagent workflow in the BABYLON-60 ecosystem MUST be 100% free, open-source, and sovereign for individuals, independent developers, and non-commercial usage.

### Zero-Worktree Swarm Scaling (Prevención de ENOSPC)
- **INV_C5_18:** For large parallel agent swarms ($N \ge 10$), creating physical disk Git Worktrees that consume storage and trigger ENOSPC is strictly prohibited. Swarm scaling must use in-memory AgencyHypervisor multi-tenant handles and single-writer BFT actors.

### Graph Isomorphism Weisfeiler-Lehman 1-WL Pre-Filter
- **INV_C5_28:** Any structural graph comparison (AST isomorphism or network ontology mapping) MUST execute 1-dimensional Weisfeiler-Lehman (1-WL) color refinement hashing ($O(V+E)$) before attempting exact bijection (VF2/NAUTY). If WL hashes differ, the engine MUST collapse instantly in $O(1)$ without wasting ATP on $O(N!)$ combinatorial search.

### AST Control Flow Nesting Depth Ceiling ($\le 4$)
- **GELABP_DEPTH_INVARIANT:** All Python source code within `babylon60/` and `scripts/` MUST maintain a maximum control flow nesting depth $\le 4$ per top-level function across all AST control structures (`ClassDef`, `FunctionDef`, `If`, `For`, `While`, `Try`, `With`).
