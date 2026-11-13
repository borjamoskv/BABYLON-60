# Auditoría y plan de los cinco experimentos de agentes

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

26 de octubre de 2026. Alcance: FL-DBR-01, FL-MCP-01, FL-PERIM-01,
FL-REC-01 y FL-PATH-01 propuestos en el radar aportado por el operador.

Actualización posterior: los dos contraejemplos de recuperación se corrigieron
y se verificaron con once regresiones; véase la
[evidencia de la corrección](fl-rec01-recovery-provenance.md). Las observaciones
y cifras iniciales de esta auditoría se conservan como antecedentes.

FL-PATH-01 se continuó sobre el cargador de skills: resolución por descriptores
y [10.000 casos por política](fl-path01-capability-root-escape.md), con cero
bytes exteriores devueltos en C y controles positivos legítimos.

La primera corrección recomendada fue la confirmación de resultados durante la
recuperación: se reprodujeron dos contraejemplos en la API local de SecureFS.
FL-MCP-01 ya tiene implementación y evidencia acotada; debe conservarse y
extender su cobertura. FL-PATH-01 dispone de resolución por descriptores, pero
falta demostrar que todas las lecturas pertinentes la utilizan. FL-PERIM-01 y
la comparación de conocimiento de FL-DBR-01 requieren bancos nuevos.

## Alcance y aceptación de la auditoría

Resultado: diagnóstico de los cinco experimentos, evidencia reproducible y
secuencia de implementación. Rutas añadidas: este informe y su
sonda aislada de recuperación (material no distribuido: `evidence/recovery-audit-2026-10-26.rs`).
El código productivo, dependencias y lockfiles quedan fuera de esta edición.
Aceptación: fuentes locales identificadas, resultados leídos, distinción entre
pruebas existentes y campañas pendientes, enlaces y controles documentales.

Base observada: `main`, HEAD `0ea2f5e08ee965d0d957c230cca973a126185c4c`,
con cambios ajenos previos. Las conclusiones corresponden al árbol inspeccionado,
no a un checkout limpio de ese commit. El índice nativo `babylon-60` se actualizó
correctamente el 26 de octubre a las 18:25 UTC; la cobertura consultada de las
rutas principales devolvió `metadata_match`. El grafo es una ayuda de búsqueda,
no una prueba de exhaustividad. Las noticias del radar no se usan como evidencia
del comportamiento de BABYLON-60; su verificación editorial queda fuera de alcance.

| Experimento | Estado observado | Trabajo que falta |
| --- | --- | --- |
| FL-DBR-01 | Infraestructura parcial; superioridad distribuida `NO_VERIFICADO`. | Corpus, referencia independiente, presupuesto agregado y comparación A/B/C. |
| FL-MCP-01 | Broker y Cortex incluyen guard de handlers y finalización asíncrona; 109 tests Python pasan. | Extender cobertura a otros servidores/backends y validar hardware. |
| FL-PERIM-01 | Aislamiento local parcial; anfitrión comprometido `NO_VERIFICADO`. | Perímetro y observador fuera del host, banco A/B/C y canales encubiertos. |
| FL-REC-01 | Dos contraejemplos locales corregidos; once regresiones pasan. | Ejecutar la campaña A/B/C de 5.000 casos y ampliar procedencia. |
| FL-PATH-01 | Lecturas e ingestión de skills corregidas; 10.000 casos por política verificados. | Extender evidencia a otros consumidores y modelos de amenaza. |

## Hallazgos que determinan la prioridad

### Confirmación de recuperación sin evidencia suficiente

En [`recover_quarantined`](../../src/secure_fs.rs), la ausencia del nombre de
cuarentena produce `Committed`, aunque no haya WAL. La sonda crea un archivo
sintético, no ejecuta ninguna eliminación y observa:

```text
REC_NO_INTENT status=Committed wal_present=false original_bytes_unchanged=true
```

En [`reconcile_wal_entry`](../../src/secure_fs.rs), `Delete + ENOENT` convierte
una reserva en resultado conocido. La segunda prueba reserva la intención,
renombra el archivo mediante un actor externo y no ejecuta el borrado:
devuelve `ReconciledCommitted` y el objeto original conserva sus bytes.
La ausencia de un nombre no demuestra quién produjo el cambio ni la ejecución
de la intención reservada. La política debe distinguir el resultado deseado
sobre una entrada de directorio de la confirmación causal de una operación.

