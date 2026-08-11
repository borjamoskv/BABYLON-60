# ⚡ BABYLON-60 Strike RS Engine (`strike_rs/`)

[![PyO3 Native](https://img.shields.io/badge/PyO3-Native_Bindings-blue?style=for-the-badge&logo=python)](https://pyo3.rs/)
[![Iceoryx2 Zero-Copy](https://img.shields.io/badge/Iceoryx2-Shared_Memory_IPC-orange?style=for-the-badge)](https://github.com/eclipse-iceoryx/iceoryx2)
[![BLAKE3](https://img.shields.io/badge/BLAKE3-Fast_Causal_Taint-brightgreen?style=for-the-badge)](https://github.com/BLAKE3-team/BLAKE3)

**`strike_rs`** is the ultra-fast Rust acceleration engine bridging Python (`cortex-persist`) with native compiled speed. It bypasses Python's Global Interpreter Lock (GIL) via PyO3, evaluates the Causal Poset DAG using BLAKE3 topological hashing, and enables microsecond zero-copy IPC via Iceoryx2 shared memory.

---

## 🎯 High-Performance Core Modules

```
┌─────────────────────────────────────────────────────────────┐
│                 Python Substrate (cortex-persist)           │
├─────────────────────────────────────────────────────────────┤
│                 PyO3 GIL-Bypass Bindings Layer              │
├──────────────────────────────┬──────────────────────────────┤
│  BLAKE3 Taint Engine         │  Iceoryx2 Zero-Copy IPC      │
│  (Kahn's Invariant DAG)      │  (bft_iceoryx2.rs)           │
├──────────────────────────────┼──────────────────────────────┤
│  AUTODIDACT-Ω Engine         │  Active Thermodynamic Memory │
│  (omega0.rs)                 │  (atms.rs / kda_memory.rs)   │
└──────────────────────────────┴──────────────────────────────┘
```

- **Causal Taint Engine (`lib.rs`)**: BLAKE3-based topological hashing enforcing Kahn's Acyclicity Invariant (`INV-GCM-003`).
- **Iceoryx2 Zero-Copy IPC (`bft_iceoryx2.rs`)**: Inter-process memory sharing with microsecond latencies between Tauri frontend and Rust/Python backends.
- **AUTODIDACT-Ω Engine (`omega0.rs`)**: High-throughput symbolic inference engine.
- **Active Thermodynamic Memory (`atms.rs` / `kda_memory.rs`)**: Exergy-bounded state eviction and kinetic cache management.

---

## ⚡ Technical Invariants

| Invariant | Code | Description |
| :--- | :--- | :--- |
| **Kahn's Acyclicity** | `INV-GCM-003` | Causal Poset graph must be a strict DAG. Cycles trigger instant `TaintError::CycleDetected`. |
| **Zero Memory Leak** | `Owned CausalNode` | Poset node instances are stack/owned structures, preventing memory leaks in dynamic graphs. |
| **BLAKE3 Determinism**| `compute_cortex_taint` | Topologically sorted nodes emit immutable deterministic `TAINT:C5_REAL_RUST:<hash>`. |

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
