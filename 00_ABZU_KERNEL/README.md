# 📦 00_ABZU_KERNEL — Crates Nativos de Bajo Nivel y Especificaciones (`00_ABZU_KERNEL/`)

> **DOMINIO ARQUITECTÓNICO: `00_ABZU_KERNEL` (`abzu.kernel`)**  
> Ubicación: `00_ABZU_KERNEL/`  
> Alcance de ejecución: Espacio de usuario (`EL0` en macOS ARM64 / C-ABI) y crates `#![no_std]`. Las garantías verificadas se declaran en [`CLAIMS.toml`](../CLAIMS.toml).

Este directorio aloja los sub-crates especializados en `00_ABZU_KERNEL/crates/` y las especificaciones TLA+ en `00_ABZU_KERNEL/formal_verification/`. Los módulos principales del broker de autorización y mediación de efectos se encuentran en [`src/`](../src/README.md), mientras que los crates de herramientas del workspace residen en `crates/` (`b60-lang/`, `babylon-attest/`, `cadt_mediator/`, `eridu-infer/`, `mxc_broker_poc/`).

## 📐 Catálogo de Crates en `00_ABZU_KERNEL/crates/`

| Ruta Relativa | Propósito Funcional | Estado y Alcance |
| :--- | :--- | :--- |
| [`crates/babylon60-kernel/`](./crates/babylon60-kernel/README.md) | Sustrato `#![no_std]`, planificador sexagesimal `F60` (`Q32.32`), ISA `.b60`, cadena Merkle `BLAKE3` y cuarentena forense en memoria. | Biblioteca `#![no_std]` compilable y testeada |
| [`crates/babylon60-compiler/`](./crates/babylon60-compiler/README.md) | Compilador y parser del DSL `.b60` hacia bytecode IR y emisor de trazas para Lean 4 (`lean_backend.py`). | Alpha / Compilador DSL |
| `crates/babylon60-fuzz/` | Harnesses de *fuzzing* para parsers y primitivas del kernel. | Pruebas de fuzzing |
| `crates/nul-zk/` | Circuitos y primitivas experimentales de conocimiento cero sobre Arkworks. | Experimental |
| [`crates/strike-rs/`](./crates/strike-rs/README.md) | Acelerador nativo PyO3 con hashing topológico `BLAKE3` (`exergy_binary_ipc.rs`) y pruebas de concepto sobre memoria compartida. | Experimental (PyO3 / IPC) |
| `formal_verification/BabylonBFT.tla` | Especificación formal en TLA+ (`BabylonBFT.tla` y `BabylonBFT.cfg`) del protocolo de consenso BFT. | Especificación formal TLA+ |

## 🛡️ Pautas de Diseño de la Cámara
- **Alineación C-ABI explícita:** Estructuras compartidas como `SharedManifest` mantienen layout fijo de 64 bytes (`align(64)`) verificado en tiempo de compilación y en tests (`inv_01_manifest_layout`).
- **Separación de primitivas criptográficas:** `BLAKE3` como digest canónico on-wire y de cadena de eventos (`ledger.rs`, `exergy_binary_ipc.rs`); `SHA-256` reservado para pre-hashes hardware NIST P-256 y testigos de precondición en `src/`.
- **Compilación determinista:** Validar siempre cambios en crates con `cargo check -q --locked` o `cargo test --locked`.
