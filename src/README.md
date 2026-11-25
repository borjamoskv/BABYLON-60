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

---

## Ingeniería de descriptores y confinamiento anti-TOCTOU

Las rutas basadas en cadenas de texto (`&str` / `Path`) son vulnerables a carreras TOCTOU (*Time-Of-Check to Time-Of-Use*), intercambio de enlaces simbólicos intermedios y colisiones de dentry entre la verificación de la política y la llamada al sistema. BABYLON-60 reemplaza la resolución por nombre por una arquitectura de descriptores anclados a inodo en [`src/capability.rs`](./capability.rs), [`src/secure_fs.rs`](./secure_fs.rs), [`crates/babylon-skills-mcp/src/lib.rs`](../crates/babylon-skills-mcp/src/lib.rs) y [`01_KISH_ENGINE/babylon60/mcp/skills_snapshot.py`](../01_KISH_ENGINE/babylon60/mcp/skills_snapshot.py):

### 1. Raíces de Capacidad Ancladas a Descriptor (`ScopedHandle` — `FL_008`)
En [`src/capability.rs`](./capability.rs), cada raíz autorizada se abre mediante:
```rust
libc::open(c_path.as_ptr(), libc::O_RDONLY | libc::O_DIRECTORY | libc::O_CLOEXEC | libc::O_NOFOLLOW)
```
Inmediatamente se ejecuta `libc::fstat(fd, &mut stat)` sobre el descriptor abierto para fijar la tupla física inmutable `ScopedHandle { requester_id: [u8; 32], dirfd: RawFd, dev: stat.st_dev, ino: stat.st_ino }`. Toda operación posterior exige coincidencia del padre causal (`verify_causal_parent`) y desciende desde `dirfd` sin volver a evaluar rutas absolutas.

### 2. Descenso Componente a Componente sin Symlinks (`resolve_confined_parent_nofollow`)
En [`src/secure_fs.rs`](./secure_fs.rs), `resolve_confined_parent_nofollow(root_fd, rel_path)` rechaza rutas vacías, rutas absolutas (`Component::RootDir`), prefijos y saltos `..` (`Component::ParentDir`). Para cada directorio intermedio $c_i$ de la ruta relativa:
1. Abre el componente hijo relativo al descriptor actual con:
   ```rust
   libc::openat(curr_fd, dir_c.as_ptr(), libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC)
   ```
2. Cierra deterministamente el descriptor intermedio previo (`libc::close(curr_fd)` y `Drop` sobre `ResolvedParentDir`) antes de avanzar al siguiente nivel.
3. Abre el objeto hoja mediante `openat_confined_nofollow` añadiendo `libc::O_NOFOLLOW | libc::O_CLOEXEC`.
4. Cualquier error del kernel `ELOOP`, `EMLINK` o `ENOTDIR` se traduce de forma fail-closed en `SecureFsError::SymlinkEscapeAttempt`.

### 3. Estabilización de Identidad y Estado sobre el Descriptor (`ObjectIdentity::from_fd`)
La estructura `ObjectIdentity` separa el localizador físico inmutable en el VFS (`ObjectLocatorIdentity { dev, ino, file_type, capability_root_id }`) del estado del contenido (`ObjectState { hash, size, mode }`):
- Verifica `fstat(fd)` exigiendo un archivo regular (`(st_mode & S_IFMT) == S_IFREG`).
- Calcula el digest `SHA-256` leyendo desde un descriptor duplicado (`libc::dup(fd)` -> `SeekFrom::Start(0)` en `compute_fd_hash`).
- Ejecuta un *bracket* TOCTOU volviendo a invocar `fstat(fd)` tras el cálculo del hash y comprobando la invariancia de `(st_dev, st_ino, st_size, st_mtime, st_mtime_nsec)`. Si un escritor concurrente altera el archivo durante la lectura, reintenta hasta `MAX_STABILIZATION_ATTEMPTS = 5` y aborta con `SecureFsError::IdentityUnstable` si no converge.