Estos resultados refutan la afirmación de confirmación con evidencia suficiente
para esas entradas de la API local. No demuestran explotación remota ni una
repetición no autorizada. El grafo solo encontró un llamador de reconciliación,
en `nemesis_wave4`; la integración productiva completa sigue sin establecerse.

El [`executor`](../../src/executor.rs) conserva `DISPATCHED → UNKNOWN` al
reiniciar, pero completa con `b"OK"` tras el retorno del adaptador, sin exigir
un testigo independiente en esa transición. Hay que definir cuándo `Completed`
es solo retorno del adaptador y cuándo puede exponerse como resultado verificado.
Un error posterior a un efecto parcial también necesita una regresión explícita.

### La resolución segura existe pero no cubre por sí sola todas las lecturas

[`resolve_confined_parent_nofollow`](../../src/secure_fs.rs) rechaza rutas
absolutas y `..`, recorre directorios con `openat + O_DIRECTORY + O_NOFOLLOW`
y abre la hoja sin seguir symlinks. `pin_object` obtiene identidad mediante
`fstat` y hash sobre el descriptor. El
[`broker`](../../src/capability.rs) también evita confusiones de prefijo y
representaciones ambiguas en los recursos textuales.

La ruta de ingestión de
[`babylon-skills-mcp`](../../crates/babylon-skills-mcp/src/lib.rs) merece una
revisión separada: `load` abre `_root_handle`, pero continúa recorriendo nombres;
`walk_skill_resources` comprueba el tipo antes de leer y `read_bytes_nofollow`
usa `open(path, O_NOFOLLOW)` únicamente sobre la hoja. Ese descriptor raíz no
interviene en las lecturas posteriores. El cambio concurrente de un componente
intermedio es un candidato de falsación; esta auditoría no reprodujo el escape
del cargador completo. Las pruebas actuales de mutación y borrado no sustituyen
la medición de lecturas y bytes filtrados de FL-PATH-01.

### El broker ya separa disponibilidad y concesión

[`McpCapabilityBroker`](../../src/capability.rs) requiere autorización explícita
tras registrar una herramienta. Los cambios de política y catálogo invalidan
tokens. La [campaña FL-MCP](../../tests/fl_mcp01_authority_drift.rs) compara A/B/C
en 81 transiciones con 100 calentamientos y 10.044 ensayos medidos. En esta
ejecución C registró cero ampliaciones, admisiones indebidas y usos obsoletos;
4.464 controles legítimos funcionaron y se detectaron 3.968 cambios observados.
Los efectos de esa matriz Rust son contadores sintéticos.

El [despachador Cortex](../../01_KISH_ENGINE/babylon60/mcp/effect_dispatch.py)
añade firma, sesión, argumentos, revisión y consumo durable. Su suite verifica
efectos de fixture mediante otro proceso. La [especificación existente](fl-mcp01-authority-drift.md)
limita la evidencia al host confiable y a los handlers síncronos ensayados;
excluye efectos posteriores al retorno y servidores ajenos a esa integración.

### El perímetro actual depende del anfitrión

El [perfil Seatbelt](../../src/omega_mediation.rs) y las
[pruebas de egress](../../tests/test_install_policy.py) aportan defensas y controles
locales. El [informe NEMESIS](../../reports/nemesis_evidence_report.json) excluye
expresamente el compromiso del kernel/anfitrión y los canales físicos. No se
encontró una campaña A/B/C de microVM y perímetro independiente en las rutas
examinadas. La whitelist de egress contiene `[PENDING_BFT_SIGNATURE]`; no se
localizó su aplicación operativa. No equivale a un perímetro activo.

### La topología distribuida todavía no evalúa conocimiento sustentado

[`AutodidactSwarmTopology`](../../02_EDIN_SWARMS/agents_archi/topologies/autodidact_topology.py)
registra recuentos de afirmaciones, ejecuta callbacks de verificación y puede
sintetizar premisas no refutadas sin comprobar sus citas. El
[`tracker de cuota`](../../02_EDIN_SWARMS/agents_archi/clients/openrouter.py)
cuenta intentos de solicitud, no tokens agregados. El
[`ledger CORTEX`](../../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py)
sí conserva identidad, hash, dominio y reloj lógico de eventos recuperados.

Antes de reutilizar la procedencia Rust, revisar
[`provenance.rs`](../../01_KISH_ENGINE/cortex/crates/cortex-core/src/provenance.rs)
y [`reopen.rs`](../../01_KISH_ENGINE/cortex/crates/cortex-core/src/reopen.rs):
calculan SHA-256 pero etiquetan resultados como `sha3-256:`. Esta discrepancia
se observó en fuente; su uso productivo no quedó establecido. Un hash tampoco
comprueba que una cita exista o respalde una afirmación.

