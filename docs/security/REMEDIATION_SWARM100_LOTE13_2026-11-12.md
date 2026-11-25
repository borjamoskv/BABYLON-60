# Lote 13 ejecutado: 30 hallazgos — 12/11/2026

Estado de cierre: **provisional**. El lote está integrado en `main` y publicado
en el VAULT interno (`origin`). La revisión independiente se ejecutó el
18/11/2026 y sus hallazgos confirmados se corrigieron (ver
[Revisión independiente](#revisión-independiente)); los residuales se cerraron
el 25/11/2026 con una segunda revisión (ver [Residuales](#residuales-25112026)).
Falta la reconciliación del inventario, así que ningún estado de este documento
debe leerse como cierre del registro.

Resultado sobre los 30 hallazgos únicos del
[plan del lote](PLAN_SWARM100_LOTE13_2026-10-30.md):

| Estado | Nº | Significado en este documento |
| --- | --- | --- |
| FIXED | 22 | Defecto corregido en el código, con prueba de regresión en el repositorio. |
| BLOCKED | 5 | La capacidad no puede cumplir la aceptación con lo que existe; ahora rechaza siempre (fail-closed). |
| CONFIRMED | 3 | El código vigente ya cumplía; se añadió o se ejecutó la prueba que lo demuestra. |

C0341 pasó de PARTIAL a FIXED tras la revisión independiente: el formato v2 de
firma de manifiesto completo ya existía en Python y faltaba en Rust.

La copia secundaria **C0461** (mismo fallo que C0103), que el plan incorporaba
sin contarla como hallazgo único, quedó corregida en `47379fc0`. Al integrar en `main`, la copia ya había sido eliminada por la purga de skills extrínsecas (`d5bcb93f`), así que la fusión conserva el borrado y retira su test.

## Contrato y alcance

Se siguió el protocolo del plan: reconfirmar hashes y estado antes de editar,
reproducir cada fallo con entradas propias, corregir, y ejecutar regresiones.
Aplican los [contratos por ámbito](../03_guides/agent_contracts.md).

- **Hashes de partida.** `void_accel.c`, `void_vec.py` y `hypervisor.rs`
  coincidían con el plan. `src/secure_fs.rs` y
  `crates/babylon-attest/src/ledger.rs` ya habían cambiado en commits anteriores,
  así que sus hallazgos se readjudicaron contra el código vigente en lugar de
  aplicar el parche histórico.
- **Fixtures.** Solo directorios, repositorios Git y ledgers temporales, procesos
  hijos propios y claves software sintéticas. Sin datos del operador, hardware,
  proveedores, despliegue ni publicación.
- **Dependencias.** Todo se compiló y probó con `--locked`. No se modificó
  ningún `Cargo.lock`, `uv.lock` ni manifiesto de dependencias.
- **Árbol de trabajo.** Había cambios ajenos sin commitear durante toda la
  ejecución (CI, Lean, `conformance/`, `evals/`, adaptador Codex). Se preservaron
  y no forman parte de estos commits. Entre los commits del lote hay tres commits
  ajenos intercalados en la rama.

Una readjudicación previa de solo lectura (481 agentes: cinco lentes por
hallazgo, dos refutadores por lente, síntesis y crítico) sirvió para priorizar.
No es evidencia de cierre: varios agentes partieron de la premisa falsa de que
el directorio no era un repositorio Git, y sus veredictos sobre C0045 y C0053
se repitieron después con pruebas ejecutadas.

## Resultado por grupo

| Grupo | IDs | Estado y comportamiento comprobado |
| --- | --- | --- |
| Memoria / FFI | C0045, C0502, C0091 | FIXED: bucles SIMD sin resta sin signo; longitudes medidas en bytes reales antes de la FFI; longitud del sobre IPC validada antes del corte en el daemon y en la API de suscripción. |
| Intención / presupuesto | C0046, C0052, C0053 | FIXED: cargo e intención durable antes de la cuarentena; presupuesto leído del registro compartido entre instancias; cargo de mutación antes de la syscall. |
| Ledger de atestación | C0349, C0350 | CONFIRMED: exclusión entre procesos y confirmación tras sincronizar ya vigentes; se añade la sincronización del directorio en la primera escritura. |
| Aritmética | C0442, C0443, C0335, C0326 | FIXED: reducción F60 conserva el valor; división exacta con ambas escalas; `MIN / -1` produce halt crítico; desbordamiento sexagesimal es error tipado en debug y release. |
| Firmas y confianza | C0107, C0381 | FIXED: `verify_chain` recalcula los hashes desde las filas; cada exportación forense tiene directorio exclusivo. |
| Firmas y confianza | C0341 | FIXED: ancla externa obligatoria y firma verificada sobre el manifiesto v2 completo, compatible con el sellador Python. |
| Firmas y confianza | C0054, C0336 | BLOCKED: el verificador CLI y `c5.auditLedger` no aprueban nada sin un verificador real. |
| Firmas y confianza | C0393 | CONFIRMED: la evidencia de ejecución aportada por el cliente ya se rechazaba. |
| Parser / UI | C0481, C0493 | FIXED: el cursor GGUF salta el array completo; los campos del ledger se insertan como texto. |
| Inferencia | C0526, C0201, C0202 | BLOCKED: sin motor de inferencia ni circuito que ligue la inferencia, no se devuelve ni se certifica nada. |
| Backend x86 | C0214 | FIXED: marco de pila dimensionado según los slots; exceso rechazado. |
| Contenedor | C0565 | FIXED: imagen `rust:1.89` y compilación `--locked`. |
| CDP | C0001, C0002, C0003 | FIXED: futuros, listeners y proceso hijo liberados en timeout, error y cancelación. |
| Verificadores | C0004, C0005 | FIXED: el PoC decide por el conteo observado; el verificador de ejecución detecta archivos no versionados. |

## Detalle por ID

Cada fila indica cómo se reprodujo el fallo, dónde vive la regresión y en qué
commit entró. "Ejecutada" significa prueba roja ejecutada antes del cambio;
"lectura" significa que el defecto se estableció leyendo el código.

| ID | Reproducción | Prueba de regresión | Commit |
| --- | --- | --- | --- |
| C0045 | Ejecutada (ASan, harness externo) | Sin prueba en el repositorio | `d905e971` |
| C0502 | Ejecutada | `tests/test_c0502_void_vec_buffer_length.py` | `d905e971`, `1c5ec0f0` |
| C0091 | Ejecutada | tests en `hypervisor.rs` y `bft_iceoryx2.rs` | `d905e971`, `35826b32` |
| C0046 | Ejecutada (fallo inyectado) | `tests/c0046_intent_before_quarantine.rs` | `1c5ec0f0` |
| C0052 | Ejecutada | `tests/c0052_shared_budget_regressions.rs` | `b166435a` |
| C0053 | Ejecutada | `tests/c0053_recovery_budget_regressions.rs` | `9a358ed2` |
| C0349 | Ejecutada (mutación: sin `flock` falla) | `crates/babylon-attest/tests/c0349_c0350_ledger.rs` | `a0fb4be9` |
| C0350 | Ejecutada (ledger sin permiso de escritura) | misma prueba | `a0fb4be9` |
| C0442, C0443 | Ejecutada | `c0442_c0443_tests` en `babylon60-runtime` | `d067a6e6` |
| C0335 | Ejecutada | tests en `babylon60-kernel/src/eval.rs` | `1301c8aa` |
| C0326 | Ejecutada (harness externo, debug y release) | tests `c0326_*` en `b60-lang/src/vm.rs` | `77bb83a0` |
| C0054 | Ejecutada (expediente fabricado) | Sin prueba en el repositorio | `86b8a117` |
| C0107 | Ejecutada | test `c0107_*` en `strike-rs/src/ledger.rs` | `f778a86e` |
| C0336 | Ejecutada | `c0336_tests` en `cortex-lsp/src/actions.rs` | `e7220f4e` |
| C0341 | Ejecutada | test `c0341_*` en `conformal_tree.rs` | `1059204c` |
| C0381 | Lectura | tests `c0381_*` en `src/babylon60_tests.rs` | `0bb5491a` |
| C0393 | Lectura; tests existentes ejecutados | `fl_p11_*` y `crates/babylon-skills-mcp/tests/proposal_boundary.rs` | — |
| C0481 | Ejecutada | `c0481_tests` en `eridu-infer/src/gguf.rs` | `1f8e0dc7` |
| C0493 | Ejecutada en navegador con ledger hostil | Sin prueba en el repositorio | `26c23218` |
| C0526 | Ejecutada | `c0526_tests` en `eridu-infer/src/server.rs` | `10283fd1` |
| C0201, C0202 | Ejecutada (prueba Groth16 fabricada) | `babylon60-verifiable-inference/tests/c0201_c0202_forgery.rs` | `18d165a1` |
| C0214 | Ejecutada | `babylon60-compiler/tests/c0214_stack_frame.rs` | `1131f0f7` |
| C0565 | Ejecutada (versión declarada) | `tests/test_c0565_dockerfile_rust_version.py` | `c7bae5eb` |
| C0001–C0003 | Ejecutada (seis pruebas) | `tests/test_c0001_c0003_cdp_resources.py` | `c71d4a27` |
| C0004 | Lectura | `c0004_tests` en `poc_bft_zerocopy_dag.rs` | `9241c53c` |
| C0005 | Ejecutada (repositorio temporal) | `tests/test_c0005_verify_execution_untracked.py` | `0d081bb1` |

## Capacidades bloqueadas

Estos cinco hallazgos no se "arreglan": la capacidad anunciaba un resultado que
no podía obtener. Ahora dice que no puede.

- **C0054** — `scripts/c5_demos/c5_verifier_cli.rs` decidía por subcadenas del
  JSON. Un expediente fabricado obtenía el dictamen de conformidad. El binario
  no tiene verificador criptográfico; rechaza siempre con código 1.
- **C0336** — `c5.auditLedger` devolvía `HEALTHY` sin abrir ningún ledger. Exige
  una ruta existente y devuelve `NO_VERIFICADO`; `cortex-lsp` no tiene verificador
  de cadena.
- **C0526** — `/v1/chat/completions` devolvía texto prefabricado atribuido al
  modelo solicitado y sellaba un recibo. No hay motor de inferencia; responde 503
  sin recibo ni tokens.
- **C0201, C0202** — el circuito solo expresa `weight * nonce == expected_hash` y
  el setup sale de una semilla pública. `verify_inference_payload` devuelve
  siempre `false`. La comprobación Groth16 queda como
  `verify_public_setup_relation_proof`, fuera del FFI y solo para demostración.

Reabrir cualquiera de ellas requiere: formato de firma y ancla para el
expediente; un verificador de cadena accesible desde `cortex-lsp`; un motor de
inferencia; y un circuito que ligue modelo, entrada y salida con parámetros de
una ceremonia confiable.

## Cambios de interfaz

- `SexaRegister::add` y `SexaRegister::from_parts` devuelven `Result` (C0326).
- `verify_manifest_file` recibe la clave ancla; `verify-aeon` exige
  `--trusted-key` (C0341).
- `X86Backend::compile` devuelve `Result<String, String>` (C0214).
- Las exportaciones forenses pasan a `artifact_bundle_v3/quarantine/<hash>-NNNN/`
  (C0381).
- `verify_inference_payload` ya no puede devolver `true` (C0201, C0202).
- El contenedor de `babylon-attest` compila con `rust:1.89-alpine` (C0565).

La primera versión de este informe afirmaba que no había otros consumidores en
el workspace. La revisión independiente encontró dos: el exportador EU AI Act
(rutas de C0381) y `tests/test_merkle_cross_bisimulation.py` (`--trusted-key`
de C0341). Ambos se corrigieron. Consumidores externos, si existen, no se han
comprobado.

## Límites que permanecen

- **Sin revisión independiente.** Todas las comprobaciones son del mismo
  ejecutor que escribió los parches.
- **C0045:** la ruta AVX-512 solo se compiló; no se ejecutó en x86_64. No hay
  prueba de regresión en el repositorio.
- **C0052:** la prueba de presupuesto compartido es secuencial. Un registro
  parcial de `.budget_usage.bin` ahora bloquea los efectos (fail-closed) y
  exige reconciliar el fichero a mano.
- **C0053, C0046:** un fallo de ejecución o de cuarentena posterior al cargo
  consume presupuesto. Es deliberado (fail-closed) y cambia el comportamiento
  observable. Los WAL escritos con el orden anterior siguen siendo ambiguos.
  Si falla la escritura del cargo tras registrar la intención, el nonce queda
  bloqueado hasta reconciliarlo, sin cargo ni efecto.
- **C0107:** el hash de statement cubre `content` y `modality`; `obligations`
  queda fuera y su alteración no se detecta. Desplazar bytes entre `content` y
  `modality` sí se detecta: la verificación exige una etiqueta canónica.
- **C0349:** el bloqueo entre procesos es `flock`; fuera de Unix no hay exclusión.
- **C0350:** no hay prueba de corte eléctrico ni de fallo de `sync` inyectado;
  el retroceso tras un fallo de escritura se verificó por lectura. Si el propio
  retroceso falla, el error lo indica y el ledger exige reconciliación manual.
- **C0381:** el paquete de artefactos del camino de éxito sigue usando rutas
  fijas; no es evidencia forense.
- **C0565:** la imagen del contenedor no se construyó; no había Docker.
- **C0005:** los archivos cubiertos por `.gitignore` quedan fuera de la
  comprobación, por contrato explícito en el script.
- **Formato:** `babylon60-kernel/src/eval.rs`, `src/secure_fs.rs` y
  `strike-rs/src/bft_iceoryx2.rs` tenían diferencias de `rustfmt` previas que no
  se tocaron.
- **Cambios críticos:** los cambios de orden en el protocolo de efectos
  (C0046, C0053) no han pasado la revisión de contrato que exige el manifiesto.

## Validación ejecutada

- `cargo check --workspace --all-targets --locked`: sin errores tras el último
  commit.
- Suites de integración que usan `secure_fs` (15), `strike_rs` (78 unitarias),
  `babylon60-kernel`, `b60-lang` (47 unitarias, más release para C0326),
  `babylon-attest`, `eridu-infer`, `babylon60-compiler` y `cortex-lsp`: en verde
  en el momento de cada commit.
- Pruebas Python nuevas y las suites existentes del motor CDP: en verde.
  `ruff check` y `ruff format --check` sobre los ficheros Python tocados.
- `gitleaks` sobre cada fichero antes de su commit: sin hallazgos.

No se ejecutó la suite completa de Python ni `pre-commit run` con la
configuración del repositorio. Las reproducciones hechas con harness externos
(C0045, C0054, C0326, C0493) no se conservaron como artefactos de evidencia.

## Revisión independiente

Se ejecutó el 18/11/2026 sobre los 24 commits del lote (incluido C0461): dos
revisores por commit con enfoques distintos (cumplimiento de la aceptación y
elusión) y un refutador por cada problema encontrado. Solo lectura, sin `cargo`.
108 agentes, ninguno con error. Sobrevivieron a la refutación 58 hallazgos, con
duplicados entre enfoques; algunos eran regresiones introducidas por este mismo
lote. Todos los de gravedad alta y los de gravedad media con impacto de
seguridad se corrigieron con prueba roja previa:

| ID | Hallazgo confirmado | Corrección | Commit |
| --- | --- | --- | --- |
| C0502 | La guarda medía el búfer con `memoryview`, pero la FFI recibía `bytes(b)`: un `__bytes__` o un `__buffer__` cambiante eludía la comprobación | Una sola vista por objeto, medida y copiada; `len(flat) == count * stride` antes de la FFI | `c2b9ba9f` |
| C0326 | `SEXA_MUL`, `SEXA_CEIL` y `b60_sexa_add` (FFI) seguían desbordando | Aritmética comprobada; contrato FFI `-2` / `-3` igual que `src/ffi_oracle.rs` | `9560bfef` |
| C0381 | Regresión: el exportador EU AI Act seguía leyendo `quarantine/manifest.json` e informaba una ejecución detenida como nominal | Reconoce los directorios exclusivos; cualquier cuarentena prevalece | `c8f2f5d8` |
| C0201 | La fachada Python certificaba con un SHA256 calculable por cualquiera; el falsificador marcaba `SUPPORTED` | `verify_payload` devuelve siempre `False`; `checksum_matches` y veredicto `UNTESTABLE` | `cb783bc1` |
| C0054 | El orquestador reutilizaba un binario compilado antes de la corrección, que seguía certificando | Compila el verificador en un directorio temporal en cada ejecución e informa el rechazo | `a7de2c85` |
| C0481 | Regresión: un `count` sobredeclarado provocaba pánico por índice | Lecturas de metadatos acotadas con error | `139c08d6` |
| C0341 | El verificador Rust firmaba solo `merkle_root` e ignoraba el formato v2 ya usado por el sellador | Verificación v2 sobre el JSON canónico completo, idéntico al de Python; prueba cruzada Python→Rust | `168feb96` |
| C0052 | Un registro parcial desalineaba el presupuesto y lo desactivaba (fail-open) | Longitud no múltiplo de 48 bloquea efectos y arranque | `be384625` |
| C0107 | Bytes desplazables entre `content` y `modality` sin cambiar el hash | Etiqueta de modalidad canónica obligatoria | `583e5e85` |
| C0046 | Con `tx_nonce` distinto de `auth.nonce`, la cuarentena no era recuperable | Se exige que coincidan antes de cualquier efecto | `b7272c3a` |
| C0350 | Directorio padre sin sincronizar; un bloque fallido quedaba encadenado | Retroceso al tamaño previo ante fallo; sincronización de `ledger/` y `BABYLON_HOME` en cada append | `5b047a85` |
| C0003 | Cancelar `launch()` dejaba vivo al hijo; un segundo `launch()` fallido mataba el hijo anterior | Limpieza limitada al hijo y perfil creados por esa llamada, también ante cancelación | `76bf21c9` |
| C0005 | `.git/info/exclude`, `core.excludesFile` y `skip-worktree` ocultaban cambios; sin hashes desde un subdirectorio | Solo `.gitignore` excluye; marcas ocultas fallan; ejecución desde la raíz | `d7baec97` |

Los hallazgos de gravedad baja o media sin impacto de seguridad directo que
quedaron abiertos se trataron el 25/11/2026 (ver la sección siguiente).

### Cambios de interfaz añadidos por la revisión

- `SexaRegister::mul_scalar` devuelve `Result`; `b60_sexa_add` (en `b60-lang`)
  devuelve `-2` y `-3`.
- `verify_manifest_file` exige el formato v2 (`babylon60.aeon-manifest.v2`).
  Manifiestos firmados solo sobre `merkle_root` dejan de verificarse.
- `secure_delete_scoped` rechaza `tx_nonce` distinto de `auth.nonce`.
- `babylon60.verifiable_inference.verify_payload` devuelve siempre `False`;
  nueva `checksum_matches`. El falsificador devuelve `UNTESTABLE` cuando el
  checksum coincide.
- `c5_sovereign_compliance_orchestrator.py` sale con código 1 cuando el
  verificador rechaza, y no ejecuta `scripts/c5_demos/babylon_verifier_bin`.
- `verify_execution.sh` falla con archivos ocultos por `.git/info/exclude`,
  `core.excludesFile`, `skip-worktree` o `assume-unchanged`.

## Residuales (25/11/2026)

Se trataron sobre `origin/main` en la rama `claude/lote13-residuals-20261125`,
cada uno con prueba roja previa, y después se sometieron a una segunda revisión
independiente (30 agentes, 18 hallazgos confirmados con duplicados, ninguno que
invalidara una corrección); sus hallazgos también se corrigieron.

| ID | Problema | Corrección | Commits |
| --- | --- | --- | --- |
| C0442 | `NIG` con multiplicador ignoraba su escala; `AFTER` convertía 1/2 en 30 ticks y los negativos en 0 | Producto exacto con escala acotada a 20; `AFTER` exige un entero no negativo y despertar sin desbordar | `c52b8bf8`, `56ae3a49` |
| Nuevo | El tokenizador leía `# comentario` como operando (multiplicador 0); `falsation_test.b60` no llegaba a probar lo que declara | `#` fuera de cadenas y corchetes termina la línea; comprobación de aridad con halt crítico | `c52b8bf8`, `56ae3a49` |
| C0526 | El HUD mostraba el 503 como "Error de conexión"; etiquetas fijas afirmaban conformidad, WORM y atestación; la ruta WebSocket respondía `ok` a cualquier RPC | El HUD informa el error real; textos fieles al estado; `rpcError` con `inference_unavailable` | `4f2da844`, `f2e17c2d` |
| C0004 | El veredicto contaba cualquier resultado firmado | Solo cuentan nodos despachados con el hash esperado, una vez | `65a96096` |
| C0053 | El cargo se persistía antes de `ATTEMPT_RESERVED`: un fallo entre ambos permitía reintentar el mismo nonce y cobrar dos veces | Intención primero, cargo después, ambos antes del efecto | `9c516520` |
| C0565 | La prueba solo miraba el `rust-version` raíz | Recorre las dependencias bloqueadas de `babylon-attest`; versiones normalizadas | `8956d601`, `0126c4a3` |
| C0003, C0214, C0091 | Pruebas que no discriminaban | `waitpid` antes de cualquier limpieza; frontera exacta de la pila del kernel; paquete válido de exactamente 8192 bytes en ambas rutas | `3e1aacbd`, `0126c4a3` |

Las pruebas de despacho del runtime, de C0091 y de C0003 se comprobaron por
mutación: al reintroducir el defecto, fallan. El residual de `yt_audit.py` dejó
de aplicar: el fichero canónico también se eliminó en la purga de skills.

Límites que siguen abiertos tras esta ronda:

- **C0004:** la decisión de `main` del PoC no tiene prueba unitaria, porque
  requiere IPC en vivo; el PoC real se ejecutó y completa 10/10 nodos.
- **C0053:** ver la entrada de C0053 en
  [Límites que permanecen](#límites-que-permanecen).
- `tools/examples/counter_sync.b60` está escrito para `babylon-dsl` y no
  termina bajo `babylon60-runtime`, igual que antes de estos cambios.

### Cambios de interfaz de la ronda de residuales

- `babylon60-runtime`: `NIG` con producto fuera de escala 20, `AFTER` con ticks
  fraccionarios, negativos o que desbordan, y líneas sin operandos terminan con
  halt crítico (código 1). `#` inicia un comentario.
- `eridu-infer`: la ruta WebSocket responde `rpcError` a toda llamada RPC.
- `secure_fs`: el orden en mutación y borrado pasa a ser intención, cargo y efecto.

## Pendiente

1. Revisión de contrato de los cambios de orden en el protocolo de efectos
   (C0046, C0053).
2. Reconciliar el inventario con estos estados, conservando la historia.
3. Decidir el formato de firma y ancla del expediente (C0054) y el alcance de las
   capacidades bloqueadas.
4. Preparar el siguiente lote, sin aplicarlo.
