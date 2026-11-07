# ⚡ BABYLON-60 Strike RS Engine (`00_ABZU_KERNEL/crates/strike-rs/`)

[![PyO3 Native](https://img.shields.io/badge/PyO3-Native_Bindings-blue?style=for-the-badge&logo=python)](https://pyo3.rs/)
[![Iceoryx2 PoC](https://img.shields.io/badge/Iceoryx2-Shared_Memory_PoC-orange?style=for-the-badge)](https://github.com/eclipse-iceoryx/iceoryx2)
[![BLAKE3](https://img.shields.io/badge/BLAKE3-Canonical_MAC_&_DAG-brightgreen?style=for-the-badge)](https://github.com/BLAKE3-team/BLAKE3)

**`strike_rs`** (`00_ABZU_KERNEL/crates/strike-rs/`) is an experimental Rust/PyO3 acceleration crate that provides native `BLAKE3` keyed MAC framing (`exergy_binary_ipc.rs`), causal DAG evaluation (`bft_engine.rs`), ATMS bitmask propagation (`atms.rs`), and shared-memory IPC proofs of concept (`bft_iceoryx2.rs`). *(Note: `strike_rs` is an experimental accelerator and is not part of the release-blocking claims in [`CLAIMS.toml`](../../../CLAIMS.toml)).*

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
cargo test --locked --manifest-path 00_ABZU_KERNEL/crates/strike-rs/Cargo.toml

# Build PyO3 wheel for local Python environment
maturin develop --manifest-path 00_ABZU_KERNEL/crates/strike-rs/Cargo.toml
```

---

<sub>BABYLON-60 Strike RS · Native GIL Bypass & Zero-Copy IPC · Borja Moskv</sub>
