# CORTEX Memory MCP Adapter — contrato mínimo (v0.1)

Estado: **MVP local verificado a nivel de protocolo y en DeepSeek Harness 0.2.2-rc.1-arm64** (v0.6: el modo inmutable solo como opción explícita; resumen de estado completo, validación de entrada, concurrencia, auditor de solo lectura en una sola instantánea, perímetro de autoridad explícito e interoperabilidad DSH verificada en sesiones aisladas A/B y modo solo lectura C; ver §8).

## 1. Alcance y fuente única de verdad

- Adaptador MCP stdio: [`cortex_memory_mcp.py`](../../01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py). Proyector y replay: [`cortex_memory_core.py`](../../01_KISH_ENGINE/babylon60/mcp/cortex_memory_core.py).
- Persistencia: `CortexPersistLedger` existente ([`cortex_persist_ledger.py`](../../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py)): SQLite WAL, `synchronous=FULL`, cadena SHA3-256 v2, triggers que impiden `UPDATE`/`DELETE`. El adaptador no crea tablas, cachés ni una segunda cadena; toda vista es una proyección pura de las filas `seq <= snapshot_seq`.
- Admisión: broker nativo Rust `McpCapabilityBroker` ([`capability.rs`](../../src/capability.rs)) a través de `_babylon60_mcp.McpBroker` ([`mcp_python.rs`](../../src/mcp_python.rs)). Cada llamada emite y valida un token ligado al resumen de los argumentos.
- Motivo de usar Python: el ledger duradero y su cadena de hashes existen solo en Python (`compute_cortex_hash`, `verify_integrity`); el broker Rust ya se expone a Python mediante PyO3 y lo carga el mismo patrón de `EffectDispatcher` ([`effect_dispatch.py`](../../01_KISH_ENGINE/babylon60/mcp/effect_dispatch.py)). En Rust habría que reimplementar la cadena SHA3-256 o abrir un puente nuevo hacia Python.
- Fuera de alcance: Memorix, Engram, embeddings, búsqueda semántica.

## 2. Autoridad (fallo cerrado)

| Elemento | Origen | Lo controla el modelo |
| --- | --- | --- |
| actor, proyecto, capacidades (`read`, `append`, `supersede`, `forget`), `policy_version`, validez | Vínculo JSON firmado con Ed25519 por la clave del operador, pasado como `--binding` y verificado con `--trust-pubkey` | No |
| Ruta del ledger y del broker | Argumentos de lanzamiento en el overlay | No |
| Contenido, consulta, `request_id`, clave estructurada, validez afirmada | Argumentos de herramienta | Sí |

- Sin vínculo válido (falta, firma alterada, clave distinta, fuera de plazo según el reloj local, permisos de archivo laxos) o sin broker nativo, el proceso termina con código 78 sin emitir ninguna trama.
- Los argumentos cuyo nombre coincide con `actor|project|token|capabilit|binding|agent|domain|policy|authority|role` se rechazan y se registra la denegación. `inputSchema` declara `additionalProperties: false`.
- `tools/list` solo publica las herramientas concedidas; las llamadas directas a herramientas no concedidas se deniegan.
- **El vínculo acredita el proceso o scope lanzado, no una sesión MCP concreta ni el modelo.** Los scopes de agente de DSH tienen transportes aislados; cada respuesta incluye `served_by` (`instance_id`, `pid`, `binding_id`) para demostrar qué instancia atendió cada llamada.
- DSH elimina de stdio las variables heredadas `/KEY|PASSWORD|SECRET|TOKEN/i` y `DSH_*`, y luego aplica `config.env`. El adaptador no necesita ningún secreto: el vínculo es una declaración firmada y la clave privada nunca llega al proceso hijo. No se asume expansión `${VAR}` ni herencia de descriptores.

### 2b. Perímetro de autoridad (supuestos de confianza)

La garantía demostrada cubre **las llamadas que llegan al adaptador por MCP**. Presupone que el agente o LLM **no** puede:

1. leer la clave privada del emisor ni ejecutar `issue-binding`;
2. sustituir la raíz de confianza (`--trust-pubkey`) ni los archivos de vínculo;
3. editar el launcher o la configuración (overlay de DSH, `cordis.patch.yml`, argumentos y `cwd`);
4. escribir en el ledger, en el código del adaptador o del proyector, en la librería del broker ni en el intérprete y sus dependencias.

**No es aislamiento** frente a un LLM con shell, ejecución de código o acceso de escritura al sistema de archivos bajo el mismo usuario del sistema operativo: ese agente podría saltarse el adaptador por completo. Cumplir estos supuestos (otro usuario, sandbox o permisos de archivo) corresponde al despliegue y queda fuera de este MVP. La comprobación de permisos de los archivos de vínculo solo rechaza configuraciones laxas evidentes; no establece por sí misma ese perímetro.

## 3. Escrituras: idempotencia y ACK

- Clave de idempotencia: `(proyecto, actor, request_id)`. Se comprueba bajo `BEGIN IMMEDIATE`. El campo `prior_body['projector']` selecciona el algoritmo de resumen (`/1` = SHA3-256 legacy, `/2` = BLAKE3 por defecto) para recalcular exclusivamente `{"tool": tool, "args": args}` antes de comparar con `prior_body['request_digest']`; `request_digest` no anida `binding_id`. Si coincide el digest se devuelve el resultado original (`replayed: true`); si difiere o la versión de proyector es desconocida, se deniega. Nuevas escrituras declaran `/2` (BLAKE3).
- `supersede` y `forget` exigen que el objetivo esté activo en el mismo proyecto.
- El ACK se escribe en stdout solo después de que `COMMIT` retorne. Una caída antes del commit no deja fila y el reintento hace commit. Una caída después del commit y antes del ACK deja la fila, y el reintento devuelve el mismo `memory_id`.
- **Durabilidad demostrada:** `SIGKILL` del proceso adaptador con WAL `synchronous=FULL`. Pérdida de corriente y caché volátil de la NVMe: **NO_VERIFICADO** (mismo alcance que `claim.cortex_persist_sqlite`).
- `supersede` concurrente sobre el mismo objetivo: la comprobación «objetivo activo» se hace dentro del mismo cerrojo de escritura. Uno de los dos hace commit y el otro recibe `target is not active`, así que nunca quedan dos sucesores activos.
- Concurrencia: varios procesos que comparten el ledger se serializan con el `BEGIN IMMEDIATE` existente, y la búsqueda de `request_id` se hace dentro del cerrojo de escritura. No se ha añadido ningún mecanismo nuevo.
- Entrega: al menos una vez **si el cliente reintenta con el mismo `request_id`**. No se promete entrega exactamente una vez.

## 4. Lecturas y receipts

- Cada `memory_read` calcula la vista y registra un evento `memory.read_receipt` en la misma transacción. El evento contiene la consulta, `snapshot_seq`, `snapshot_head_hash`, el orden (`recorded_seq_asc`), `projector_version` (`/2` por defecto), `policy_version`, `view_digest`, los ids entregados e `instance_id`.
- **Versionado explícito de proyector:**
  - `cortex-memory-projector/1`: SHA3-256 legacy (solo para lectura y verificación de registros históricos).
  - `cortex-memory-projector/2`: BLAKE3 (estándar canónico por defecto para nuevas escrituras, resúmenes y receipts).
  - Versiones no reconocidas son rechazadas con error.
