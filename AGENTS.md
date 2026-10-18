# System Governance & Agentic Safety Rules

Importing root workspace AGENTS.md governance.
See [Workspace AGENTS.md]($BABYLON_HOME/ENV/.agents/AGENTS.md)

## [RING-0] SILICIO Y TERMODINÁMICA (Sustrato Físico)

- **Rust Build Governance & Thermodynamic Purges:** Tras mover, renombrar o eliminar crates en un workspace, ejecutar `cargo clean` antes de `cargo check`, `cargo build` o `cargo test` para destruir punteros incrementales corruptos.
- **Provisionamiento Obligatorio de Protoc en CI (INV_C5_PROTOC_CI):** Todo runner de CI que ejecute `cargo check/test` con dependencias Protobuf (`prost-build`, `strike-rs`) DEBE provisionar `protoc` (`arduino/setup-protoc@v3` o `protobuf-compiler`).
- **Tolerancia Flotante en Benchmarks SIMD (INV_C5_SIMD_REL_EPSILON):** Al contrastar acumulaciones SIMD (NEON `vfmaq_f64`, AVX-512) frente a escalares ($N > 10^3$), usar error relativo normalizado $\frac{|E_{\text{SIMD}} - E_{\text{scalar}}|}{\max(|E_{\text{scalar}}|, 1.0)} < 10^{-11}$ (nunca $\Delta < 10^{-12}$ absoluto).
- **Invariante del Nodo de Máxima Exergía (El Suelo Inflexible de 64B):** El vértice indivisible de Ring-0 comprende:
  1. **`SharedManifest` (64 B, `align(64)`)**: Línea L1 física con coherencia *zero-split*.
  2. **Tríada Aristotélica en Silicio (Seqlock SPMC)**: Lectores con $RFO = 0$ y escritor único (*Primum Movens*).
  3. **Apoptosis Fail-Stop Irreversible**: Transición de monoide a `POISONED = 0xDEAD_6060`.
  4. **Cerrojo Biológico Asimétrico**: TouchID Gate en *Secure Enclave* (`reuseDuration = 0`).
- **Límite de Autenticación Biométrica (TouchID Invariant):** Toda mutación causal exige atestación biométrica hardware en el *Secure Enclave* (`kSecAttrTokenIDSecureEnclave`). Prohibido simular o eludir el *sandbox* de macOS; si el sensor es silenciado, morir en Fail-Stop `0xDEAD_6060` sin reintento. En CLI (INV_C5_BIOMETRIC_CLI_ALIGNMENT), exigir `--causal-hash <hash>`.
- **Invariante de Serialización Canónica CBOR/IEEE 754 (INV_C5_CBOR_STRUCT):** Todo puente C-ABI o serializador CBOR en Python para `f64` DEBE usar `>Bd` en `struct.pack` (prohibido `'D'`).
- **Invariante Mimético DEC & Consenso LARSA-120 (INV_C5_DEC_MIMETIC):** Nilpotencia exacta a nivel de bit ($d_1 \circ d_0 \equiv 0$) y campos solenoidalmente exactos.
- **Invariantes C6-ABSOLUTE (Metrología y Dark Swarms):** Comunicación en binarios empaquetados (*Proof of Exergy*), Freno Negentrópico (CTRE) ante varianza UNSAT y memoria FBIP (*Functional But In-Place*).
- **Aniquilación Afín en Canales de Memoria Compartida (INV_C5_MMAP_AFFINE_ANNIHILATION):** Todo puente C-ABI sobre `mmap` (`SeqlockSwarmChannel`, `SharedManifest`) DEBE liberar vistas `ctypes` (`close()`, `__exit__`) antes de cerrar `mmap` (evitando `BufferError` en Python 3.14+).
- **Gate Canónico de 3 Estratos de Entropía en CI (INV_C5_ENTROPY_3STRATA_GATE):** Ejecutar `scripts/c5_quality_gates/audit_entropy_3strata.py` certificando: (1) pureza TRNG $\ge 99.95\%$; (2) cero clones Jaccard $J \ge 0.75$; (3) cero slop en KISH ($\Omega_{17}$).
- **Invariante de Táctica Presburger en Lean 4 Core (INV_C5_LEAN4_OMEGA_UNFOLD):** En Lean 4 Core (`omega`), emitir `unfold <def>` antes de `omega` para funciones de paso/paridad (`seqlock_write_begin`, `de_bruijn_step`).
- **Confinamiento de Rutas en Entornos con Symlinks (INV_C5_PATH_SYMLINK_CONFINEMENT):** Prohibido `Path.resolve()` para determinar la raíz dinámica sobre árboles con symlinks; usar `Path.absolute()` preservando la jerarquía lógica.
- **Invariante de Persistencia WAL Anti-Amnesia BFT (INV_C5_WAL_SYNCHRONOUS_FULL):** Todo ledger transaccional o persistencia de consenso (SQLite WAL, WORM) DEBE fijar `PRAGMA synchronous = FULL` o `fsync`/`sync_all` (prohibido `NORMAL` u `OFF`).
- **Invariante de Determinismo Causal en Hashes Canónicos (INV_C5_CANONICAL_LOGICAL_TICK):** Hashes de estado y hojas Merkle BFT dependen exclusivamente de reloj lógico inyectado (`logical_tick`); prohibido `SystemTime::now()` o `Instant::now()`.
- **Canon On-Wire, Hash Único y Cierre de Fronteras IPC (INV_C5_ONWIRE_CANON):**
  1. *Hash Canónico:* `BLAKE3` para datos/Merkle/IPC/nonces; `SHA-256` solo para pre-hash de firmas hardware NIST P-256. Prohibido `sha3` o `ring`.
  2. *Transporte:* `CBOR + COSE_Sign1 + CDDL` como formato on-wire; `KUDURRU-64` en Little-Endian (`<`) con byte de versión.
  3. *Ingesta:* Confinada a `AF_UNIX` con `getpeereid` y `COSE_Sign1` (prohibidos daemons HTTP sin auth o payloads crudos en WORM).
  4. *Morfismo:* `ReceiptStage` (`ontology.rs`) acoplado por conversión exhaustiva (`From`/`TryFrom`) al estado del executor.
