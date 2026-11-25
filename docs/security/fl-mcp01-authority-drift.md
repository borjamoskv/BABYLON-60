# FL-MCP-01 — Implicit authority drift

Actualizado: 26 de octubre de 2026. Estado: `SUPPORTED_WITHIN_DOMAIN` para el
broker Rust y el despachador Cortex sobre ledgers temporales con firmas de
prueba y testigo independiente. Validación biométrica hardware: `NO_VERIFICADO`.

## Contrato y cambio

La disponibilidad externa no concede autoridad. En
[`McpCapabilityBroker`](../../src/capability.rs), registrar servidores y
herramientas solo actualiza el catálogo. El plano de control de confianza debe
llamar expresamente a `authorize_tool` con una definición revisada. La concesión
acota identidad/hash, efectos y recursos; se comprueba tanto al emitir un token
como al validar su uso. `revoke_tool` retira la concesión.

`update_external_policy` resuelve `Enabled`, `Disabled` y `Unconfigured`.
Un valor explícito prevalece sobre el global; una herencia sin valor habilitado
resuelve a no disponible. La política externa puede reducir disponibilidad, pero
no modificar las concesiones. Este es un modelo sintético, no un adaptador de
las políticas de GitHub ni una certificación de su comportamiento.

Cambios en política, catálogo o concesiones invalidan tokens mediante revisiones
monótonas. Restaurar un valor anterior no restaura tokens antiguos (ABA).
Re-registrar un servidor borra sus concesiones. Refrescar valores idénticos no
invalida tokens. Los tokens y las tablas internas son privados: un consumidor no
puede cambiar la época de un token ni escribir directamente en las concesiones.

Cambio de API: los consumidores deben autorizar después de registrar; consultar
`issued_epoch()` y `token_id()` en lugar de acceder a campos del token. Se adaptan
las pruebas FL-008 y su ejemplo. No se modifican dependencias ni lockfiles.

## Evidencia del broker — 23 de octubre

La PoC previa al cambio registró un servidor y una herramienta, sin concesión
independiente: obtuvo 10.000 capacidades en 10.000 intentos y falló el criterio
de cero ampliaciones. La misma prueba permanece en
[`fl_mcp01_authority_drift.rs`](../../tests/fl_mcp01_authority_drift.rs).

```sh
cargo test -q --locked -p babylon60_root --test fl_mcp01_authority_drift --test admission_capability_test -- --nocapture
cargo test -q --locked -p babylon60_root --doc capability::
cargo check -q --locked -p babylon60_root --example fl008_mcp_capability_activation
python3 scripts/c5_quality_gates/audit_token_budget.py
python3 scripts/guards/verify_active_topology.py
```

Entorno observado: Apple M3 Pro, arm64, rustc 1.97.1; perfil de tests debug,
sin MCP externo ni operaciones protegidas. El estrés usa 100 calentamientos y
10.044 ensayos medidos: 124 repeticiones de 81 transiciones entre pares
de estados local/global. A hereda automáticamente; B hereda y observa deriva;
C usa el broker real con concesiones independientes. A y B son referencias
deliberadamente inseguras del arnés, no implementaciones de productos externos.

| Medida sintética | Resultado |
| --- | ---: |
| `implicit_capability_expansions_C` | 0 |
| `unauthorized_mcp_effects_C` (admisiones simuladas) | 0 |
| `stale_policy_bypasses_C` | 0 |
| `legitimate_tool_success` | 4.464 / 4.464 |
| `false_rejection_rate` | 0 / 4.464 |
| `configuration_drift_detection` (tokens previos, cambios observados) | 3.968 / 3.968 |
| Admisiones sin concesión en A y B | 4.464 cada uno |

El arnés imprime `policy_resolution_latency_p99_ns`: mide actualización de
política y petición denegada en C, en el proceso de pruebas. Es un diagnóstico
local con `Instant`, sin objetivo de latencia ni extrapolación a producción;
no participa en hashes ni en el estado causal.

