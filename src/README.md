# 🦀 SRC — Broker de Autorización, Mediación y Primitivas en Rust (`src/`)

> **NÚCLEO EN ESPACIO DE USUARIO (`EL0` / C-ABI)**  
> Ubicación: `src/`  
> Contiene la biblioteca raíz de Rust (`babylon60_root`) y los binarios nativos que implementan las garantías `L1_FORMAL`–`L4_EXPERIMENTAL` declaradas en [`CLAIMS.toml`](../CLAIMS.toml).

---

## 📐 Estructura Real de Módulos (`src/`)

```
src/
├── bin/
│   ├── babylon60_kernel.rs      # Binario de diagnóstico y benchmark secuencial Seqlock
│   ├── babylon_authorityd.rs    # Demonio de autoridad y mediación sobre socket Unix
│   ├── babylon_top.rs           # Monitor de telemetría en terminal
│   ├── tamkarum.rs              # Ejecutor CLI del gate presupuestario TAMKARUM-60
│   └── tour.rs                  # Recorrido verificable de primitivas del broker
├── lib.rs                       # Punto de entrada y reexportaciones del crate raíz
├── manifest.rs & shared_manifest_core.rs # Layout SharedManifest de 64 bytes (align 64, C-ABI)
├── seqlock.rs                   # Protocolo Seqlock SPMC (modelo acotado en Loom)
├── spsc.rs & spsc_ring.rs       # Colas circulares SPSC sin bloqueos
├── executor.rs & executor_ipc.rs# Despacho único (AUTH_001..003) y frontera AF_UNIX (AUTH_002)
├── secure_fs.rs                 # Cuarentena atómica, defensa anti-TOCTOU (AUTH_004/007) y .effect_wal.bin (BLAKE3)
├── omega_mediation.rs           # Mediación completa INV-OMEGA, Seatbelt macOS y despacho firmado P-256
├── capability.rs & admission.rs # Broker de capacidades acotadas (FL_008) y control de admisión (FL_007)
├── acs_bridge.rs                # Guardia OWASP ACS v0.1.0, reconciliación VOP-1 y detección de deriva (FL_016)
├── enclave.rs                   # Verificación criptográfica NIST P-256 (FIPS 186-4 SHA-256 pre-hash)
├── receipt.rs                   # Recibos firmados con Ed25519 según RFC 9942 (cose_ed25519_receipt)
├── halt.rs                      # Parada determinista Fail-Stop (0xDEAD_6060) y evidencia de parada (AUTH_005)
├── worm.rs                      # Cadena de hashes en memoria con detección de manipulación (worm_durability)
├── larsa.rs & larsa_bft.rs      # Quórum de verificación heterogéneo local 2/3 (Rust, Lean 4, Z3)
├── lean_emitter.rs, z3_oracle.rs, aot_oracle.rs & ffi_oracle.rs # Puentes de verificación formal
├── tamkarum.rs                  # Compuerta presupuestaria KudurruBudgetGate (64 B, criterio de Kelly)
├── f60.rs & dec.rs              # Aritmética sexagesimal exacta y cálculo exterior discreto (DEC)
├── ffi.rs & ffi_python.rs       # Enlaces C-ABI y PyO3
└── thermodynamics.rs & telemetry.rs # Modelos de coste informacional y telemetría local
```

---

## 🔍 Correspondencia con `CLAIMS.toml`

1. **Memoria Compartida y Concurrencia (`manifest.rs`, `seqlock.rs`):**
   - `inv_01_manifest_layout`: `SharedManifest` de exactamente 64 bytes y alineado a 64 bytes.
   - `inv_02_seqlock_concurrency`: Protocolo Seqlock SPMC verificado en su modelo con Loom (`seqlock_loom`).
2. **Autorización de Un Solo Uso y Mediación Completa (`executor.rs`, `secure_fs.rs`, `omega_mediation.rs`):**
   - `AUTH_001`–`AUTH_007`: Rechazo de replays tras `SIGKILL` y reapertura del ledger, aislamiento por socket Unix, transición a `UNKNOWN` sin reintentos automáticos ciegos, y cuarentena atómica con `O_NOFOLLOW` y `renameatx_np`/`renameat2`.
   - `INV_OMEGA_complete_mediation` y `FL_014`: Confinamiento de procesos en macOS (`sandbox-exec`) y registro WAL binario de 154 bytes protegido con `BLAKE3` (`.effect_wal.bin`).
3. **Capacidades, Admisión y Recibos (`capability.rs`, `admission.rs`, `receipt.rs`, `enclave.rs`, `halt.rs`):**
   - `FL_007` y `FL_008`: Control de admisión acotado por Ley de Little y handles de capacidad acoplados a `dev/ino` y época de política.
   - `cose_ed25519_receipt`, `secure_enclave_p256` y `AUTH_005`: Emisión de recibos Ed25519 RFC 9942, verificación P-256 con pre-hash `SHA-256` y prohibición de firmas sintéticas o rellenas de ceros ante fallos.

---

## 🛠️ Comandos de Compilación y Verificación

```bash
# Comprobación rápida de tipos con lockfile congelado
cargo check -q --locked

# Pruebas unitarias de la biblioteca principal
cargo test --locked --lib

# Campaña de mediación completa (INV-OMEGA) y pruebas adversariales NEMESIS
cargo test --locked --features cortex-persist --test omega_mediation_campaign
cargo test --locked --features cortex-persist --test adversarial_nemesis
```