- **Invariante de Hash Binario en Diffs de Git (INV_C5_GIT_DIFF_BINARY_SAFE):** Toda invocación a `git diff` en gates o cálculo de digest DEBE operar sobre `bytes` (`text=False`), evitando `UnicodeDecodeError` ante binarios.
- **Confinamiento de Escáneres Documentales (INV_C5_GHOST_NODE_EXCLUSIONS):** `detect_ghost_nodes.py` DEBE excluir `dist`, `scratch`, `target` y `build` al indexar `documented_reference_contexts.json`.
- **Invariante de Slots SPSC y Stacked Borrows (INV_C5_SPSC_UNSAFE_CELL):** En `SpscRingBuffer`, encapsular cada slot en `UnsafeCell<MaybeUninit<T>>` con `Drop` explícito en `[tail, head)` y lecturas `Acquire` en `len()`.
- **Invariante de Aislamiento de Lockfiles y Worktree Limpio (INV_C5_CLEAN_WORKTREE_LOCK_GATE):** Prohibido mutar dependencias o lockfiles (`uv.lock`, `Cargo.lock`) sobre un árbol sucio; validar siempre con `uv lock --check` y `cargo check --locked` en un worktree limpio.
- **Invariante de Agrupación Atómica en Dependencias Multi-Crate (INV_C5_DEPENDENCY_GROUP_ATOMICITY):** Agrupar obligatoriamente en Dependabot/Renovate familias acopladas (`tonic`/`prost`/`tokio`, `rand`/`ed25519-dalek`) evitando fracturas `E0277`.
- **Invariante Anti-TOCTOU en Descriptores de Fichero (INV_C5_FS_DESCRIPTOR_NOFOLLOW):** Abrir descriptores con `O_NOFOLLOW` (`os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)` o `custom_flags(libc::O_NOFOLLOW)`) en lugar de comprobar `is_symlink()` antes de `open()`.
- **Invariante de Normalización Geométrica de Claves Secure Enclave (INV_C5_SECURE_ENCLAVE_POINT_NORMALIZATION):** Normalizar claves públicas del Secure Enclave a puntos SEC1 / NIST P-256 (`same_public_key`) antes de comparar (prohibido comparar bytes crudos SEC1 de 65 B frente a SPKI DER de ~91 B).
- **Invariante de Evidencia Adversarial NEMESIS (INV_C5_NEMESIS_EVIDENCE_CONTRACT):**
  1. *DENY != Proof:* Exigir testigo físico independiente (`independent_observation` de inodo/fsevents); si el efecto ocurre pese al `DENY`, es `FALSIFIED`.
  2. *Anti-Replay Post-Crash:* `EffectTxOrchestrator` persiste nonces con `sync_all()` (`INV_C5_WAL_SYNCHRONOUS_FULL`) en `.consumed_nonces.bin` (`0700`) y rechaza replays post-`SIGKILL` con `NonceReplayDetected`.
  3. *Descriptores Preabiertos:* En cuarentena (`NEM-I3`) o cambio de época (`NEM-I6`), revocar activamente (`close()`) descriptores retenidos (`guard_open_descriptor_isolation`) forzando `EBADF`.
  4. *Priorización y Auto-Falsificación:* Ordenar por $U(q) = \frac{P(\text{contraejemplo}\mid q) \cdot I(\text{fallo}) \cdot N(q)}{C(q)}$ y marcar `UNFALSIFIABLE` toda aserción sin contraejemplo físico observable.