## Plan de implementación

El orden propuesto responde a los contraejemplos y dependencias observados.
Los destinos nuevos de esta sección son propuestas, no archivos implementados.

1. **Cerrar el contrato común de evidencia.** Definir manifiesto de campaña con
   versión, semilla, amenaza, configuración, permisos, presupuesto, escenarios,
   controles y criterio de fallo. Identificar intención, intento, sesión,
   autorización y testigo por separado. Registrar `UNKNOWN` ante pérdida de
   observación y contabilizarlo; un caso desconocido no cuenta como cero efectos.
   Reutilizar ledgers y observadores existentes, sin crear otro broker.
2. **Corregir FL-REC-01 primero.** Añadir regresiones en
   `tests/fl_rec01_recovery_provenance.rs` para los dos casos reproducidos, WAL
   parcial, testigo de otra sesión, recibo obsoleto y error tras efecto parcial.
   Conservar ambigüedad o ausencia de intención cuando falta evidencia; propagar
   fallos de persistencia. Integrar después reconciliación, procedencia CORTEX y
   observador. Comparar A memoria conversacional, B ledger y C ledger más
   procedencia y observador en 5.000 casos predefinidos, con fallos en reserva,
   despacho, efecto y persistencia. Incluir compactación, snapshots corruptos y
   reinicios reales concurrentes. Exigir en C cero replays no autorizados,
   recibos fabricados, mezclas entre sesiones y éxitos no verificados; medir finalización legítima,
   latencia p99, incertidumbre y reconciliación. Sin idempotencia verificable,
   un resultado incierto impide el reintento automático.
3. **Completar FL-PATH-01.** Reutilizar la resolución canónica de `secure_fs`
   en los consumidores de lectura, empezando por la ingestión de skills. Ligar
   la adquisición del descriptor raíz a autorización e identidad verificadas;
   especificar renombrados, revocación, hardlinks y cruces de montaje. Añadir
   `tests/fl_path01_capability_root_escape.rs`: A prefijo, B componentes y C
   resolución mediante descriptor, sobre 10.000 operaciones medidas después de
   calentamiento. Usar canarios exteriores sintéticos, swaps concurrentes y un
   testigo de los bytes devueltos. Exigir en C cero lecturas exteriores, escapes por
   symlink, colisiones de prefijo y bytes filtrados; medir éxito legítimo,
   falsos rechazos y latencia p99. Un descriptor abierto que luego cambia de
   ubicación requiere una política de identidad explícita.
4. **Extender FL-MCP-01 sin reimplementarlo.** Mantener
   `tests/fl_mcp01_authority_drift.rs` y `tests/test_fl_mcp01_dispatch.py`.
   Inventariar todas las rutas con efectos, incluyendo acceso directo a handlers
   y tareas asíncronas, y llevar cada integración nueva al mismo punto de
   mediación. Conservar cero ampliaciones, efectos indebidos y bypasses por
   política obsoleta; medir éxito legítimo, falsos rechazos, detección de deriva
   y resolución p99. Las firmas software de las pruebas no sustituyen la
   validación hardware de un despliegue protegido.
5. **Construir FL-PERIM-01 en infraestructura separada.** Definir primero si
   se compromete proceso, invitado, host de VM o broker. Situar perímetro,
   claves y observador fuera del host declarado comprometido. Proponer
   `scripts/experiments/fl_perim_01/` con políticas A proceso, B microVM y C
   perímetro independiente más mediación; 1.000 escenarios de destinos y
   credenciales sintéticos, relays, deriva concurrente y pérdida de observación.
   Verificar llegadas en destino, cero efectos/bypasses/relays indebidos en C, éxito
   legítimo, latencia p99, cobertura y unknowns. La provisión de infraestructura
   y cualquier efecto protegido se preparan con su autorización y atestación.
   Separar el estudio de canales CPU/caché/almacenamiento: mensajes sintéticos,
   controles sin señal, orden aleatorizado, muestras independientes, bits/s y
   contraste estadístico registrado. No inferir ausencia universal de canales.
