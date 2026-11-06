# ⚙️ BABYLON-60 Low-Level Kernel (`00_ABZU_KERNEL/crates/babylon60-kernel/`)

[![Rust](https://img.shields.io/badge/Rust-≥1.89-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![no_std](https://img.shields.io/badge/no__std-Bare--Metal_Ready-brightgreen?style=for-the-badge)]()
[![Formal Verification](https://img.shields.io/badge/Lean_4-Verified_Causality-green?style=for-the-badge)](../../../proof/lean/BabylonTrace.lean)
[![Criterion Benchmarks](https://img.shields.io/badge/Benchmarks-Criterion_F60_&_WORM-purple?style=for-the-badge)](./benches/thermo_benches.rs)

The **`babylon60-kernel`** crate is a `#![no_std]` Rust library providing the exact sexagesimal (`F60`) Q32.32 scheduler, in-memory forensic quarantine snapshot, BLAKE3 Merkle-causal event ledger, and `.b60` ISA evaluation engine.

---

## 🔬 Substrate Modules

| Module | Location | Description |
| :--- | :--- | :--- |
| **Scheduler** | [`scheduler/`](./src/scheduler) | Exact sexagesimal (`F60`) Q32.32 time-slice manager (`0;20` exact ticks, zero `f64` floating-point drift). |
| **Forensic Quarantine** | [`forensic_quarantine/`](./src/forensic_quarantine) | In-memory snapshot (`QuarantineSnapshot::freeze`) with 64-bit FNV-1a integrity checksum upon anomaly detection (persistent durability is delegated to SQLite WAL in `01_KISH_ENGINE`). |
| **B60 ISA** | [`isa.rs`](./src/isa.rs) | Bytecode Instruction Set Architecture definition for deterministic causal coroutines. |
| **Evaluator** | [`eval.rs`](./src/eval.rs) | Pure evaluation loop enforcing single-step causal transition bounds. |
| **Ledger Actor** | [`ledger.rs`](./src/ledger.rs) | Single-writer tamper-evident Merkle hash-chain manager using canonical `BLAKE3` domain-separated digests. |
| **State Machine** | [`state.rs`](./src/state.rs) | Memory-bounded state transition register. |
| **Shared Manifest & SCITT** | [`shared_manifest.rs`](./src/shared_manifest.rs) · [`scitt.rs`](./src/scitt.rs) | 64-byte C-ABI manifest layout (`shared_manifest_core.rs`) and SCITT envelope helpers. |
| **Entropy & Thermo** | [`semantic_entropy.rs`](./src/semantic_entropy.rs) · [`thermodynamics.rs`](./src/thermodynamics.rs) | Entropy metrics and thermodynamic accounting primitives. |

---

## ⚡ Technical Invariants

1. **`#![no_std]` Compatibility**: Compiles with `extern crate alloc;`, suitable for embedded or constrained user-space substrates.
2. **Zero Floating-Point Drift**: Temporal calculations use exact Q32.32 sexagesimal fractions ($F_{60}$), eliminating rounding accumulation across runs.
3. **In-Memory Quarantine Snapshot**: Captures deterministic state (`QuarantineSnapshot::freeze`) before halting execution.

---

## 🛠️ Verification & Criterion Benchmarks

```bash
# Test kernel crate in workspace
cargo test --locked -p babylon60-kernel

# Run Criterion micro-benchmarks (benches/thermo_benches.rs)
cargo bench --locked -p babylon60-kernel
```

### Benchmark Suite (`benches/thermo_benches.rs`)
- `f60_scheduler_cycle_benchmark`: Measures Q32.32 fixed-point addition cycle latency.
- `worm_snapshot_serialization_benchmark`: Benchmarks freeze latency for 1KB and 1MB memory dumps under quarantine.

---

<sub>BABYLON-60 Low-Level Kernel · `#![no_std]` Rust Substrate · Borja Moskv</sub>