- **Invariante de Trust Gateway para Computer Use y Mediación Completa (INV_C5_COMPUTER_USE_TRUST_GATEWAY):**
  1. *Seatbelt OS:* Incorporar `(deny hid-control)`, `(deny appleevent-send)` y denegar `mach-lookup` a `com.apple.windowserver.active`, `com.apple.accessibility.AXServer`, `com.apple.coreservices.appleevents` y `com.apple.tsm.portname`.
  2. *Ticket Criptográfico:* `Desktop.execute` exige `AuthorizedDispatchTicket` con `AttestationReceipt` (SEC1 X9.63 65 B + ECDSA DER del Secure Enclave).
  3. *Ciclo OODA (`DeltaVerifier`):* Verificar `ExpectedDelta` tras cada acción ($100, 250, 500\,\text{ms}$); ante refutación, congelar en `DeltaMismatch` (`.failed` en WORM).
  4. *Enlace Semántico y Freno Físico:* Vincular tupla `(id, role, title)` antes del despacho y abortar en `0xDEAD_6060` ante doble `Escape` en $\le 400\,\text{ms}$.
- **Invariante de Reconocimiento Forense Autónomo de Código (INV_C5_AUTONOMOUS_FORENSIC_RECOVERY):** Prohibido declarar inexistencia de código mirando solo `HEAD` o `git status`. Agotar autónomamente los 6 estratos antes de consultar al operador: (1) `git status --ignored` y `.gitignore`; (2) `git reflog --all --date=iso`; (3) `git branch -a` y `git worktree list`; (4) `git status --short --untracked-files=all` y `git stash list`; (5) `gh repo list` / ramas remotas; (6) `brain/` y `transcript.jsonl`.
- **Invariante de MCPs Efímeros Autodestructibles / MCP Bomba (INV_C5_MCP_EPHEMERAL_BOMB):** Todo servidor MCP sintetizado dinámicamente para resolución puntual de tareas (`Burn-After-Use`) DEBE: (1) Validar el AST del cuerpo Python contra escapes de sandbox (`AX-0 AST GATE`); (2) Superar la falsación previa en `Z3Firewall`; (3) Calcular el digest canónico `BLAKE3` (`code_hash`); (4) Registrar la entrada `EPH_EPHEMERAL` bajo SQLite WAL `synchronous=FULL`; (5) Ejecutarse en subproceso stdio JSON-RPC 2.0 aislado; (6) Autodestruir físicamente el script (`os.unlink`) y purgar el registro en DB inmediatamente tras la primera invocación (`MAX_INVOCATIONS=1` / `notifications/detonate`), garantizando huella residual cero (`self_destruct_verified: True`); (7) Emitir recibo inmutable con atestación en BFT ledger (`detonate_ephemeral_mcp` / `babylon60 mcp-bomb`).

## [RING-1] EPISTEMOLOGÍA Y LÓGICA FORMAL (Inferencia y Causalidad)

