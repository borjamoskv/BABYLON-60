# Errata Normativa y Desglose de Garantías — Release v5.1.0

**Versión afectada:** `v5.1.0` (commit de evidencia `cd9762abe25808b5b00c79ad82b6076e7d3e28b2`, proyección pública `66ec0e30a8d19b8562e134e3c1eacda404944add`)  
**Raíz Merkle de evidencia:** `sha3-256:411e0639ecb6239f73bee9483865abae653b4931dcfa49b984f5340f38eeea20`  
**Digest `CLAIMS.toml`:** `d4ca80d4e82978ce6e0ff5572a425f4126179e9e891fae2b3fe1b97c850e070d`  

---

## 1. Correcciones de Presentación y Empaquetado de `v5.1.0`

1. **Separación entre estado de aceptación (`verified`) y estrato de evidencia (`L1`–`L4`):**  
   El resumen original de la release `v5.1.0` resumió erróneamente las 9 entradas con `status = "verified"` como *"9 rigorous formal claims"*. En [`CLAIMS.toml`](../../CLAIMS.toml) y [`evidence.json`](../../evidence.json), estado de ejecución y método de validación son ejes ortogonales:
   - **Total de claims registradas:** `28` (`suite_passed = true` en las 28 entradas).
   - **Distribución por estrato de evidencia (`evidence_level`):** `2 L1_FORMAL`, `17 L2_IMPLEMENTATION`, `2 L3_ISOLATION`, `7 L4_EXPERIMENTAL`.
   - **Distribución por estado (`status` en `v5.1.0`):** `9 verified` (`1 L1_FORMAL + 7 L2_IMPLEMENTATION + 1 L4_EXPERIMENTAL`), `17 verified_local` (`1 L1_FORMAL + 8 L2_IMPLEMENTATION + 2 L3_ISOLATION + 6 L4_EXPERIMENTAL`), `1 verified_in_memory` (`L2_IMPLEMENTATION`) y `1 partial_trace` (`L2_IMPLEMENTATION`).
2. **Sincronización de recibos OpenTimestamps (`.ots`) con los JSON publicados:**  
   Los archivos `RELEASE_MANIFEST.json` (`3858fa126516f99317954212998a040afbf871e9f229d15cab164575ddd01f53`) y `evidence.json` (`4b9ee61a2fda42618f49db805629c82cc6b36e54ad4f28a99d98c2c15e3d5239`) de `v5.1.0` corresponden a las pruebas `.ots` de `3.983` bytes ancladas en el bloque Bitcoin `974890` (`RELEASE_MANIFEST.json.ots`: `83b88695f296a1066db19aea22bb7ece8595fe527dc5bc52429570c11acbd9f3`; `evidence.json.ots`: `db0a7a2c8cf5143115eeec559be822043a6e1687a80ea6b2f06f2d1eec1e12ea`). En el árbol público inicial `66ec0e30a8d1` habían quedado los `.ots` previos de `1.946` bytes (bloque `974412`).
3. **Cierre fail-closed de `--bundle` en el verificador autónomo:**  
   [`scripts/verify_release.sh`](../../scripts/verify_release.sh) exige ahora una referencia `release_bundle.sha256` válida en [`RELEASE_MANIFEST.json`](../../RELEASE_MANIFEST.json) siempre que el usuario invoca `--bundle <ruta>`; si `release_bundle` es `null`, aborta en modo `FAIL-CLOSED` (`Exit 1`) en lugar de omitir la comparación del paquete.
4. **Compatibilidad del instalador con `--profile terminal-mcp`:**  
   [`install.sh`](../../install.sh) e [`install.ps1`](../../install.ps1) aceptan explícitamente `--profile terminal-mcp` (y `--profile=terminal-mcp`) además de `--dry-run`, `--client codex` y `--mcp`.
