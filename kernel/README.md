# ⚙️ BABYLON-60 Low-Level Kernel (`kernel/`)

[![Rust](https://img.shields.io/badge/Rust-1.80%2B-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![no_std](https://img.shields.io/badge/no__std-Bare--Metal_Ready-brightgreen?style=for-the-badge)]()
[![Formal Verification](https://img.shields.io/badge/Lean_4-Verified_Causality-green?style=for-the-badge)](../BabylonTrace.lean)

The **BABYLON-60 Kernel** is a `#![no_std]` high-assurance Rust crate providing the core execution engine, exact sexagesimal (`F60`) scheduler, WORM forensic quarantine system, Merkle-causal ledger actor, and B60 ISA evaluation engine.

---

## 🔬 Substrate Modules

| Module | Location | Description |
| :--- | :--- | :--- |
| **Scheduler** | [`scheduler/`](./src/scheduler) | Exact sexagesimal (`F60`) time-slice manager (`0;20` exact 20-min ticks, zero `f64` floating point drift). |
| **Forensic Quarantine** | [`forensic_quarantine/`](./src/forensic_quarantine) | Immutable WORM (Write-Once-Read-Many) cryptographic state preservation upon panic or anomaly detection. |
| **B60 ISA** | [`isa.rs`](./src/isa.rs) | Bytecode Instruction Set Architecture definition for deterministic causal coroutines. |
| **Evaluator** | [`eval.rs`](./src/eval.rs) | Pure evaluation loop enforcing single-step causal transition bounds. |
| **Ledger Actor** | [`ledger.rs`](./src/ledger.rs) | Single-writer tamper-evident Merkle hash-chain manager. |
| **State Machine** | [`state.rs`](./src/state.rs) | Memory-bounded state transition register with SHA-256 state vector verification. |

---

## ⚡ Technical Highlights

1. **`#![no_std]` Compatibility**: Compiles with `extern crate alloc;`, enabling execution inside Secure Enclaves (ARM TrustZone, AWS Nitro Enclaves, Intel SGX/TDX) and bare-metal environments.
2. **Zero Floating-Point Drift**: All temporal calculations use exact sexagesimal fractions ($F_{60}$), eliminating rounding accumulation across agent runs.
3. **Forensic Freeze Guarantee**: When an assertion fails, state is instantly serialized into a signed WORM payload before termination, ensuring evidence is preserved for regulatory inspection (EU AI Act Art. 12).

---

## 🛠️ Verification & Testing

```bash
# Test kernel crate in workspace
cargo test -p babylon60_kernel

# Run benchmarks
cargo bench -p babylon60_kernel
```

---

<sub>BABYLON-60 Low-Level Kernel · `#![no_std]` Rust Substrate · Borja Moskv</sub>