### 4. Mutación sobre el Mismo Descriptor y Cuarentena Atómica (`AUTH_004` / `AUTH_007`)
- **`MUTATE_FILE` (`NativeSecureFs::secure_mutate`):** Abre el objetivo con `openat_confined_nofollow(root_fd, rel_path, libc::O_RDWR)`, comprueba sobre ese mismo `fd` que `(st_dev, st_ino)` y el `SHA-256` actual coincidan con `authorized_identity`, escribe en bucle controlado con `libc::pwrite`, ajusta tamaño con `libc::ftruncate(fd, len)` y sincroniza con `libc::fsync(fd)` antes de calcular el `post_hash` y cerrar el descriptor.
- **`DELETE_FILE` (`QuarantineContext` + `quarantine` + `verify_quarantined` + `destroy_quarantined`):**
  1. **Inicialización confinada (`QuarantineContext::initialize`):** Abre `<root>` con `O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC`, comprueba `st_uid == geteuid()` y desciende a `.babylon/quarantine` vía `libc::mkdirat(..., 0o700)` + `libc::openat(..., O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)` + `libc::fchmod(fd, 0o700)`, verificando pertenencia al mismo `st_dev` (`EXDEV` aborta con `CrossDeviceUnsupported`).
  2. **Aislamiento atómico de dentry:** Mueve el archivo desde `resolved_src.dir_fd` al descriptor `quarantine_fd` sin seguir symlinks ni sobrescribir entradas existentes (`renameatx_np(..., RENAME_EXCL | RENAME_NOFOLLOW_ANY)` en macOS; `renameat2(..., RENAME_NOREPLACE)` en Linux).
  3. **Re-verificación post-aislamiento (`VerifiedTx`):** Reabre el objeto dentro de `quarantine_fd` con `O_RDONLY | O_NOFOLLOW | O_CLOEXEC`, recalcula `ObjectIdentity::from_fd` y verifica `(dev, ino, state.hash)` antes de emitir el token lineal `#[must_use] VerifiedTx`.
  4. **Destrucción y observación física (`NEM-I2` / `NEM-I3`):** Ejecuta `libc::unlinkat(quarantine_fd, c_name, 0)` y comprueba la desaparición del dentry mediante `libc::fstatat(quarantine_fd, c_name, &mut check_stat, libc::AT_SYMLINK_NOFOLLOW) != 0`. Cualquier descriptor preabierto retenido por el proceso se revoca activamente (`close()` forzando `EBADF` en `guard_open_descriptor_isolation`) al entrar en cuarentena (`NEM-I3`) o cambiar de época (`NEM-I6`).

### 5. Persistencia de Nonces, WAL Binario e Ingesta MCP sin TOCTOU
- **Cerrojo y registros en cuarentena (`EffectTxOrchestrator`):** Adquiere `.epoch_fence.bin` dentro de `quarantine.dir_fd` mediante `openat(..., O_CREAT | O_EXCL | O_RDWR | O_NOFOLLOW | O_CLOEXEC, 0o600)` + `libc::flock(fd, libc::LOCK_EX)`, y lee `.consumed_nonces.bin`, `.effect_wal.bin` y `.nonce_intent_<hex>` con `O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK`.
- **Snapshot inmutable de Skills y Adaptadores MCP:** Tanto el servidor Rust ([`crates/babylon-skills-mcp/src/lib.rs`](../crates/babylon-skills-mcp/src/lib.rs), `read_bytes_nofollow`) como el servidor Python ([`01_KISH_ENGINE/babylon60/mcp/skills_snapshot.py`](../01_KISH_ENGINE/babylon60/mcp/skills_snapshot.py), `_read_bytes_nofollow`) y el adaptador de Codex ([`01_KISH_ENGINE/babylon60/adapters/codex/mcp_server.py`](../01_KISH_ENGINE/babylon60/adapters/codex/mcp_server.py)) abren catálogos y artefactos con `O_RDONLY | O_NOFOLLOW` (y `O_DIRECTORY` en directorios de sesión), verifican `S_ISREG(st_mode)` sobre `fstat(fd)` y sirven las consultas posteriores desde RAM.
