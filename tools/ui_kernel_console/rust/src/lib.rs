//! Emisor y verificador de referencia, en Rust, del recibo de ejecución que comprueba
//! `tools/ui_kernel_console` en el navegador.
//!
//! Es una propuesta del cliente: ningún componente del kernel emite todavía este formato. Lo que sí
//! comparte con el kernel, y cómo se contrasta:
//!
//! - Merkle BLAKE3 v1: [`merkle_b3`] es el archivo `crates/babylon-attest/src/merkle_b3.rs` del
//!   kernel compilado tal cual, de modo que hojas y raíz son las del kernel por construcción.
//! - Perfil CBOR restringido y `Sig_structure` COSE_Sign1: [`cbor`] replica las funciones de
//!   `src/acs_bridge.rs` y se contrasta con `tests/acs_cbor_golden.txt`.
//! - Ed25519 con `verify_strict` de ed25519-dalek, la misma versión que fija el kernel.
//!
//! Frente a la implementación TypeScript, el crate reproduce byte a byte el recibo dorado
//! (`tests/fixtures/goldenReceipt.ts`) y aplica las mismas reglas y códigos de fallo; el arnés
//! `scripts/differential.mjs` compara ambas sobre recibos aleatorios y alterados.
//!
//! El binding WebAssembly (característica `wasm`) solo expone verificación: una página no debe
//! custodiar claves privadas.

#![cfg_attr(not(feature = "wasm"), forbid(unsafe_code))]
#![cfg_attr(feature = "wasm", deny(unsafe_code))]
#![warn(missing_docs)]

// Archivo del kernel compilado tal cual: `rustfmt::skip` impide que `cargo fmt` lo reescriba.
#[rustfmt::skip]
#[path = "../../../../crates/babylon-attest/src/merkle_b3.rs"]
pub mod merkle_b3;

pub mod canonical;
pub mod cbor;
pub mod json_text;
pub mod point;
pub mod schema;
pub mod seal;
pub mod verify;

// El código que genera `#[wasm_bindgen]` contiene bloques `unsafe`; el nuestro, ninguno.
#[cfg(feature = "wasm")]
#[allow(unsafe_code)]
mod wasm;
