# CORTEX: idempotencia ligada a la intención

Fecha: 2026-11-18. Alcance: adaptador MCP stdio, broker nativo disponible y
SQLite temporal de ensayo. No modifica el protocolo ni usa memoria de producción.

## Contrato observado

La distinción de [Stripe, API v1](https://docs.stripe.com/api/idempotent_requests)
es pertinente: el reintento reclama el resultado original; reutilizar la clave
con parámetros distintos debe producir un error. No se trasladan sus políticas
de caducidad, retención de errores ni comportamiento de API v2.

En [`Adapter.write`](../../01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py),
la búsqueda de `(proyecto, actor, request_id)` ocurre bajo `BEGIN IMMEDIATE`.
El registro guarda un digest de `{"tool": tool, "args": args}`; el reintento
lo recalcula con la versión del proyector del registro original. La
serialización canónica ordena las claves JSON. Un digest distinto produce
`isError: true`, `status: denied` y el motivo explícito
`request_id already used with different content`.

El ACK de escritura identifica la fila con `memory_id`, `seq` y `entry_hash`.
El contenido y el digest de la operación se comprueban en esa fila: el ACK no
contiene por sí solo todo el contenido acreditado. El error no devuelve esos
campos ni un receipt de éxito. Las denegaciones pueden añadir eventos de
auditoría `memory.decision`; no añaden una operación de memoria.

## Prueba reproducible

[`test_cortex_memory_idempotency.py`](../../tests/test_cortex_memory_idempotency.py)
reutiliza el cliente MCP del harness y crea un ledger independiente por caso.
Emplea procesos reales, vínculos Ed25519 de ensayo y el broker nativo, sin mocks
de persistencia ni de autorización.

| Caso | Comprobación |
| --- | --- |
| `R1`: «idioma preferido: euskera» | `SIGKILL` después del commit y antes del ACK; queda exactamente una operación persistida con ese contenido. |
| Repetición idéntica | `replayed: true`; mismo `memory_id`, `seq` y `entry_hash` que la fila original. |
| `R1`: «idioma preferido: castellano» | Error explícito; sin recibo de éxito en `structuredContent` ni en el texto MCP; filas de operaciones idénticas a las anteriores. |
| Cambio de atributo o de herramienta | Misma denegación; no se añade ni altera una operación. |
| Claves JSON en orden inverso | Recupera el recibo original sin conflicto. |
| Conflicto antes del primer reintento válido | Rechaza el cambio y conserva la posibilidad de recuperar el resultado original. |
| Otro actor, mismo proyecto | La misma clave admite otra operación y su propio reintento. |
| Mismo actor, otro proyecto | La misma clave admite otra operación y su propio reintento. |

Se comprueba también el digest BLAKE3 del contenido original mediante una
serialización independiente. La evidencia no se limita a contar filas.

```sh
uv run --locked pytest tests/test_cortex_memory_idempotency.py -q
uv run --locked pytest tests/test_cortex_memory_mcp.py tests/test_cortex_memory_idempotency.py -q
uv run --locked ruff check tests/test_cortex_memory_idempotency.py
uv run --locked mypy tests/test_cortex_memory_idempotency.py --follow-imports=silent
```

Primera ejecución en el checkout compartido: **4 passed** en los casos nuevos y **28 passed** en la suite
conjunta del adaptador (31,95 s), Ruff y comprobación de tipos correctos.
También pasan los contratos semánticos, presupuesto de instrucciones, topología,
los dos enlaces locales de este documento y `git diff --check`.
La suite omite los casos si falta el broker nativo; una ejecución omitida no
acredita este contrato.

Revalidación para publicación sobre `ab35f40f` en un worktree aislado, incluyendo
únicamente los dos archivos de esta tarea: **27 passed** (106,11 s), sin casos
omitidos. Esa base conserva el proyector `/2`; no incluye el caso adicional de
la edición concurrente `/3`. Se reutilizaron el entorno bloqueado y el broker
nativo del checkout principal, con `UV_PROJECT_ENVIRONMENT`,
`CORTEX_MEMORY_BROKER_LIB` y `uv run --locked --no-sync`. Ruff, tipos y los
controles documentales también pasan en esa base.

## Límites

Se verificó pérdida del proceso tras commit con SQLite WAL; pérdida de corriente
y cachés de almacenamiento quedan `NO_VERIFICADO`. El control de normalización
cubre el orden de las claves del objeto, no equivalencias arbitrarias entre
valores, Unicode, listas, ausencia y `null`. No acredita entrega al cliente del
ACK perdido ni ejecución en Stripe o DeepSeek Harness.

Durante el trabajo hubo cambios concurrentes del proyector en el checkout.
Las pruebas se mantienen en un archivo independiente y usan la versión vigente
del proyector; este cambio aporta pruebas, sin modificar el protocolo.
Las verificaciones documentales se limitan al workspace: se omiten configuración
global y telemetría de ghost listeners.
