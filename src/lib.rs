//! # BABYLON-60 — `SharedManifest` formal specification crate
//!
//! Implements four certified invariants for a 64-byte, cache-line–resident,
//! lock-free IPC slot on AArch64/ARMv9 (Apple Silicon + server ARM):
//!
//! | Invariant | Module | Guarantee |
//! |-----------|--------|-----------|
//! | INV-1 | [`manifest`] | C-ABI layout, 64 B, align(64), zero padding waste |
//! | INV-2 | [`seqlock`]  | SPMC seqlock; readers pure-load; no RFO |
//! | INV-3 | [`thermodynamics`] | Landauer floor, Dynamis/Entelecheia bisimulation |
//! | INV-4 | [`halt`]     | Fail-stop, POISONED state, RFC 9942 COSE_Sign1 receipt |
//!
//! ## Memory model
//! Targets AArch64 ARMv9 (multicopy-atomic, **not** TSO). All ordering choices
//! are conservative and correct on x86-TSO as well (Acquire/Release compile to
//! `LDAR`/`STLR` on AArch64; to plain MOV on x86).
//!
//! ## EU AI Act compliance hooks
//! [`halt::epistemic_halt`] and [`receipt::emit_halt_receipt`] implement the
//! logging requirements of Art. 12 and the transparency obligations of Art. 50
//! of Regulation (EU) 2024/1689 ("EU AI Act"). The halt receipt is a
//! COSE_Sign1 signed statement per RFC 9942 + SCITT-22 with SHAKE256 (−45).
//!
//! ## Safety constraints
//! * `Arc` is **prohibited on the hot path** — its refcount reintroduces the
//!   RMW contention eliminated by the seqlock design.
//! * The `SharedManifest` is designed for `mmap`/`static` residence; no `Drop`
//!   should be called on it while other threads may be reading.
//! * In production, use `Box::leak` or a static pool; never pass by value.

// Formally Verified Invariants INV-1..4 — BABYLON-60 IPC Specification

#![deny(unsafe_op_in_unsafe_fn)]
#![warn(missing_docs)]

/// Módulo de halt epistémico y fail-stop.
pub mod halt;
/// Módulo de definición del layout C-ABI `SharedManifest`.
pub mod manifest;

/// Módulo de generación de recibos COSE_Sign1.
#[cfg(feature = "halt-receipt")]
pub mod receipt;

/// Módulo de integridad criptográfica Append-Only (WORM Ledger).
#[cfg(feature = "cortex-persist")]
pub mod worm;
/// Módulo de sincronización lock-free seqlock SPMC.
pub mod seqlock;
/// Módulo de invariantes termodinámicos y bisimulación.
pub mod thermodynamics;
/// Módulo de constantes de calibración topológica de Aphairesis auto-generado.
pub mod generated_aphairesis_constants;
/// Módulo de canal lock-free Single-Producer Single-Consumer (SPSC) Zero-Copy.
pub mod spsc_ring;
/// Módulo de Telemetría Termodinámica y medición de ciclos de reloj.
pub mod telemetry;
/// Módulo de Consenso Isostático BFT de la Tríada de Larsa (Ring-0).
pub mod larsa_bft;
pub mod aot_oracle;
pub mod z3_oracle;
/// Módulo del Kernel Matemático Sexagesimal F60 (Matemática de Enki).
pub mod f60;
/// Módulo de Cálculo Exterior Discreto (DEC) y Complejo de De Rham (Iteraciones 31-32).
pub mod dec;
/// Módulo de Termodinámica de la Información y Cota de Landauer para Navier-Stokes (Iteraciones 81-90).
pub mod fluid_thermo;
/// Módulo de Síntesis Soberana, SCITT L5 y Punto Fijo Omega (Iteraciones 91-100).
pub mod omega_synthesis;

/// Módulo de interfaz C-ABI (FFI) para integración C/C++.
pub mod ffi;
pub mod ffi_oracle;

/// Módulo de atestación física biométrica (Apple Secure Enclave).
#[cfg(feature = "std")]
pub mod enclave;

pub use manifest::{HaltReason, SharedManifest, POISONED, RUNNING, MAX_RETRIES};
pub use spsc_ring::SpscRingBuffer;


#[cfg(feature = "cortex-persist")]
pub mod cortex;
pub use seqlock::{publish, read};

#[cfg(feature = "python")]
/// FFI bridge for Python (PyO3). Exposed when `python` feature is enabled.
pub mod ffi_python;