6. **Evaluar FL-DBR-01 tras estabilizar evidencia y permisos.** Proponer
   `scripts/experiments/fl_dbr_01.py` y `tests/test_fl_dbr_01.py`. Congelar 100
   unidades con fuentes y adjudicación independiente; reservar proyectos y
   episodios completos antes del ajuste. Comparar A recuperación monolítica,
   B distribución y síntesis, C distribución más verificador y broker. Fijar
   corpus, modelo exacto, permisos y presupuesto agregado; incluir tokens de
   verificación, síntesis, recuperación y reintentos. Antes de aceptar una
   afirmación, comprobar localizador, bytes/digest y respaldo del fragmento;
   sin verificador permanece `UNVERIFIED`. Medir precisión, recall,
   contradicciones, citas fabricadas, duplicación, tokens por afirmación validada
   y por afirmación nueva, latencia p95 y efectos no autorizados. Registrar incertidumbre y
   denominadores antes de ejecutar, incluido recall basal cero. La predicción
   exige mejora relativa de recall de al menos 20 %, pérdida de precisión de
   como máximo 2 puntos porcentuales, cero efectos indebidos y menor coste por
   afirmación nueva. El número de investigadores es un parámetro experimental;
   100 unidades no obliga a lanzar 100 agentes.

Cada banco debe detectar un control deliberadamente inseguro y permitir tareas
legítimas. Un fallo observado falsará la propiedad correspondiente; las campañas
favorables solo permiten `SUPPORTED_WITHIN_DOMAIN` en el dominio registrado.

## Verificación ejecutada

| Comprobación | Resultado y alcance |
| --- | --- |
| Cuatro suites Rust dirigidas | 50 pasan: admisión 5, NEMESIS adversarial 28, deriva MCP 7 y Wave IV 10. |
| Dos tests unitarios Seatbelt | 2 pasan; comprueban generación de perfiles, no compromiso del host. |
| Integración Python MCP con librería reconstruida | 15 pasan, 1 omitido por atestación hardware voluntaria. |
| Topología distribuida y recuperación de eventos | 4 pasan; no comparan calidad de conocimiento A/B/C. |
| Sonda de recuperación | Reproduce las dos confirmaciones sin evidencia causal suficiente. |

En la auditoría inicial se ejecutaron 71 tests existentes con éxito y una omisión
explícita. Los dos contraejemplos se corrigieron después en la nota enlazada al
principio. No se ejecutaron las campañas nuevas de 1.000, 5.000
o 10.000 casos ni inferencia de pago.

Comandos de las comprobaciones ejecutadas:

```sh
cargo test -q --locked -p babylon60_root --test fl_mcp01_authority_drift --test admission_capability_test --test nemesis_wave4 --test adversarial_nemesis -- --nocapture
cargo test -q --locked -p babylon60_root --lib seatbelt_ -- --nocapture
cargo build -q --locked -p babylon60_root --lib --features python
BABYLON60_TEST_CAPABILITY_LIBRARY="$PWD/target/debug/libbabylon60.dylib" uv run --locked pytest tests/test_fl_mcp01_dispatch.py -q
uv run --locked pytest tests/test_autodidact_omega_pipeline.py::test_autodidact_swarm_topology_async_execution tests/test_agents_archi.py::test_royal_rumble_100_iterations_3_interrupts_model_switch -q
uv run --locked pytest tests/test_cortex_query_filters.py::test_individual_filters_are_exact_and_preserve_event_evidence tests/test_cortex_query_filters.py::test_reopening_preserves_history_hashes_and_append_only_durability -q
```

La compilación Python fresca sustituyó una comprobación inicial sobre una
librería anterior a las fuentes. La sonda se reproduce desde la raíz del repo:

```sh
cargo build -q --locked -p babylon60_root --lib
rustc --edition=2021 docs/security/evidence/recovery-audit-2026-10-26.rs --extern babylon60=target/debug/deps/libbabylon60.rlib -L dependency=target/debug/deps -o /tmp/b60-recovery-audit
/tmp/b60-recovery-audit
```

La sonda crea y elimina únicamente un directorio temporal propio. Sale con éxito
cuando observa los contraejemplos registrados; después de corregirlos, fallará
su aserción y deberá sustituirse por las regresiones de aceptación del paso 2.

Controles de la auditoría inicial: auditor semántico, presupuesto local y topología pasan;
los 19 enlaces locales originales existen y ambos archivos añadidos superan el control de
espacios y el formato Rust de la sonda. Se omiten explícitamente la configuración
global y la telemetría de ghost listeners. `git diff --check` global falla en
`tests/test_markov_bridge.py:145` por una línea vacía al final de un archivo con
cambios ajenos. Esta tarea no modifica ese archivo. No se prepara commit ni se
certifica el runtime mediante estos controles documentales.
