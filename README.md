# BABYLON-60

**Autoridad de ejecución para agentes de IA.** El modelo propone efectos; el broker aplica política, comprueba una autorización ligada a la operación y media la ejecución sobre recursos protegidos. Implementación Rust/Python en espacio de usuario (EL0), no en el kernel.

**Estado:** candidato v5.0.0 (alpha de seguridad). La mediación completa exige aislar el proceso del agente: si conserva acceso directo al recurso o al ledger, puede eludir el broker. Inventario de afirmaciones y niveles de evidencia: [`CLAIMS.toml`](./CLAIMS.toml).

## Frontera de ejecución

```text
Agente confinado
  -> EffectRequest
  -> validación de política, firma, nonce y época
  -> capacidad ligada a recurso y tipo de efecto
  -> syscall mediada sobre descriptor
  -> observación y registro del resultado
```

Las propiedades de la implementación (L2), del confinamiento del sistema operativo (L3) y de las campañas adversariales (L4) no son equivalentes. [Modelo de seguridad](./docs/01_spec/spec_security_model.md) · [Declaraciones verificables](./CLAIMS.toml).

## Seguridad de rutas: `O_DIRECTORY` / `O_NOFOLLOW`

Fuentes: [`src/capability.rs`](./src/capability.rs), [`src/secure_fs.rs`](./src/secure_fs.rs).

### Capacidad anclada al descriptor

`ScopedHandle::new` abre el directorio raíz con:

```rust
libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC
```

`fstat(fd)` registra `st_dev` y `st_ino`; el handle conserva el descriptor y el `requester_id`. `verify_causal_parent` comprueba la identidad del solicitante. `O_DIRECTORY` exige un directorio y `O_NOFOLLOW` evita seguir un enlace simbólico en el último componente de esa apertura. No valida automáticamente los ancestros de la ruta utilizada para abrir la raíz.

### Resolución relativa, componente a componente

`resolve_confined_parent_nofollow` rechaza rutas absolutas y `..`. Desde `root_fd` abre cada directorio intermedio mediante:

```rust
libc::openat(
    parent_fd,
    component,
    libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
)
```

La hoja se abre con `openat` y `O_NOFOLLOW | O_CLOEXEC`. El broker obtiene la identidad con `fstat` sobre el descriptor abierto, no volviendo a consultar el nombre de ruta. `ObjectIdentity::from_fd` registra `dev`, `ino`, tipo, modo, tamaño y SHA-256 de los bytes. La lectura se acota con `fstat -> hash -> fstat` y se rechaza una identidad que permanezca inestable.

Estas operaciones limitan las carreras por sustitución de symlinks. No impiden que otro actor autorizado escriba sobre el mismo inodo, ni neutralizan por sí solas hardlinks, descriptores preabiertos o acceso directo fuera del broker.

### `DELETE_FILE`: cuarentena antes de destrucción

La ruta de eliminación utiliza:

1. Comprobación de autorización, época, efecto y precondición.
2. `renameatx_np(RENAME_EXCL | RENAME_NOFOLLOW_ANY)` en macOS o `renameat2(RENAME_NOREPLACE)` en Linux hacia `.babylon/quarantine/`. La cuarentena se abre por descriptores, se fija a permisos `0700` y se exige el mismo dispositivo.
3. Reapertura en cuarentena y comprobación de `st_dev`, `st_ino` y SHA-256 frente a la identidad autorizada.
4. `unlinkat` únicamente tras la verificación y comprobación del resultado.

`MUTATE_FILE` comprueba identidad y prehash y escribe sobre el mismo descriptor mediante `pwrite`, `ftruncate` y `fsync`. La recuperación utiliza registros `AttemptReserved`, `OutcomeUnknown` y `OutcomeKnown`. Si una interrupción deja una operación irreversible sin recibo, `AmbiguousOutcomeRequiresReconciliation` bloquea el reintento automático hasta reconciliar el nonce con el estado observado.

`0700` no constituye un sandbox frente a código con el mismo UID o mayor privilegio. El alcance declarado es un sistema de archivos local, una cuarentena controlada por el broker y operaciones dentro del mismo dispositivo. No se extrapola a NFS, sistemas remotos ni a cortes de alimentación a partir de pruebas con `SIGKILL`.