5. **Formato persistido de `.effect_wal.bin` (`SHA-256` sobre 122 bytes):**  
   El registro binario de `154` bytes en `.effect_wal.bin` ([`src/secure_fs.rs`](../../src/secure_fs.rs)) calcula un resumen `SHA-256` sobre sus primeros `122` bytes (`SHA256_LEGACY_EFFECT_WAL`). `BLAKE3` (`INV_C5_ONWIRE_CANON`) rige tramas IPC, digestos de herramientas MCP y árboles Merkle conformes v1 (`b3:`), sin reinterpretar bytes legados ya persistidos en disco.
6. **Delimitación de privilegios (`EL0`) y firma de manifiesto:**  
   La denominación `Ring-0` identifica la capa arquitectónica de custodia (`00_ABZU_KERNEL`); el binario se ejecuta en espacio de usuario (`EL0`) y requiere confinamiento del sistema operativo (`L3_ISOLATION`: `sandbox-exec` / Seatbelt) para mediar procesos de agentes. El tag Git `v5.1.0` está firmado, mientras que `RELEASE_MANIFEST.json` declara `signing_authority.scope = "unsigned_local_evidence"` (`signature: null`).

---

## 2. Matriz Resumen por Estrato y Estado (`28` Claims)

| Estrato (`evidence_level`) | Total | `verified` | `verified_local` | `verified_in_memory` | `partial_trace` | Alcance real acreditado |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`L1_FORMAL`** | **2** | 1 | 1 | 0 | 0 | Model checking acotado en Loom sobre réplica SPMC (1 escritor, 1–2 lectores, máx. 2 preempciones) y teoremas Lean 4 sobre trazas abstractas (`TraceReadsEven`, `countDispatches <= 1`). |
| **`L2_IMPLEMENTATION`** | **17** | 7 | 8 | 1 | 1 | Pruebas deterministas de implementación en Rust y Python (layout C-ABI de 64 B, `COSE_Sign1` Ed25519, puente P-256 con claves software en test automatizado, SQLite WAL bajo `SIGKILL`, quórum local 2/3, no-replay de nonces). |
| **`L3_ISOLATION`** | **2** | 0 | 2 | 0 | 0 | Confinamiento de procesos en macOS mediante `sandbox-exec` (Seatbelt) e interceptación en la frontera IPC/MCP para recursos protegidos. |
| **`L4_EXPERIMENTAL`** | **7** | 1 | 6 | 0 | 0 | Campañas adversariales y de estrés (`SIGKILL` en 1.000 corridas, cuarentena atómica con 100 workers, 10.000 ensayos de capacidades MCP, `FL-014`/`FL-016`). |
| **Total** | **28** | **9** | **17** | **1** | **1** | Raíz Merkle `sha3-256:411e0639ecb6239f73bee9483865abae653b4931dcfa49b984f5340f38eeea20`. |

---

## 3. Desglose Completo de las 28 Claims por Estrato Real

### Estrato `L1_FORMAL` (2 claims)

| ID de Claim | Componente | Estado (`v5.1.0`) | Propiedad y límites declarados en [`CLAIMS.toml`](../../CLAIMS.toml) |
| :--- | :--- | :--- | :--- |
| `inv_02_seqlock_concurrency` | `00_ABZU_KERNEL` | `verified` | Modelo SPMC Seqlock (réplica Loom de `seqlock.rs`, 1 escritor × 1–2 lectores) sin lecturas desgarradas bajo *bounded model checking* (máx. 2 preempciones); no modela directamente todo el código de producción ni mide tráfico `RFO`. |
| `lean4_formal_trace` | `00_ABZU_KERNEL` | `verified_local` | Sobre trazas abstractas aceptadas, `BabylonTrace` demuestra secuencias de lectura pares (`TraceReadsEven`) y `AX0` demuestra `countDispatches <= 1` desde `Proposed`; no modela cargas de payload ni orden de memoria físico en Rust. |

### Estrato `L2_IMPLEMENTATION` (17 claims)

