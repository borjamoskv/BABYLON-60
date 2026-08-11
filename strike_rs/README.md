# ⚡ BABYLON-60 Strike RS Engine (`strike_rs/`)

[![PyO3 Native](https://img.shields.io/badge/PyO3-Native_Bindings-blue?style=for-the-badge&logo=python)](https://pyo3.rs/)
[![Iceoryx2 Zero-Copy](https://img.shields.io/badge/Iceoryx2-Shared_Memory_IPC-orange?style=for-the-badge)](https://github.com/eclipse-iceoryx/iceoryx2)
[![BLAKE3](https://img.shields.io/badge/BLAKE3-Fast_Causal_Taint-brightgreen?style=for-the-badge)](https://github.com/BLAKE3-team/BLAKE3)

**`strike_rs`** is the ultra-fast Rust acceleration engine bridging Python (`cortex-persist`) with native compiled speed. It bypasses Python's Global Interpreter Lock (GIL) via PyO3, evaluates the Causal Poset DAG using BLAKE3 topological hashing, and enables microsecond zero-copy IPC via Iceoryx2 shared memory.

---

## 🎯 High-Performance Core Modules & C Structs

```
┌─────────────────────────────────────────────────────────────┐
│                 Python Substrate (cortex-persist)           │
├─────────────────────────────────────────────────────────────┤
│                 PyO3 GIL-Bypass Bindings Layer              │
├──────────────────────────────┬──────────────────────────────┤
│  BLAKE3 Taint Engine         │  Iceoryx2 Shared Memory IPC  │
│  (Kahn's Invariant DAG)      │  (bft_iceoryx2.rs)           │
├──────────────────────────────┼──────────────────────────────┤
│  AUTODIDACT-Ω Engine         │  Active Thermodynamic Memory │
│  (omega0.rs)                 │  (atms.rs / kda_memory.rs)   │
└──────────────────────────────┴──────────────────────────────┘
```

### Zero-Copy Shared Memory Message Layout (`bft_iceoryx2.rs`)

```rust
#[repr(C)]
pub struct BftMessage {
    pub sender_id: u64,
    pub view: u64,
    pub seq_num: u64,
    pub payload_hash: [u8; 32], // 32-byte Merkle root hash
    pub signature: [u8; 64],    // Ed25519 signature
}
```

- **Zero-Copy Publisher/Subscriber (`run_abft_publisher_poc` / `run_abft_subscriber_poc`)**: Transfers `BftMessage` instances across process boundaries using OS shared memory handles without serializing or socket overhead.

---

## ⚡ Technical Invariants

| Invariant | Code | Description |
| :--- | :--- | :--- |
| **Kahn's Acyclicity** | `INV-GCM-003` | Causal Poset graph must be a strict DAG. Cycles trigger instant `TaintError::CycleDetected`. |
| **Zero Memory Leak** | `Owned CausalNode` | Poset node instances are stack/owned structures, preventing memory leaks in dynamic graphs. |
| **BLAKE3 Determinism**| `compute_cortex_taint` | Topologically sorted nodes emit immutable deterministic `TAINT:C5_REAL_RUST:<hash>`. |
| **Zero-Worktree Scaling**| `INV_C5_18` | Inter-process BFT message exchange over Iceoryx2 shared memory without socket starvation. |

---

## 🛠️ Build & Verification

```bash
# Test Rust crate
cargo test -p strike_rs

# Build PyO3 wheel for local Python environment
maturin develop --manifest-path strike_rs/Cargo.toml
```

---

<sub>BABYLON-60 Strike RS · Native GIL Bypass & Zero-Copy IPC · Borja Moskv</sub>