## Matriz criptográfica por subsistema

Los tres algoritmos coexisten con funciones y formatos distintos. No son intercambiables.

| Algoritmo | Aplicación verificada en código | Referencia |
| :--- | :--- | :--- |
| **BLAKE3** | Árbol Merkle v1 para atestación, con dominios separados para hoja/nodo/raíz, cardinalidad y prefijo `b3:`. Revisión de archivos en MCP local. | [`merkle_b3.rs`](./crates/babylon-attest/src/merkle_b3.rs), [`merkle_b3.py`](./01_KISH_ENGINE/babylon60/attestation/merkle_b3.py), [`babylon60_mcp.py`](./tools/babylon60_mcp.py) |
| **SHA-256** | Contenido y pre/postestado de archivos leídos a través de FD; digest de los 122 bytes del registro `.effect_wal.bin`; hashes de argumentos, tokens y evidencia en el broker de capacidades. | [`secure_fs.rs`](./src/secure_fs.rs), [`capability.rs`](./src/capability.rs) |
| **SHA3-256** | Encadenamiento del ledger CORTEX Python sobre JSON canónico y Merkle del subsistema heredado. | [`cortex_crypto_kernel.py`](./01_KISH_ENGINE/babylon60/bft/cortex_crypto_kernel.py), [`cortex_persist_ledger.py`](./01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py) |

**Diferencia entre documentación y ejecución:** los comentarios de `WalRecord` citan BLAKE3, pero `WalRecord::new` y `WalRecord::from_bytes` ejecutan `Sha256::digest`. El formato efectivo de ese WAL es SHA-256 en esta revisión. No debe etiquetarse como BLAKE3 sin modificar y migrar el formato. El contrato y el nivel de evidencia por componente figuran en [`CLAIMS.toml`](./CLAIMS.toml).

## Instalación y ejecución

CLI y servidor MCP de memoria por stdio; Python 3.11+, `uv` y checkout limpio:

```bash
git clone https://github.com/borjamoskv/BABYLON-60.git
cd BABYLON-60
bash install.sh --dry-run
bash install.sh
.venv/bin/babylon60 --help
.venv/bin/babylon60-mcp --ledger /ruta/ledger.db
```

El instalador usa `uv sync --locked --no-dev`. El paquete fuente se obtiene con `bash scripts/package_release.sh /ruta/de/salida`. El [servidor MCP del kernel](./docs/03_guides/guide_kernel_mcp.md) necesita el checkout completo y su entorno independiente. El [contrato de presentación](./01_KISH_ENGINE/babylon60/presentation.md) es informativo; lo renderiza la aplicación anfitriona.

Las acciones críticas requieren una [autorización firmada](./docs/03_guides/guide_signed_authorization.md) vinculada al efecto:

```bash
.venv/bin/babylon60 approve <execution_id> --task-file <task.json>
```

Una fila de auditoría sin firma válida no concede permiso.

## Evidencia reproducible

Comandos indicados por el [registro de claims](./CLAIMS.toml). Un resultado positivo solo respalda la propiedad y el entorno efectivamente ensayados.

```bash
python3 scripts/c5_quality_gates/verify_claims.py --list
cargo test --locked --lib secure_fs
cargo test --locked --test adversarial_nemesis --features cortex-persist
cargo test --locked --features cortex-persist --test admission_capability_test test_fl008
cargo test --locked --test nemesis_wave4 --features cortex-persist
```

| Nivel | Alcance |
| :--- | :--- |
| L1 | Propiedades del modelo formal, no del binario completo. |
| L2 | Controles de la implementación y sus pruebas. |
| L3 | Confinamiento real del proceso bajo un perfil del sistema operativo. |
| L4 | Ensayos adversariales acotados al entorno y las hipótesis descritos. |

## Seguridad y licencia

[`SECURITY.md`](./SECURITY.md) · [`LICENSE`](./LICENSE) · [`COMMERCIAL_LICENSE.md`](./docs/COMMERCIAL_LICENSE.md) · [Documentación](./docs/).

BABYLON-60 v5.0.0 · Borja Moskv