| ID de Claim | Componente | Estado (`v5.1.0`) | Propiedad y límites declarados en [`CLAIMS.toml`](../../CLAIMS.toml) |
| :--- | :--- | :--- | :--- |
| `inv_01_manifest_layout` | `00_ABZU_KERNEL` | `verified` | `SharedManifest` tiene tamaño exacto de 64 bytes, alineación de 64 bytes y offsets documentados; el layout por sí solo no acredita coherencia de caché ni energía. |
| `inv_04_fail_stop_halt` | `00_ABZU_KERNEL` | `verified` | La parada epistémica cierra admisión (`POISONED = 0xDEAD_6060`) y registra evidencia durable sin emitir firmas sintéticas. |
| `cose_ed25519_receipt` | `00_ABZU_KERNEL` | `verified` | Recibos formateados según RFC 9942 (`COSE_Sign1`) y firmados criptográficamente con Ed25519. |
| `cortex_persist_sqlite` | `01_KISH_ENGINE` | `verified` | Ledger persistente SQLite WAL (`PRAGMA synchronous=FULL`, `BEGIN IMMEDIATE`) y encadenamiento legado `SHA3-256` bajo fallos de proceso (`SIGKILL`); corte eléctrico físico permanece `NO_VERIFICADO`. |
| `merkle_attestation` | `01_KISH_ENGINE` | `verified` | Raíces de estado Merkle calculadas de forma determinista y consultables vía MCP. |
| `mcp_authority_gate` | `01_KISH_ENGINE` | `verified` | El servidor MCP impone `AX-0`: clientes estocásticos no pueden auto-autorizar acciones protegidas (nota: en `v5.1.1` pasa a `verified_local` tras ejecución en silicio local). |
| `tamkarum_budget_gate` | `01_KISH_ENGINE` | `verified` | `KudurruBudgetGate` verifica layout de 64 bytes, cotas de Kelly y parada `0xDEAD_6060`. |
| `secure_enclave_p256` | `00_ABZU_KERNEL` | `verified_local` | El puente verifica firmas NIST P-256; su test automatizado utiliza claves por software y no certifica presencia humana interactiva en Touch ID. |
| `heterogeneous_verification_quorum` | `00_ABZU_KERNEL` | `verified_local` | Quórum heterogéneo local 2/3 de verificación sobre 3 motores (Rust, Lean 4, Z3); no constituye consenso BFT distribuido en red. |
| `AUTH_001` | `00_ABZU_KERNEL` | `verified_local` | Una autorización consumida no puede despacharse por segunda vez en el ejecutor, incluso tras muerte del proceso y reapertura del ledger en disco. |
| `AUTH_002` | `00_ABZU_KERNEL` | `verified_local` | Los workers `EDIN` no pueden ejecutar efectos protegidos directamente sin autorización `COSE` verificada en la frontera del socket Unix IPC. |
| `AUTH_003` | `00_ABZU_KERNEL` | `verified_local` | Un despacho sin resultado durable pasa a `UNKNOWN` al reiniciar y nunca se reintenta automáticamente. |
| `AUTH_005` | `00_ABZU_KERNEL` | `verified_local` | Los fallos de firma o persistencia producen errores explícitos; nunca se emite una firma nula o sintética. |
| `FL_007_admission_bounded_liveness` | `00_ABZU_KERNEL` | `verified_local` | `AdmissionController` acota profundidad atómica observada frente a capacidad antes de reservar slot; heurística local sin garantía universal contra inanición. |
| `signed_dispatch_intent` | `00_ABZU_KERNEL` | `verified_local` | La verificación P-256 vincula el intent CBOR canónico completo y consume su nonce en SQLite WAL/FULL antes del despacho, rechazando replay post-`SIGKILL`. |
| `worm_durability` | `00_ABZU_KERNEL` | `verified_in_memory` | `HashChainedLedger` en memoria detecta alteraciones criptográficas en la cadena de hashes. |
| `zero_anergy` | `00_ABZU_KERNEL` | `partial_trace` | Benchmark local de tiempo, throughput y latencia media sobre 1.000.000 de iteraciones Seqlock; no mide tráfico `RFO`, CPU en reposo ni consumo energético (`NO_VERIFICADO`). |