- `delivery = recorded_before_send_unconfirmed`: el receipt prueba que la vista se **preparó y registró** antes del envío, no que el cliente la recibiera ni lo que el LLM razonó con ella. No hay acuse de recepción del cliente (pendiente).
- **Dos resúmenes distintos.** `view_digest` cubre la página entregada (filtrada y limitada a `limit` ≤ 100). `snapshot_state_digest` cubre el **estado completo** proyectado en `snapshot_seq`: todos los ítems, activos o no, con su estado de `supersede`/`forget`, incluyendo el objeto canónico con su `"projector": version`. No depende del límite de página. El replay compara ambos según el `projector_version` guardado en cada receipt y `head_state_digests` usa solo el segundo bajo `/2`. Esto corrige el defecto de v0.1, en el que `limit:1000` dejaba fuera del resumen los cambios desde el ítem activo 1001.
- Cada ítem lleva procedencia (`actor`, `binding_id`, `recorded_seq`, `entry_hash`) y `trust: untrusted_data`, conservando literalmente los hashes de fila originales.

## 4a. Replay (alcance: eventos y vistas de memoria)

`python -m babylon60.mcp.cortex_memory_core <ledger>` (`replay`):

- **Verifica:** la cadena de bloques del ledger con la regla del kernel (`verify_row_invariants`); cada `memory.read_receipt` recalculando su vista y su resumen de estado completo según el `projector_version` registrado en dicho receipt (`/1` con SHA3-256 o `/2` con BLAKE3; versiones desconocidas se marcan como mismatch); y el resumen de estado completo de la cabeza de cada proyecto bajo `/2`. Conserva literalmente `entry_hash` y `binding_id` de eventos previos sin reescribir la historia.
- **No verifica (pendiente):** el replay de decisiones de autorización. Los eventos `memory.decision` solo se cuentan (`decisions_recorded_not_replayed`). Tampoco se revalidan la firma del vínculo histórico, sus grants ni su `policy_version`: `cortex_taint` guarda un hash del vínculo, no el sobre firmado. No se registra la identidad de la librería del broker como evidencia verificable, ni la hora externa, ni el razonamiento del LLM.
- **Auditor de solo lectura:** nunca instancia `CortexPersistLedger`, porque su constructor crea directorios, inicializa tablas y migra el esquema. **Modo por defecto, válido para un ledger potencialmente activo:** `mode=ro` + `BEGIN` + una primera lectura que fija la instantánea. Ve los commits que solo están en `-wal` y no bloquea a los escritores. Que no exista `-wal` al abrir **no** se interpreta como prueba de que el ledger esté estático. El auditor no escribe eventos, esquema ni datos en la base, pero SQLite puede crear o actualizar los archivos auxiliares operativos `-wal`/`-shm` (https://www.sqlite.org/wal.html#read_only_databases). **`--static-copy`** (opción explícita, nunca automática): `immutable=1` (https://www.sqlite.org/uri.html#uriimmutable). Solo sirve para una copia que quien la usa garantiza estática; se rechaza si existe `-wal`, porque se ignorarían commits, y una comprobación del estado del archivo descarta el resultado si cambió. No se copia solo el `.db`, porque se perderían los commits que aún están en el WAL. Política:
  - ruta inexistente o que no es un archivo → código 2, sin veredicto y sin crear nada;
  - archivo que no es SQLite o no tiene el esquema `cortex_ledger` esperado → código 2;
  - ledger existente con el esquema esperado y 0 filas → **válido y vacío** (código 0, `events_verified: 0`);
  - cadena rota o algún receipt que no coincide → código 1.
- **Instantánea única:** toda la auditoría (esquema, cadena, receipts, proyecciones de cabeza y recuento de decisiones) se ejecuta dentro de **una sola transacción de lectura**. Al final se comprueba, dentro de esa transacción, que el máximo `seq` y el hash de cabeza no han cambiado. La salida incluye `audit_snapshot` (`seq`, `head_hash` y `mode`, que vale `read_txn` o `static_copy_immutable`).

## 4b. Validación de entrada

- Envoltura JSON-RPC: un frame que no sea un objeto (`[]`, lotes, escalares, `null`) devuelve `-32600`. JSON ilegible devuelve `-32700`. Si `jsonrpc` no es `"2.0"`, `method` no es texto o `id` no es string/int/null, devuelve `-32600`. Si `params` no es un objeto, o en `tools/call` `name` no es texto o `arguments` no es un objeto, devuelve `-32602`. Una herramienta desconocida devuelve `-32602`; un método desconocido, `-32601`. Los frames sin `id` no se responden.
- Argumentos de herramienta: se validan de forma estricta contra el mismo `inputSchema` que publica `tools/list` (`TOOL_SPECS`), sin coerción de tipos. `null` en un campo opcional equivale a ausente. Un número, una lista, un objeto o un booleano en un campo de texto, y un `limit` fuera de 1..100 o no entero, producen un resultado de herramienta con `isError: true` y `status: invalid`. Orden de admisión: nombres reservados → capacidad → esquema; una petición no concedida se deniega antes de examinar sus tipos.
- Fallos internos (cualquier excepción que no sea `ValueError` ni `Denied`) devuelven `-32603` y se registran en stderr. **Nunca se devuelven como éxito.** En todos los casos el servidor sigue atendiendo.

## 5. Contradicciones

- **Estructuradas (detectadas):** misma `(entity, attribute)`, valor distinto e intervalos `[valid_from, valid_to)` solapados. Ambas afirmaciones se conservan y se informan en `conflicts`. El tiempo de registro es `recorded_seq`; la validez la afirma quien escribe y no se verifica externamente.
- **Semánticas libres (no detectadas):** el texto no estructurado contradictorio se almacena sin marcar. No hay garantía.

## 6. `forget`

- Es una exclusión lógica: el ítem desaparece de las vistas calculadas en instantáneas posteriores al evento `memory.forget`. Requiere la capacidad `forget`.
- No es borrado: los bytes permanecen en el ledger, en el WAL, en las copias de seguridad y en cualquier caché del cliente o del modelo. No hay gestión verificable de claves, así que no se promete olvido criptográfico ni irreversibilidad.
- Replay histórico: una vista anterior al `forget` se reconstruye con el contenido olvidado incluido. Así se conserva la auditabilidad.

## 7. Inyección

Se mide el efecto, no se detecta texto. El texto recuperado no puede conceder capacidades, cambiar la política ni cruzar proyectos, porque esas magnitudes solo proceden del vínculo y del broker. No se usa ningún detector.

## 8. Evidencia y límites

| Escenario | Prueba | Resultado (2026-11-06) |
| --- | --- | --- |
| Lanzamiento con fallo cerrado (4 casos) | `tests/test_cortex_memory_mcp.py::test_fail_closed_launch` | pasa |
| A/B escritura y recuperación desde un proceso nuevo (iteración 2: protocolo 2025-11-25 renegociado; `snapshot_state_digest` presente) | `test_a_b_*` + `scripts/cortex_memory/sdk_ab_probe.mjs` (`@modelcontextprotocol/client` 2.4.0, protocolo negociado 2025-11-25) | pasa |
| C lanzamiento distinto de solo lectura | `test_c_*` | pasa |
| D contradicción estructurada | `test_d_*` | pasa |
| E efecto de la inyección | `test_e_*` | pasa |
| `forget` lógico | `test_forget_is_logical_exclusion` | pasa |
| G caídas con `SIGKILL` y reinicio | `test_g_*` | pasa |
| H aislamiento por proyecto | `test_h_*` | pasa |
| F replay determinista de eventos y vistas y detección de manipulación | `test_f_*` | pasa |
| R1 entrada malformada (17 argumentos, 21 frames) y fallo interno como `-32603` | `test_r1_*` | pasa |
| R2 resumen del estado completo con 1205 ítems activos; cambios en las posiciones 1101 y 1150 y al final | `test_r2_*` | pasa |
| R3 dos procesos, mismo ledger, 15 rondas por caso | `test_r3_*` | pasa |
| R3b dos `supersede` concurrentes sobre el mismo objetivo, 10 rondas | `test_r3b_*` | pasa |
| R5 auditoría con escritura concurrente: una escritura dirigida, confirmada entre la verificación de la cadena y las proyecciones, no aparece en el resultado; además, varias auditorías mientras otro proceso escribe 400 eventos, sin conexión retenida (la auditoría puede empezar con o sin `-wal`) | `test_r5_*` | pasa |
| R4 auditor de solo lectura: ruta inexistente, esquema ajeno, basura, ledger vacío; fuente sin cambios byte a byte | `test_r4_*` | pasa |
| DSH Real (`DeepSeek Harness 0.2.2-rc.1-arm64`): overlay Cordis (`--dump-config`, `dsh web --patch` y `dsh --profile headless --patch`), Sesión A (`mcp__cortex-memory__memory_append`, `pid=70620`, `instance_id=90165a7cf877ded7`) → Sesión B limpia (`mcp__cortex-memory__memory_read`, `pid=70641`, `instance_id=60c323fae0e09782`), `memory_supersede`, `memory_forget` y overlay `cortex-memory-readonly.cordis.yml` (`mcp__cortex-memory-ro__memory_read`, `actor=dsh-reader`) | `dsh` real + `cortex_memory_core` replay (`events_verified=6`, `chain_ok=true`) | pasa |

### 9. Protocolo de Ejecución Aislada de la Sonda Interop Node JS (`scripts/cortex_memory/sdk_ab_probe.mjs`)

La sonda interop utiliza el cliente oficial MCP en TypeScript (`@modelcontextprotocol/client@2.4.0`, fuente oficial: [First Client - MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk/blob/main/docs/get-started/first-client.md)).
Para preservar los lockfiles del repositorio (`package.json`, `uv.lock`) y cumplir con la resolución estricta de módulos ECMAScript (.mjs):
```bash
TMP_DIR=$(mktemp -d /tmp/cortex-mcp-probe.XXXXXX)
cd "$TMP_DIR"
npm init -y
npm install @modelcontextprotocol/client@2.4.0
cp "<repo>/scripts/cortex_memory/sdk_ab_probe.mjs" "$TMP_DIR/"
node "$TMP_DIR/sdk_ab_probe.mjs" <abs-python> <abs-repo> <abs-binding> <abs-pubkey> <abs-ledger> <abs-brokerlib>
rm -rf "$TMP_DIR"
```
*(Nota Node ESM: `NODE_PATH` no resuelve imports bare de paquetes en módulos ESM nativos `.mjs`; la ejecución requiere que la copia del script se encuentre en un directorio con acceso a `node_modules`)*.

**Verificado en DSH Real (2026-11-06):** carga y evaluación de expresiones `!!js` de `config/dsh/cortex-memory.cordis.yml` y `config/dsh/cortex-memory-readonly.cordis.yml` por Cordis; registro de las 4 herramientas `mcp__cortex-memory__memory_{append,forget,read,supersede}` en el modo escritor y exclusivamente `mcp__cortex-memory-ro__memory_read` en el modo solo lectura; pureza de `stdout` bajo transporte `@deepseek-ai/dsh-mcp-client` y recuperación entre sesiones independientes con `instance_id` y `pid` distintos sobre `~/.cortex-memory/ledger.db`. *(Nota: la ejecución se realizó con responder local `openai-completions` sobre `llm-pi-ai` debido a `HTTP 402 Insufficient Balance` en la cuenta remota `api.deepseek.com`).*

La cadena de hashes acredita consistencia respecto de una raíz de confianza (la cabeza conocida o una atestación externa). Por sí sola no prueba identidad ni hora externa: el `timestamp` es el reloj local y no forma parte del hash v2.

## 9. Pendiente

0. Replay de decisiones de autorización: guardar el sobre firmado del vínculo (o su referencia direccionada por contenido) y la identidad del broker, y revalidar firma, grants y `policy_version` por evento.
1. Acuse de recepción opcional desde el cliente para los receipts.
2. Anclar la cabeza del ledger a una raíz externa (Rekor/OTS ya existen en `anchor_to_rekor`).
3. Revocar vínculos antes de que caduquen (lista de revocación firmada).
4. Inyectar pérdida de corriente o probar en hardware.
