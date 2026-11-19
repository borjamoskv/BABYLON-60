# CORTEX: revalidación tras corregir una fuente

Fecha: 2026-11-18. Alcance: adaptador MCP de memoria y proyector Python;
comprobación local con SQLite temporal y broker nativo existente.

## Contrato y resultado

Resultado esperado: una inferencia dependiente de una versión sustituida deja de
servirse como vigente, conserva su justificación histórica y no invalida otra
inferencia independiente. Se comprueban tanto 500→300 como 500→600 para un pedido
de 400 €. En ambos casos el estado correcto es `PENDING_REVALIDATION`, sin decidir
automáticamente si la conclusión es falsa.

Rutas: [adaptador](../../01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py),
[proyector](../../01_KISH_ENGINE/babylon60/mcp/cortex_memory_core.py),
[aceptación nueva](../../tests/test_cortex_memory_dependencies.py),
[regresiones y replay](../../tests/test_cortex_memory_mcp.py) y
[contrato MCP](../01_spec/spec_cortex_memory_mcp.md#5a-dependencias-de-versión-y-revalidación).
Restricciones: conservar cambios ajenos, dependencias y lockfiles; no modificar
el ledger del usuario ni atribuir atestación hardware a pruebas locales.

| Criterio | Resultado observado | Evidencia |
| --- | --- | --- |
| Registrar dependencia de una versión | `depends_on=[S1.memory_id]` queda en el evento y en el histórico | Casos 300 y 600 |
| Vista actual tras sustitución | I1 no aparece al abrir otro proceso MCP | Casos 300 y 600; PID e instancia distintos |
| Vista histórica | I1 conserva texto y S1; S1 conserva su hash y enlaza a S2 | Trazas JSON |
| Control independiente | Sigue `ACTIVE` y disponible en la consulta actual | Casos 300 y 600 |
| Corrección sin cambio de verdad | 600 también exige revalidar la justificación | Caso 600 |
| Recibos anteriores | Se verifican formatos `/1` y `/2` con sus algoritmos originales | Prueba parametrizada de replay legacy |

## Hallazgo y transferencia desde Nix

La ejecución previa a la corrección falló en los dos casos al crear I1:
`status="invalid"`, `unexpected arguments: ['depends_on']`. Es un fallo de la
primera etapa del protocolo propuesto, no evidencia de haber completado antes
una prueba de sustitución con dependencias válidas. El proyector anterior solo
excluía al elemento sustituido u olvidado; no tenía dependencias ni estado de
revalidación.

La revisión de [Nix 2.34.9, references.cc](https://github.com/NixOS/nix/blob/2.34.9/src/libstore/references.cc)
confirma que `search` busca hashes candidatos en bytes, y `RefScanSink` conserva
el extremo del fragmento anterior para detectar referencias que cruzan bloques.
El [manual de construcción](https://nix.dev/manual/nix/2.34/store/building.html)
explica su registro como dependencias. Las consultas
[`--referrers` y `--referrers-closure`](https://github.com/NixOS/nix/blob/2.34.9/doc/manual/source/command-ref/nix-store/query.md)
recorren la relación inversa, directa o transitiva. Se inspeccionaron código y
documentación oficiales; no se ejecutó ni modificó Nix.

La transferencia consiste en registrar dependencias e invalidar su vigencia.
No se copia el escáner: I1 no contiene literalmente S1 ni su ID en el texto; la
relación existe solo en el argumento estructurado. Tampoco se construye un grafo
global ni una segunda base: la proyección usa el orden de eventos ya existente.

El [README citado](https://github.com/borjamoskv/BABYLON-60/blob/6c8944482b8b59ccb94245dd666e4ae1329220b8/README.md)
y el [handoff citado](https://github.com/borjamoskv/BABYLON-60/blob/6c8944482b8b59ccb94245dd666e4ae1329220b8/HANDOFF.md)
describen superficies distintas: la ontología `SourceRecord` y el adaptador
`memory_supersede` no constituían por sí solos un contrato compartido de
dependencias. El módulo de gobernanza posee otras relaciones y estados; este
cambio se limita a la ruta MCP del handoff.

## Comportamiento añadido

- Referencias por `memory_id` inmutable, no por entidad ni por búsqueda textual.
- Dependencias existentes, activas y del mismo proyecto, comprobadas dentro de
  la transacción de escritura. Se rechazan versiones ausentes, ajenas o inactivas.
- Invalidación directa y transitiva al sustituir u olvidar una fuente. El orden
  de registro permite recorrer los elementos una vez sin recursión.
- `memory_read(view="history")` muestra contenido, dependencia y estado;
  la consulta por defecto entrega solo elementos activos.
- La revalidación crea otra versión con fuentes vigentes. Ni un reintento ni
  sustituir una inferencia omitiendo sus dependencias renuevan la justificación.
  Sus descendientes antiguos siguen pendientes.
- Proyector `/3` para las nuevas vistas; replay `/1` y `/2` conserva los formatos
  anteriores, sin reescribir eventos ni cambiar la cadena del ledger.

## Validación reproducible

```sh
uv run --locked pytest tests/test_cortex_memory_dependencies.py \
  tests/test_cortex_memory_mcp.py tests/test_cortex_ptc_ralph.py -q
# 71 passed

uv run --locked ruff check 01_KISH_ENGINE/babylon60/mcp/cortex_memory_core.py \
  01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py \
  tests/test_cortex_memory_dependencies.py tests/test_cortex_memory_mcp.py

uv run --locked mypy --follow-imports=silent \
  01_KISH_ENGINE/babylon60/mcp/cortex_memory_core.py \
  01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py \
  tests/test_cortex_memory_dependencies.py tests/test_cortex_memory_mcp.py
```

Las pruebas nuevas usan procesos MCP reales, broker nativo y SQLite, sin sustituir
esas fronteras por mocks. Incluyen dependencias transitivas, varios padres,
olvido, revalidación explícita, idempotencia, aislamiento entre proyectos,
autosustitución circular y entradas malformadas. La carrera derivación/corrección
ejecuta dos rondas de calentamiento y veinte de comprobación: o se admite I1 antes
de la corrección y queda pendiente, o se rechaza por fuente inactiva; nunca queda
como conclusión actual. La suite existente añade sus casos de crash y replay.

Las trazas conservan respuestas, PID, instancia, hashes y recibos:
[500→300](evidence/cortex-source-revalidation-20261118/limit-300.json) y
[500→600](evidence/cortex-source-revalidation-20261118/limit-600.json).
Cada una verifica tres recibos con `chain_ok=true` y ningún mismatch.
Los JSON documentan la ejecución; repetir la suite produce los ledgers temporales
y una nueva traza, con identificadores y hashes propios de esa ejecución.

La [salida de pytest](evidence/cortex-source-revalidation-20261118/pytest.log)
registra 71 pruebas pasadas. Una comprobación separada de conformidad PTC e
idempotencia pasó otros 17 casos. Tras terminar la sesión concurrente, la
[comprobación conjunta](evidence/cortex-source-revalidation-20261118/compatibility.log)
de dependencias y lecturas causales pasó 29 casos (15 de dependencias ya incluidos
en los 71 anteriores y 14 causales). Ruff y MyPy pasaron sobre los cuatro archivos
Python de esta tarea. También pasaron los controles semántico, presupuesto del
workspace, topología, `git diff --check` y los enlaces/anclas locales de los
dos documentos editados.

Entorno observado: Python 3.14.0, SQLite 3.50.4 y macOS 26.6.2 arm64.
El [registro de entorno](evidence/cortex-source-revalidation-20261118/environment.json)
incluye hashes BLAKE3 de fuentes y broker observados después de la prueba; no es
un sellado de release ni demuestra ausencia de escritores concurrentes.

## Validación del conjunto aislado para Git

Se preparó un worktree sobre `bba00a929699dad6389b7cd4bc2e7320071a4853`,
con solo la corrección de revalidación, pruebas, contrato y evidencia. Se
excluyeron los cambios concurrentes de revisiones causales del adaptador y del
replay, así como los cambios del ledger, gobernanza, PTC y demás sesiones.
El checkout compartido y su índice no se modificaron para preparar el commit.

La [ejecución aislada](evidence/cortex-source-revalidation-20261118/isolated-pytest.log)
pasó **71 pruebas, sin fallos ni omisiones** usando el extra `dev` bloqueado y
`python -m pytest` dentro del entorno del worktree. Se fijó
`CORTEX_MEMORY_BROKER_LIB` a la biblioteca nativa existente, identificada por
hash en el [manifiesto aislado](evidence/cortex-source-revalidation-20261118/isolated-validation.json).
Las nuevas trazas [300](evidence/cortex-source-revalidation-20261118/isolated-limit-300.json)
y [600](evidence/cortex-source-revalidation-20261118/isolated-limit-600.json)
corresponden a este conjunto. Las trazas anteriores se conservan como evidencia
de la ejecución original sobre el árbol compartido, no como certificación del
contenido aislado. No se incluyó código de las otras sesiones para reproducirlas.

```sh
uv run --locked --extra dev python -m pytest \
  tests/test_cortex_memory_dependencies.py tests/test_cortex_memory_mcp.py \
  tests/test_cortex_ptc_ralph.py -q
```

## Corrección del invariante de CI tras el merge

El CI de `f8041c8261df75bd32335f643b43d57eff3a4799` ejecutó correctamente los
15 casos de dependencias y los 24 casos de Memory MCP en Linux con Python 3.11
y 3.12, pero falló `test_inv_c5_13_nesting_depth_ceiling`: `Adapter.write()`
tenía profundidad de anidamiento 5, superior al máximo 4. El fallo consta en
los jobs [3.11](https://github.com/borjamoskv/BABYLON-60-VAULT/actions/runs/44345445197/job/134946683729)
y [3.12](https://github.com/borjamoskv/BABYLON-60-VAULT/actions/runs/44345445197/job/134946684331).
La reproducción local del invariante también falló antes del cambio.

Se extrajo la validación del destino a `Adapter._validate_target()`. Su llamada
y la comprobación de dependencias siguen usando la proyección obtenida dentro
de `BEGIN IMMEDIATE`. Se conservan los rechazos de destino inexistente o inactivo
y la obligación de declarar dependencias al sustituir una inferencia. No se
modificó el invariante ni su lista de excepciones.

Tras la corrección pasan **120 pruebas por versión**, sin omisiones, en macOS:
[Python 3.11.16](evidence/cortex-source-revalidation-20261118/ci-python311.log)
y [Python 3.12.14](evidence/cortex-source-revalidation-20261118/ci-python312.log).
Los 119 casos funcionales incluyen revalidación, idempotencia, entradas inválidas,
replay y PTC; el caso adicional es el invariante que fallaba en CI. Ruff y MyPy
también pasan sobre el adaptador. Comando por versión, con la biblioteca nativa
disponible indicada mediante `CORTEX_MEMORY_BROKER_LIB`:

```sh
UV_PROJECT_ENVIRONMENT=.venv-ci-3.12 uv run --locked --extra dev --python 3.12 \
  python -m pytest tests/test_cortex_memory_dependencies.py \
  tests/test_cortex_memory_mcp.py tests/test_cortex_ptc_ralph.py \
  tests/test_cortex_memory_idempotency.py tests/test_cortex_mcp_server_malformed_input.py \
  tests/test_c5_invariants.py::test_inv_c5_13_nesting_depth_ceiling -q
```

Estos resultados locales no certifican el CI completo. El merge también presenta
fallos fuera de esta corrección: contexto documental obsoleto, campos privados en
un ejemplo Rust, detecciones del escáner en un test de Gemini, enlaces ausentes en
el paquete de terminal, una expectativa de workflow `claims`, un buffer de test
incompatible con Python 3.11 y la expectativa de salida del comando MCP `bomb`.
Los cuatro jobs fallidos de Matrix, Claims y Secret Sentinel repiten los
errores del padre `bba00a92`. No se incluyeron correcciones de esos componentes ni
cambios del checkout compartido.

## Límites

Una dependencia no declarada no se descubre. La prueba negativa sin `depends_on`
lo comprueba: el texto continúa disponible. El adaptador no decide la verdad,
no clasifica automáticamente la ontología ni demuestra que una fuente sustente
semánticamente la inferencia. Un consumidor todavía debe usar la vista actual;
una copia retenida en su contexto no se actualiza por modificar SQLite.

`history` incluye elementos olvidados con estado `FORGOTTEN`; no es borrado.
No se acredita corte de alimentación, Touch ID/Secure Enclave, despliegue,
interoperabilidad nueva con DSH ni protección frente a escritura arbitraria de
SQLite. Los controles documentales son locales al workspace; se omite telemetría
global de listeners. Hubo modificaciones concurrentes del adaptador para
revisiones causales: se preservan y no se atribuyen a esta corrección.