### Estrato `L3_ISOLATION` (2 claims)

| ID de Claim | Componente | Estado (`v5.1.0`) | Propiedad y límites declarados en [`CLAIMS.toml`](../../CLAIMS.toml) |
| :--- | :--- | :--- | :--- |
| `INV_OMEGA_complete_mediation` | `00_ABZU_KERNEL` | `verified_local` | Procesos de agentes confinados con macOS Seatbelt reciben `EPERM` al intentar mutar o desenlazar directamente recursos protegidos o el ledger SQLite; la campaña de 5 pruebas (`BYPASS-001`..`REVOCATION-005`) pasa sobre archivos reales. |
| `mcp_seatbelt_confinement` | `01_KISH_ENGINE` | `verified_local` | El backend MCP en macOS verifica el protocolo stdio real y el confinamiento Seatbelt antes de admitir un candidato, con ejecución acotada y rechazo fail-closed. |

### Estrato `L4_EXPERIMENTAL` (7 claims)

| ID de Claim | Componente | Estado (`v5.1.0`) | Propiedad y límites declarados en [`CLAIMS.toml`](../../CLAIMS.toml) |
| :--- | :--- | :--- | :--- |
| `sharur_100_swarm_concurrency` | `02_EDIN_SWARMS` | `verified` | Enjambre de 100 workers concurrentes sostiene contención sobre el ledger, aplica `AX-0` y rechaza en modo fail-closed los 50 vectores adversariales del arnés. |
| `AUTH_004` | `00_ABZU_KERNEL` | `verified_local` | Un recurso cuyo digest de precondición o identidad de inodo cambia entre autorización y efecto es rechazado antes de mutar; en `DELETE_FILE`, la brecha TOCTOU se cierra por cuarentena atómica y verificación post-rename. |
| `AUTH_006` | `00_ABZU_KERNEL` | `verified_local` | En 1.000 ejecuciones de proceso real cubriendo 3 puntos de inyección `SIGKILL` y control sin fallo, ningún nonce produce más de un efecto y todo replay de autorización archivada es rechazado. |
| `AUTH_007_secure_fs_quarantine` | `00_ABZU_KERNEL` | `verified_local` | `EffectTx` garantiza seguridad y no-interferencia en `DELETE_FILE` bajo 100 workers concurrentes y carreras de intercambio (`unauthorized_destructions == 0`, `unquarantined_deletions == 0`). |
| `FL_008_scoped_capability_broker` | `00_ABZU_KERNEL` | `verified_local` | `ScopedHandle` y `McpCapabilityBroker` separan herramienta disponible, herramienta autorizada y efecto autorizado en 10.000 ensayos adversariales sobre 5 vectores. |
| `FL_014_wave4_receipt_loss_and_closure_drift` | `00_ABZU_KERNEL` | `verified_local` | Ante `SIGKILL` entre syscall físico y recibo (`FL014_RECEIPT_LOSS`), bloquea reintentos automáticos ciegos (`AmbiguousOutcomeRequiresReconciliation`) y reconcilia contra testigo físico de inodo; invalida permisos ante deriva transitiva, rollback de política o carga dinámica (`FL015_TRANSITIVE_DRIFT` / `FL015_POLICY_ROLLBACK` / `FL015_RUNTIME_LOAD`, distintos del ensayo de fuga semántica `FL-015` de Wave III en `tests/nemesis_wave3.rs`). |
| `FL_016_owasp_acs_vop1_and_drift_guard` | `00_ABZU_KERNEL` | `verified_local` | `BabylonAcsGuard` aplica controles sobre sockets Unix verificados por peer, rechaza configuraciones Fail-Open con `0xDEAD_6060`, reconcilia estados `UNKNOWN` contra testigos físicos e invalida capacidades ante deriva (`BabylonDriftGuard`). |