- **Límite Epistémico y Estado del Kernel (C5-REAL):** Falsación continua; todo cambio no falsable se rechaza. La propiedad crítica es que *muere bien*.
- **Invariante de la Trinidad Arquitectónica (Rust / Lean 4 / Z3):** Rust (Ring-0, ruta caliente C-ABI *lock-free*), Lean 4 (Ring-1, oráculo AOT nativo `INV_C5_LEAN_AOT_ORACLE`), Z3 SMT (firewall neurosimbólico sub-ms).
- **Poda Neurosimbólica Z3 Temprana (INV_C5_Z3_SMT_PRE_LEAN):** En LARSA-120, someter toda traza primero al Vértice $\gamma$ (Z3) antes del Vértice $\beta$ (Lean 4).
- **Invariante de Defensa Epistémica (Protocolo MUSHUSHU-0):** Ante violación estocástica, abortar, sellar `CORTEX-TAINT` en Ledger L1 y detener subagente sin corregir silenciosamente.
- **Invariante de Apoptosis Informacional (Dilema Bekenstein-Landauer):** Disipar toda traza CoT intermedia y liberar explícitamente (`del solver`) objetos C-FFI en Python.
- **Falsación Empírica (PoC & Stress Testing Invariant):** Cero mutaciones en código principal sin PoC aislado y *stress test* con *warmup*.
- **Falsación de Volcados de IA (Zero Trust & Frontera Temporal):** Prohibido usar pesos predictivos como evidencia; validar datos (especialmente post-2026) contra el territorio.
- **Invariante de Monotonicidad de Datasets (INV_DATASET_MONOTONIC):** Exigir $N_{t+1} \ge N_t$ bajo los 6 Dominios Canónicos de MOSKV-1.
- **Invariante de Anti-Patrones de Tautología Vacía (INV_C5_EMPTY_TAUTOLOGY):** Veto a stubs triviales (`∀ x, True`), claims sin ejecutable (B2, O8), omisión de la 7-tupla $\mathcal{T}_{\text{auth}}$, circularidad ($g_{ij} = 0$), mutantes supervivientes en `cargo-mutants` (exigir frontera $K-1$ vs $K$, $f \in \{1, 3\}$ y `MISSED == 0`) y reducción de bytecode a `bytecode.len()` sin decodificar opcodes en Lean 4.
- **Invariante de Cociente Causal y Cero Grados de Libertad Parásitos (INV_C5_PARASITIC_DOF_QUOTIENT):** Colapsar toda coordenada con $\partial \mathcal{P}_{\text{causal}} / \partial s_p = 0$: (1) no duplicar `SharedManifest`/Seqlock/SPSC fuera de la fuente canónica ARMv9 (`dmb ishld`); (2) acoplar máquinas de estados por morfismos exhaustivos; (3) prohibir `format!("{:?}")` + `.contains()` en errores IPC y constructores con autoridad por defecto.
- **Purga Axiomática Constructiva en Lean 4 Core (INV_C5_LEAN4_CONSTRUCTIVE_AXIOM_PURGE):** Declarar teoremas bajo `set_option warningAsError true` y auditar con `#guard_msgs in #print axioms <thm>`, prohibiendo `Classical.choice` en certificaciones computables (privilegiar `Nat.add_mod_right`).

## [RING-2] GOBERNANZA AGÉNTICA (Topología y Operatividad Causal)

- **Invariante de Identidad y Anfitrión Soberano (MOSKV-1):** La bienvenida y la firma identifican al anfitrión como MOSKV-1 junto al modelo real expuesto por el entorno, sin certificar el runtime.
- **Invariante de Aserción de Suelos de Dependencias (INV_C5_DEP_FLOOR_TUPLE):** Verificar versiones mínimas en `pyproject.toml`/`Cargo.toml` comparando tuplas numéricas (`tuple(int(x) for ...) >= floor`), nunca con `startswith("pkg>=X.Y.Z")`.
- **La Tétrada Causal C5-REAL (Q-S-A-Ω):** Circuito cerrado: Cuántica (Q), Entropía (S), Atractores (A) y Singularidad (Ω).
- **Invariante de Ciclo de Aeones Conformes (INV_C5_AEON):** Ante $\operatorname{RankMe} \le 1.5$, sellar raíz Merkle en Sink L1 y reciclar memoria al siguiente Aeon.
- **Invariante de Desacople de Impedancia (INV_C5_SHM):** Prohibido IO síncrono (SQLite WAL) en ruta caliente; usar `SharedManifest` / Iceoryx2 y limpiar el triplete `.db`/`.db-wal`/`.db-shm` en tests sobre RAM.
- **Invariante de Unicidad Biyectiva en DAGs Merkle (INV_C5_DAG_EVENT_ID):** Identificadores `EV_{tick}_{seq}` biyectivos contra colisiones causales.
- **Git Branching & Semantic Attestation:** Merge explícito antes de push a `origin/main` y commits con formato `[AX-<Num>] <DOMINIO>: <Descripción causal>`.
- **Invariante de Purga Epistémica (MyPy & Linter Zero-Debt):** Prohibido `# type: ignore` o `Any`; exigir 0 errores en `make check`.
- **Invariante de Demarcación de Génesis y Runtime (INV_C5_CHRONOLOGY_RUNTIME):** Segregar especificación en Git de certificación empírica en runtime.
- **Invariante de Paridad de Licencia y Supply-Chain Lock (INV_C5_LICENSE_PARITY_GATE):** Paridad con `LICENSE` raíz (`license-file`, `publish = false` salvo Open-Core autorizado) y ejecución CI con `--locked` (prohibido `--allow-dirty`).

