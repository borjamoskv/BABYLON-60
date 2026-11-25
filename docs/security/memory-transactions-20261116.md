# Memoria: auditoría de transacciones de `add_record()`

Fecha: 2026-11-16. Alcance: [motor de gobernanza](../../01_KISH_ENGINE/babylon60/memory/governance.py), [regresiones transaccionales](../../tests/test_memory_transactions.py) y adaptación de los fixtures de [falsación](../../tests/test_memory_governance_falsification.py), [invariantes](../../tests/test_memory_second_order_invariants.py) y [concurrencia V05](../../tests/test_swarm100_round2_regressions.py).

## Hallazgos reproducidos

| Caso | Antes | Corrección |
| --- | --- | --- |
| Ledger en otro archivo, fallo al insertar el blob | 0 registros y 1 evento confirmado tras `IntegrityError` | Rechazo de configuración separada; todas las escrituras reciben la conexión transaccional del motor |
| Fallo al verificar la respuesta de una inserción | Excepción después del commit, con registro y evento persistidos | Proyección y verificación dentro de la transacción, antes del commit |
| Cambio de época mientras la inserción espera | Firma ligada a la época anterior y fila/evento a la nueva; error después del commit | Una instantánea de entrada firmada conserva la misma época en firma, evento y fila |
| Revocación entre lectura de fila y lectura del permiso | Consultas mezclaban estados de dos momentos | `get_record()` usa una transacción de lectura para fila, permiso y relaciones |
| Cadena con 1.026 registros | Se revocaban 1.025; el último conservaba estado y contenido | CTE de clausura con `UNION` sobre identificadores, sin corte de profundidad |

Cinco casos de regresión se ejecutaron contra una copia aislada del módulo anterior y fallaron: rechazo de base separada (dos variantes), rollback de la proyección, lectura consistente y época de firma. La prueba de cadena larga reprodujo por separado `1025 != 1026` antes de corregir la consulta.

## Contrato resultante

`add_record()` conserva su firma pública y pasa de 260 a 75 líneas. Las comprobaciones de UUID, contenido y firma preparan una entrada inmutable. Duplicados, ventanas temporales, cicatrices de retractación, permisos entre tenants, actividad de dependencias, modalidad, ciclos y sustitución por autoridad se comprueban bajo `BEGIN IMMEDIATE`. Los ayudantes de validación, planificación y persistencia usan la conexión del llamador; no abren ni confirman otra transacción.

Evento, reloj lógico, sustituciones, fila, blob y relaciones se confirman juntos, después de verificar la proyección. Revocación y retractación también pasan siempre su conexión al ledger. Se conservan WAL, `synchronous=FULL`, formatos de eventos y algoritmos criptográficos existentes.

**Compatibilidad:** `MemoryGovernanceEngine(..., ledger=...)` requiere que ambos apunten al mismo archivo SQLite. Se admite otra instancia de ledger y un alias de ruta al mismo archivo. Una base distinta se rechaza; no se migran ni fusionan bases existentes automáticamente. Sustituir el atributo `ledger` después de construir el motor tampoco habilita escrituras separadas: la validación de la conexión del ledger las rechaza sin persistir cambios.

La lectura que empezó antes de una revocación puede terminar usando su instantánea anterior. Las lecturas posteriores ven la revocación y la eliminación de permisos. Una respuesta de inserción representa el registro en el momento de su confirmación; no impide una revocación posterior.

## Evidencia

187 pruebas pasadas en total. El conjunto principal pasa sus 117 pruebas, sin omisiones, con este comando:

```sh
BABYLON60_TEST_GEOMETRY_LIBRARY="$PWD/target/debug/libbabylon60.dylib" \
  uv run --locked pytest tests/test_memory_transactions.py \
  tests/test_memory_governance_falsification.py \
  tests/test_memory_second_order_invariants.py \
  tests/test_fl019_geometry_workflow.py \
  tests/test_fl022_final_artifact_persist.py -q
```

La revisión de llamadores añadió otras 70 pruebas pasadas:

```sh
uv run --locked pytest tests/test_swarm100_round2_regressions.py -k v05 -q
# 7 passed, 48 deselected: selección de las regresiones de memoria.
uv run --locked pytest tests/test_fl027_provenance_authority.py -q
# 63 passed.
```

Las 32 pruebas nuevas cubren fallos SQLite en siete etapas de escritura, rechazo en el commit mediante una clave foránea diferida, fallo de proyección, rollback de revocación, UUID duplicado concurrente, visibilidad entre conexiones, permisos específicos, sustitución del ledger, lectura durante revocación, época y cadena larga. Las carreras controladas cubren ambos órdenes de derivación/revocación, ambos tipos de dependencia y acceso local o delegado. El estrés usa dos rondas de calentamiento y 32 rondas con dos insertores y un revocador. Se usan conexiones SQLite reales, triggers de fallo y callbacks de trazado para coordinar, sin reemplazar el almacenamiento por mocks.

Entorno: Python 3.14.0, SQLite 3.50.4, macOS 26.6.2 arm64. La integración geométrica utiliza la biblioteca local existente `target/debug/libbabylon60.dylib`, SHA-256 `057bbfaf339eeed8e285d9e84fbc862c1a04e4a42cc4425453e6f47860e9f20c`; este trabajo no recompila ni certifica su correspondencia con todo el código Rust actual.

Ruff sobre los cinco archivos Python afectados; MyPy con `--follow-imports=silent` sobre el motor y la suite nueva. Comprobación de diff, enlaces locales, auditoría semántica, presupuesto y topología del workspace. Se preservaron mediante comparación de hashes los archivos modificados previamente ajenos a este cambio, las dependencias, el ledger y el índice Git.

## Límites

Las pruebas verifican transacciones, integridad del ledger y reapertura de bases temporales. No certifican recuperación ante corte de alimentación, borrado físico de páginas WAL, aislamiento de procesos nativos ni atestación hardware. La resistencia de las cicatrices a paráfrasis semánticas y otros recorridos de retractación fuera de la clausura de revocación no se amplían. No se modifican dependencias ni lockfiles, ni se crea commit o publicación. Los controles documentales se ejecutan con alcance de workspace; se omite la telemetría global de listeners.
