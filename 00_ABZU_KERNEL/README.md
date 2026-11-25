# 📦 00_ABZU_KERNEL — Crates Nativos de Bajo Nivel y Especificaciones (`00_ABZU_KERNEL/`)

> **DOMINIO ARQUITECTÓNICO: `00_ABZU_KERNEL` (`abzu.kernel`)**  
> Ubicación: `00_ABZU_KERNEL/`  
> Alcance de ejecución: Espacio de usuario (`EL0` en macOS ARM64 / C-ABI) y crates `#![no_std]`. Las garantías verificadas se declaran en [`CLAIMS.toml`](../CLAIMS.toml).

Este directorio aloja los sub-crates especializados en `00_ABZU_KERNEL/crates/` y las especificaciones TLA+ en `00_ABZU_KERNEL/formal_verification/`. Los módulos principales del broker de autorización y mediación de efectos se encuentran en [`src/`](../src/README.md), mientras que los crates de herramientas del workspace residen en `crates/` (`b60-lang/`, `babylon-attest/`, `cadt_mediator/`, `eridu-infer/`, `mxc_broker_poc/`).

## 📐 Catálogo de Crates en `00_ABZU_KERNEL/crates/`

| Ruta Relativa | Propósito Funcional | Estado y Alcance |
| :--- | :--- | :--- |
| [`crates/babylon60-kernel/`](./crates/babylon60-kernel/README.md) | Sustrato `#![no_std]`, planificador nominal a 60 Hz (`Q32.32` cuantizado), ISA `.b60`, cadena Merkle `BLAKE3` y cuarentena forense en memoria. | Biblioteca `#![no_std]` compilable y testeada |
| [`crates/babylon60-compiler/`](./crates/babylon60-compiler/README.md) | Parser de un subconjunto ISA, frontend de asignaciones/alloc/free y emisor experimental de trazas Lean 4. | Alpha / Compilador DSL |
| `crates/babylon60-proof-ir/` | Estructuras de obligaciones e invariantes abstractos; no es un verificador. | Biblioteca auxiliar |
| `crates/babylon60-runtime/` | Intérprete con racionales de base 60 (`BigInt`), independiente del evaluador ISA. | Runtime experimental |
| `crates/babylon60-fuzz/` | Harnesses de *fuzzing* para parsers y primitivas del kernel. | Pruebas de fuzzing |
| `crates/nul-zk/` | Generador experimental de IR de circuitos y código fuente Arkworks; no acredita pruebas ZK ejecutadas. | Experimental |
| [`crates/strike-rs/`](./crates/strike-rs/README.md) | Acelerador nativo PyO3 con hashing topológico `BLAKE3` (`exergy_binary_ipc.rs`) y pruebas de concepto sobre memoria compartida. | Experimental (PyO3 / IPC) |
| `formal_verification/BabylonBFT.tla` | Especificación formal en TLA+ (`BabylonBFT.tla` y `BabylonBFT.cfg`) del protocolo de consenso BFT. | Modelo TLA+ acotado; ejecución TLC no acreditada aquí |

## Límites de convergencia y perfil mínimo

- Q32.32: cada tick usa floor(2^32/60) = 71582788 unidades; el déficit es 16 unidades cada 60 ticks, aproximadamente 0.322 ms/día antes de saturación. El reloj lógico cuenta ticks, no segundos físicos.
- El runtime representa racionales num/60^scale, y AFTER exige ticks enteros no negativos. El parser ISA del compiler no acepta AFTER ni BA.EXACT. No existe una equivalencia de ejecución general demostrada entre estas capas (NO_VERIFICADO).
- TLA+ especifica TypeOK, StrictConsensus y Termination bajo weak fairness para tres agentes y quórum dos; no demuestra BFT de red ni una cota temporal física. Sin resultado TLC nuevo.
- La telemetría PMU del scheduler distingue None (no disponible) de Some(0); los contadores no miden energía. NUL-ZK prueba IR y texto generado, no generación/verificación de pruebas criptográficas.
- El perfil nativo mínimo selecciona explícitamente el paquete y las features existentes. Los experimentos permanecen en el workspace y su CI integral, sin cambiar Cargo.lock ni los formatos persistidos.

```sh
cargo check --locked -p babylon60_root --lib --no-default-features --features microkernel
cargo check --locked -p babylon60-kernel --lib
cargo test --locked -p babylon60-kernel
cargo test --locked -p babylon60-compiler
cargo test --locked -p babylon60-runtime
cargo test --locked -p nul-zk
```

Estos comandos son recetas de verificación, no recibos de ejecución. La evidencia normativa se delimita en [CLAIMS.toml](../CLAIMS.toml).

## 🛡️ Pautas de Diseño de la Cámara
- **Alineación C-ABI explícita:** Estructuras compartidas como `SharedManifest` mantienen layout fijo de 64 bytes (`align(64)`) verificado en tiempo de compilación y en tests (`inv_01_manifest_layout`).
- **Separación de primitivas criptográficas:** `BLAKE3` como digest canónico on-wire y de cadena de eventos (`ledger.rs`, `exergy_binary_ipc.rs`); `SHA-256` reservado para pre-hashes hardware NIST P-256 y testigos de precondición en `src/`.
- **Compilación determinista:** Validar siempre cambios en crates con `cargo check -q --locked` o `cargo test --locked`.