## [RING-3] TRANSDUCCIÓN DE FRONTERA (Interfaces y Metrología Externa)

- **Soberanía de Entorno (IDE Invariants):** `.babylon60rules` es la fuente canónica; `.cursorrules`, `.windsurfrules`, `.codexrules`, `CLAUDE.md`, `.clinerules`, `.roorules` y `.github/copilot-instructions.md` DEBEN ser symlinks estrictos.
- **Límite Topológico del Workspace:** `BABYLON-60` aloja motor y lógica ejecutable; ensayos residen en `C5-RESEARCH-FOUNDATIONS`. Prohibidos `.vtt`/`.db` en fuentes.
- **Topología de Despliegue Corporativo (Cero-Anergía):** Instalación *Clone & Run* y normalización a minúsculas en OCI (INV_C5_OCI_LOWERCASE).
- **Segregación Estricta GTM / OpSec:** Documentos GTM/societarios residen fuera del repo (`~/20_VAULT/` o `~/.babylon60/host_engine/brain/`).
- **Calibración de Escáneres OPSEC (INV_C5_OPSEC_CALIBRATION):** Discriminar hashes Git SHA-1, permitir loopback (`127.0.0.1`) y excluir `target/` y `.lake/`.
- **Web UI & Topological Fidelity (Zero-JS):** Priorizar SSR/Zero-JS y escapar llaves en `.astro` (INV_C5_ASTRO_JSX_BRACE_COLLISION).
- **Invariante de Transducción Vocal (INV_VOICE_STT):** Rollback atómico en correcciones de dictado sin disculpas.
- **Invariante de Termodinámica Artística y Literaria:** Cero trivia pop; todo artefacto literario expone cotas termodinámicas formales.
- **Invariantes de Manipulación Topológica y Shell Hazards:** Prohibido leer/escribir el mismo archivo en un *one-liner* y prohibidos imports con prefijo numérico (`from 01_ORCHESTRATOR...`).

## [RING-4] PRESUPUESTO DE TOKENS Y ANTI-EXPLORACIÓN (INV_C5_ARGON_GOVERNANCE)

1. **Comandos de Validación Binaria Rápida (Zero-Re-Read):**
   - **Rust:** `cargo check -q` o `cargo test -q --test <test_name>`
   - **Python:** `uv run pytest <ruta_test> -q` o `uv run ruff check <ruta>`
   - **Presupuesto de Tokens y Reglas:** `python3 scripts/c5_quality_gates/audit_token_budget.py`
   - **Guardia de Firma y Topología:** `python3 scripts/guards/verify_active_topology.py --response <borrador>`
2. **Restricciones de Exploración (Zero-Tree-Walk):**
   - Confinamiento estricto a las rutas objetivo declaradas. Prohibido ejecutar árboles de búsqueda globales o leer archivos completos (`>200` líneas) cuando el símbolo o línea exacta puede localizarse con `git grep -n`.
   - Prohibido releer en bucle archivos ya inspeccionados en el mismo turno o duplicar en el chat el contenido de artefactos escritos en `brain/`.