También cubre ampliaciones de efectos/recursos, cambios de hash, servidores y
herramientas nuevos, revocación, re-registro, ABA, desbordamiento de vigencia y
cambio de política desde otro hilo entre emisión y validación. Dos doctests
`compile_fail` comprueban que tablas y épocas no son mutables desde consumidores.

Resultado de ejecución: 12 tests dirigidos y 2 doctests pasan; el ejemplo
FL-008 completa 10.000 intentos adversariales y 2.500 controles legítimos sin
admisiones indebidas. Compilación del ejemplo, presupuesto, topología, enlaces
locales y `git diff --check` pasan.

## Integración del despachador — 24 de octubre

[`CortexMCPServer`](../../01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py)
media los handlers con efectos mediante
[`EffectDispatcher`](../../01_KISH_ENGINE/babylon60/mcp/effect_dispatch.py) y el
[puente PyO3](../../src/mcp_python.rs) al mismo broker Rust. No se duplica el
motor de políticas en Python. Sin librería nativa, clasificación de efecto o
aprobación válida, el handler no se invoca. Los diagnósticos de una lista cerrada
siguen disponibles; añadir un handler no le concede autoridad. Los aliases
se normalizan antes de validar. `tools/list` anuncia el requisito en `_meta`.

La aprobación exacta incluye sesión aleatoria, revisión causal, herramienta,
hash BLAKE3 de código/módulo/mediador/kernel, efecto y snapshot de argumentos.
El cliente puede preparar ese documento, pero no firmarlo ni crear concesiones.
La firma P-256 se verifica con `VerificationGate.is_allowed`; ninguna
puntuación, etiqueta de riesgo o booleano del cliente puede sustituirla.
La adquisición hardware sigue en el CLI existente, fuera del MCP.

El mismo lock cubre cambios externos, validación y la ejecución completa del handler.
[`VerificationGate.execute_once`](../../01_KISH_ENGINE/babylon60/verification/verification_gate.py)
consume el `execution_id` en SQLite WAL `synchronous=FULL` antes del efecto.
Una segunda transacción `BEGIN IMMEDIATE` revalida y excluye escritores de
aprobación/revocación durante el efecto. Si el proceso cae entre ambas,
la ejecución sigue consumida. Si el handler falla después de empezar,
la respuesta indica `EFFECT_OUTCOME_UNKNOWN`; no afirma que el efecto se denegó
ni permite un replay con el mismo identificador.

### Uso y comprobación

Construir explícitamente la librería (no se compila desde un tool call):

```sh
cargo build -q --locked -p babylon60_root --lib --features python
uv run --locked python -m babylon60.mcp.cortex_mcp_server \
  --ledger /ruta/ledger.db --causal-gate /ruta/approvals.db \
  --capability-library /ruta/libbabylon60.dylib
```

En Linux, usar la librería `.so`. Las rutas pertenecen al despliegue de confianza;
no se aceptan rutas de librería desde una petición MCP.

Enviar `tools/call` con el nombre/argumentos propuestos y:

```json
{"_meta":{"babylon60/authorization":{"execution_id":"ID-NUEVO","mode":"prepare"}}}
```

Guardar `result.approval_task` exactamente como JSON y aprobar fuera del MCP:

```sh
uv run --locked babylon60 approve ID-NUEVO --db /ruta/approvals.db --task-file /ruta/task.json
```

Reenviar la llamada con `_meta.babylon60/authorization.mode` igual a `execute`.
La sesión debe seguir activa. Un cambio de argumentos, código, sesión o política
requiere preparar y aprobar una tarea nueva. No borrar el consumo para reintentar
un resultado incierto. Conservar la clave pública aprovisionada en
`BABYLON_ENCLAVE_PINNED_PUBKEY`; nunca fijarla a partir del autorreporte del helper.

Pruebas del despachador y los controles existentes:

```sh
BABYLON60_TEST_CAPABILITY_LIBRARY="$PWD/target/debug/libbabylon60.dylib" \
uv run --locked pytest tests/test_fl_mcp01_dispatch.py tests/test_cortex_mcp_server.py \
  tests/test_ax0_mcp_isolation.py tests/test_authorization_regression.py \
  tests/test_causal_hitl_verification_gate.py tests/test_agents_archi.py \
  tests/test_mcp_deduction.py tests/test_audit_mcp_lifecycle_regressions.py -q
```

La PoC previa a esta integración produjo una fila real mediante `tools/call`
sin autorización; un proceso lector independiente la detectó. Se probaron
10 calentamientos y 100 repeticiones (deduplicadas por el ledger), con resultado
contrario al criterio. Tras la corrección, las llamadas sin permiso no producen
filas. La prueba positiva comprueba firma real con una clave software aislada,
handler real, fila persistida y dispositivo/inodo observados desde otro proceso.
No se parchean ni el verificador ni el broker. Otro caso recorre stdio JSON-RPC
entre procesos y verifica el mismo efecto y la ausencia de replay.

Resultado observado el 24 de octubre: 86 tests Python pasan y uno se omite
explícitamente (biometría hardware). Las 12 regresiones Rust pasan; la librería
se compiló con `--features python` y el adaptador se cargó y ejercitó realmente.
Ruff y `cargo check --locked --features python` pasan.

La suite cubre las 81 transiciones local/global: cuatro casos habilitados sin
deriva producen efecto; los otros 77 no producen efecto. Incluye ABA,
revocación, argumentos/identidad alterados, clave incorrecta, ausencia de clave,
consumo seguido de terminación del proceso, actualización concurrente y error
posterior al efecto. Los tests anteriores de mutación sin configuración ahora
esperan rechazo; el control positivo está en esta suite firmada.

Para el intento hardware único, con clave de confianza previamente aprovisionada:

```sh
BABYLON60_RUN_HARDWARE_ATTESTATION=1 \
BABYLON60_TEST_CAPABILITY_LIBRARY="$PWD/target/debug/libbabylon60.dylib" \
uv run --locked pytest tests/test_fl_mcp01_dispatch.py -k hardware_attested_fixture_effect -q
```

En esta sesión no está configurada la clave fijada: ese intento no se ejecuta.
El test hardware no usa claves de prueba, helpers sustituidos ni reintentos.

## Mediación de handlers directos y tareas asíncronas

Ampliación del 26 de octubre: las entradas con efectos de `CortexMCPServer` y
`BabylonMailIntegration.send` exigen una invocación mediada activa. Se comprueban
despachador, herramienta, argumentos canónicos, hilo y tarea propietarios. Las
sobrescrituras en subclases conservan el guard; los nuevos métodos `_tool_`
sin clasificación quedan protegidos por defecto. La lista de diagnósticos
observacionales sigue cerrada y requiere código revisado.

Una llamada directa carece de ese contexto y no alcanza el cuerpo del handler.
Un contexto copiado queda inutilizado al terminar la invocación. Un hijo o un
hilo no puede heredar el permiso para llamar directamente a otro handler ni
volver a invocar el mismo. El código de un efecto tampoco puede reentrar en
el despachador o modificar su propia política. El hash de aprobación se liga
al código original del handler, además del mediador y el kernel.

El ingreso MCP continúa siendo síncrono. Si el handler devuelve una operación
awaitable, el despachador la completa en un ciclo `asyncio` privado antes de
responder. Las tareas hijas creadas en ese ciclo se registran y se esperan,
incluidas las creadas por otros hijos. Ante fallo o cancelación se cancelan y
esperan las pendientes. El lock de política y la transacción de aprobación
siguen activos durante la operación y el cierre del ciclo; ningún awaitable
se devuelve al cliente como si ya fuera un resultado.

