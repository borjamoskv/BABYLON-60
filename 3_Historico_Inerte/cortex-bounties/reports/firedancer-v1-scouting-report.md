# Firedancer V1 Audit - Forensic Scouting Report [C5-REAL]

**Target:** Firedancer V1 (Solana Independent Validator)
**Reward Threshold:** Up to $1M+ (Critical Consensus/Safety)
**Audit Window:** Closes May 9, 2026

---

## 🏗️ Architectural Overview (Tiles & Shmem)
Firedancer is a **multi-process, tile-based** validator written in C. 
- **Tiles:** Individual processes pinned to CPU cores (Networking, Verification, Banking).
- **Communication:** Lock-free shared memory channels (`disco`, `mcache`).
- **Memory:** Pre-allocated huge/gigantic pages (`fd_wksp`). No standard heap in hot paths.

---

## ⚡ High-Exergy Attack Vectors

### Vector 1: `fd_funk` Fork-Aware State Corruption
The `funk` module manages the in-memory Accounts Database across multiple ledger forks.
- **Root Cause:** Complexity in **Fork Pruning and Branching**. 
- **Exploit Hypothesis:** A malicious validator sends a sequence of blocks that triggers rapid forking and pruning. If `fd_funk_prune` fails to correctly handle a parent-child relationship during a race condition between Bank tiles, it could reclaim memory for a record that is still needed by an active fork.
- **Impact:** Use-after-free in shared memory -> State corruption -> Bank Hash divergence.

### Vector 2: `fd_vm` SBF Conformance & MMU Bypass
Firedancer implements its own SBF (Solana BPF) Virtual Machine in C.
- **Root Cause:** Mismatch in **Integer Overflow** or **MMU Validation**.
- **Exploit Hypothesis:** SBF programs often perform complex pointer arithmetic. If the `fd_vm_mmu_load/store` logic has an off-by-one error or fails to handle address wraparound correctly, a program could access memory outside its mapped regions (e.g., other accounts or tile metadata).
- **Impact:** Consensus failure (Bank Hash mismatch) or Sandbox Escape.

### Vector 3: `mcache` Sequence Wraparound Race
Tiles communicate via `mcache` ring buffers using sequence numbers.
- **Root Cause:** **Atomic Sequence Logic** under extreme load.
- **Exploit Hypothesis:** By flooding the `quic` tile with specifically timed UDP/QUIC fragments, an attacker might trigger a race condition where the `verify` tile reads a fragment before the `quic` tile has finished writing its metadata, due to a missing memory fence (`FD_COMPILER_MFENCE`) or an unexpected 64-bit sequence wraparound.
- **Impact:** Validator panic (DoS) or malformed transaction injection.

---

## 🛠️ Next Steps: Operational Strike
1. **Target `src/funk/fd_funk.c`:** Audit the `fd_funk_txn_commit` and `fd_funk_recyc` routines.
2. **Target `src/flamenco/vm/fd_vm.c`:** Audit the opcode handlers for `LDX`/`STX` and the `gas` calculation.
3. **Execution:** Prepare a Soroban/Rust contract that generates extreme branching to stress the `funk` store.

---
**Crystallized by:** Antigravity (CORTEX Swarm)
**Status:** C5-REAL Scouting Phase Complete.
**Action:** Ready for deep-code dissection.