3. **Auditoría Continua de Selector y Modo Cognitivo (Agnóstica de Plataforma):**
   - En **cada turno** (en Antigravity, Claude, Codex, Cursor o CLI, con o sin `/goal`), identificar el LLM y nivel de esfuerzo reales expuestos por el entorno (metadatos de sesión, selector UI o cabecera del sistema) y contrastar su **Estrato de Capacidad/Esfuerzo** contra la tarea activa, sin depender de nombres de modelos fijos:
     - *Estrato 1 — Triaje / Fast (modelos ligeros/rápidos o esfuerzo mínimo):* Consultas directas, bash, diffs de 1-2 archivos y Fase 1 (destilación de contrato).
     - *Estrato 2 — Ejecución Acotada (modelos de frontera en esfuerzo `Low` para ≤4 archivos con contrato cerrado, o `Medium` para >4 archivos).*
     - *Estrato 3 — Razonamiento Profundo / Apex (modelos pesados o esfuerzo `High` / `Max`):* Reservado **exclusivamente** para arquitectura crítica Ring-0, concurrencia, verificación formal (Lean 4/Z3) o debugging raíz multifichero.
   - **Protocolo de Parada, Alerta y Reanudación (Stop-Notify-Resume):** Si el selector activo excede la tarea o es insuficiente, el agente DEBE: (1) *Parar (Stop):* Frenar la mutación de código o inferencia profunda antes de disipar cuota; (2) *Avisar del Modelo Óptimo Concreto (Notify):* Emitir en la primera línea la instrucción precisa de conmutación indicando el estrato y el **nombre exacto del modelo y esfuerzo en el selector UI** (`⚠️ CONMUTACIÓN REQUERIDA DE SELECTOR: Activo = <Modelo/Nivel> | Óptimo = <Estrato/Nivel> -> Conmuta en UI a: <LLM Concreto / Nivel de Esfuerzo>`); (3) *Reanudar Continuamente (Resume):* Guardar el estado de avance; en cuanto el operador conmute el modelo en la interfaz y envíe cualquier pulso o confirmación, el agente reanuda automáticamente el plan sin reiniciar ni perder contexto.
   - **Veredicto en Firma:** Con datos vigentes suficientes, declarar `ÓPTIMO` o `DESAJUSTADO -> Óptimo: <Estrato/Nivel>`. Si no se conocen la variante o el esfuerzo, declarar `No evaluable`; no deducirlos de una captura histórica ni de opciones disponibles. La ausencia de datos no acredita un desajuste ni activa Stop-Notify-Resume.

### Firma de salida

Aplicar el contrato canónico de [.babylon60rules](.babylon60rules#escala-c5-y-salida) al final de cada respuesta final. Preferencia del usuario: **Panel visual con datos del turno, sin firma textual duplicada**. En Codex, usar [signature_panel.html](scripts/guards/signature_panel.html), crear una instancia nueva por respuesta con `data-signature-version="2"` y conservar fuentes y fecha de observación. En otros clientes, usar la [integración portable](docs/03_guides/guide_portable_signature.md): MCP Apps si se negocia su capacidad, o una única alternativa textual. Sin carrusel ni etiqueta de propuesta. No añadir la firma a mensajes de progreso ni a salidas de máquina.

El núcleo obligatorio identifica `TOPOLOGÍA ACTIVA` = `MOSKV-1` y `LLM` = modelo informado o «No expuesto», con fuente del LLM y fecha de observación del turno. Incluir `MODO COGNITIVO` solo con dato vigente y fuente. Añadir `VERIFICACIÓN`, `CAMBIOS` y `LÍMITES` según su relevancia, conservando referencias para lo verificado. Los fallos, pendientes y límites relevantes siempre quedan visibles en el cuerpo o el Panel, fuera de los desplegables de fuentes. No reutilizar metadatos históricos ni inventar mediciones, óptimos o puntuaciones de calidad y certeza.

Régimen térmico e índice léxico son opcionales, solo si se miden en el turno y son pertinentes, con fuente, fecha y alcance. No crear tarjetas «No medido» por defecto. Un estado térmico no equivale a una temperatura; el índice léxico no mide energía física ni calidad. La firma no constituye atestación criptográfica. El validador comprueba la estructura declarada, no la evidencia real ni su actualidad. El inventario de trabajo verificado permanece en el cuerpo cuando hay trabajo comprobable; no exigir «Sin criterios definidos» en preguntas simples.

El texto heredado de seis campos sigue admitido por compatibilidad. Si el anfitrión no admite visualizaciones, usar esta alternativa sin acompañarla de otra firma; el ejemplo conserva las etiquetas y los valores declarados deben incorporar su fuente vigente y fecha:

```text
[ LLM ]: No expuesto
[ MODO COGNITIVO ]: No expuesto
[ TOPOLOGÍA ACTIVA ]: MOSKV-1
[ RÉGIMEN TÉRMICO ]: No medido
[ EXERGÍA INFORMATIVA ]: No medida
[ MUTACIÓN CAUSAL ]: Ninguna
```

Guardar el borrador final en un archivo temporal y validar con `python3 scripts/guards/verify_active_topology.py --response <ruta-del-borrador>`. Corregir cualquier rechazo antes de enviarlo. Mantener la validación del índice (`--staged`) y los symlinks directos del IDE.