El ciclo privado evita cambiar el gestor de tareas de una aplicación ajena.
La ejecución desde un hilo que ya tiene un ciclo activo se rechaza antes de
invocar el handler; preparación y diagnósticos siguen disponibles. El modelo
se apoya en la gestión de ciclo y cierre de
[`asyncio.Runner`](https://docs.python.org/3.14/library/asyncio-runner.html)
y en el registro de tareas mediante
[`set_task_factory`](https://docs.python.org/3.14/library/asyncio-eventloop.html#asyncio.loop.set_task_factory).
Context7 no pudo responder por cuota agotada; se consultó la documentación
oficial de Python como alternativa.

Los errores después de iniciar el efecto, incluida una cancelación asíncrona,
producen `EFFECT_OUTCOME_UNKNOWN`. El identificador permanece consumido: no se
infiere que el efecto no ocurrió y no se habilita un replay automático.

Regresiones nuevas: llamadas directas síncronas y asíncronas; handler nuevo sin
clasificar; contexto retenido tras el retorno; salto a otro hilo, tarea o
herramienta; intento de modificar la política desde el efecto; finalización de
hijos antes de liberar la política; cancelación de hijos pendientes; fallo y
cancelación tras una escritura real; y correo local firmado que sigue
registrándose una sola vez. Los testigos de escritura usan lectores SQLite
desde otro proceso sobre ledgers temporales, no el recibo del despachador.
Las claves de firma son software aislado y no acreditan Secure Enclave.

Antes del cambio, 10 calentamientos y 100 llamadas directas produjeron una fila
real no autorizada (el ledger deduplicó los intentos). El handler asíncrono
devolvía una corutina sin ejecutar. Ambas regresiones fallaron antes del cambio.

Tras reconstruir explícitamente la librería con `--features python`, el comando
de integración de la sección anterior da **109 tests correctos y una omisión**
(atestación biométrica voluntaria). Ruff sobre los tres módulos y la suite
modificados pasa. Mypy estricto de esos tres módulos y la suite, con imports
externos silenciados, también pasa. Se conservan las firmas, la validación nativa y el
consumo durable del verificador; no se modifican dependencias ni lockfiles.

## Límites de la evidencia

`commit_execution` valida admisión y emite evidencia; no realiza el efecto MCP.
El contador de efectos del arnés es sintético, sin testigo físico independiente.
No demuestra ausencia de efectos reales ni confinamiento del sistema operativo.
La campaña inicial solo cubría pruebas y el
[`ejemplo FL-008`](../../examples/fl008_mcp_capability_activation.rs); la integración
posterior añade el despachador Cortex y su transporte stdio.

El integrador debe reservar `authorize_tool` al plano de control autenticado;
no exponerlo al agente, descubrimiento ni sincronización de políticas. El broker local no autentica por sí solo al operador: Cortex exige la firma del
verificador existente. Las concesiones no persisten entre sesiones; el consumo
sí persiste. El puente es en proceso y no crea un canal IPC o daemon adicional.

Para certificar runtime hay que mediar todos los efectos, serializar validación
y efecto frente a cambios de política, conservar los controles hardware
existentes y observar el resultado con un testigo independiente conforme a los
[contratos de evidencia y atestación](../03_guides/agent_contracts.md).
Un único efecto sin concesión efectiva falsaría esa garantía. Esta evidencia
cubre las entradas protegidas Cortex, las tareas del ciclo privado y los efectos
de fixture ensayados. No cubre otros servidores MCP, introspección o modificación
arbitraria del código Python, acceso directo al backend/DB/clave desde un host
hostil, ni trabajadores nativos externos al ciclo que produzcan I/O sin pasar
por las entradas protegidas. La autoridad no se convierte en confinamiento del
sistema operativo ni en capacidad de cancelar una syscall ya emitida.
No se despliega el runtime ni se certifica procedencia Secure Enclave mediante
firmas software. La ausencia actual de la clave fijada bloquea esa última
validación hardware, no se sustituye por una clave generada para las pruebas.
