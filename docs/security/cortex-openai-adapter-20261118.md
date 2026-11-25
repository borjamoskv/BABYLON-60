# Adaptador OpenAI–CORTEX y prueba de presencia

Fecha: 2026-11-18. Base Git: `ab35f40f0d81f70cb95071c02e6bd0e98e7a4af8`.
Checkout compartido con cambios concurrentes, preservados.

## Contrato

Implementar una ruta ejecutable Responses → proyección Python → cliente MCP
oficial → servidor CORTEX stdio. La herramienta sintética empieza cada caso y
ruta con `nota="original"`. Comparar los argumentos recibidos y el estado final,
independientemente de la respuesta `ok`. Ningún cambio de dependencias, lockfiles,
controles de autorización o datos productivos. Las llamadas a OpenAI envían solo
la herramienta sintética y las tres intenciones, con `store: false` y sin reintentos.

## Implementación

El [adaptador](../../01_KISH_ENGINE/babylon60/mcp/cortex_openai_adapter.py):

- Descubre una lista explícita de herramientas mediante `tools/list`, incluidas
  sus páginas, y genera `sdk_source` con `render_mcp_tools_sdk_py`.
- Analiza las declaraciones del `Protocol` mediante AST; no ejecuta código del
  generador ni del modelo. Crea métodos `adapter.tools.<nombre>(**kwargs)` con la
  firma proyectada. `Signature.bind` conserva solo los argumentos suministrados;
  nunca aplica defaults, elimina null ni filtra valores por su valor de verdad.
- Conserva el JSON Schema original y `strict: false` en las funciones de OpenAI.
  Los nombres normalizados se traducen de vuelta a nombres MCP y propiedades
  originales. Rechaza colisiones y esquemas abiertos que la firma no expresa.
- Rechaza llamadas incompletas, nombres no permitidos, claves JSON duplicadas,
  constantes no JSON y argumentos desconocidos antes del envío.
- Reenvía únicamente los metadatos de autorización dados por la aplicación;
  `_meta` propuesto por el modelo no otorga autoridad. La validación y admisión
  de efectos siguen en el servidor. El adaptador no reintenta ni garantiza
  idempotencia: el consumidor debe respetar la política del servicio original.
- Devuelve `function_call_output` con `call_id` y conserva `caller` cuando existe.
  No ejecuta el runtime PTC alojado de OpenAI ni completa una conversación autónoma.

La conexión stdio usa MCP **2.3.0**, ya disponible en el entorno y lockfile; el
acceso HTTPS usa HTTPX **0.28.1**, dependencia existente. El SDK MCP pertenece al
entorno opcional `gemini`; no se añadieron dependencias. La credencial OpenAI
permanece en el proceso cliente, fuera del entorno del servidor de herramientas.

La interfaz soportada tiene `type: object` y `additionalProperties: false` en la
raíz, con propiedades declaradas. Otros esquemas fallan explícitamente; esta
iteración no afirma equivalencia para todo JSON Schema. La firma conserva su
ambigüedad descriptiva heredada sobre nullable/opcional; el servidor conserva el
contrato original. Como OpenAI recibe también el esquema, no se afirma ahorro de
tokens mediante este adaptador.

Fuentes consultadas: [function calling de OpenAI](https://developers.openai.com/api/docs/guides/function-calling)
y [MCP Python SDK 2.3.0](https://github.com/modelcontextprotocol/python-sdk/tree/v2.3.0).

## Pruebas por stdio

La [herramienta de prueba](../../tests/fixtures/cortex_openai_note_server.py) es un
subproceso real que hereda inicialización, framing y bucle stdio de CORTEX.
Registra únicamente `update_note`; no abre ledgers ni registra herramientas
productivas protegidas. Reutiliza `jsonschema` instalado para validar entradas.
Después de cada llamada escribe argumentos, estado y PID en un archivo temporal
que el proceso padre lee; la respuesta MCP es siempre `ok` para los casos válidos.

Los [tests del adaptador](../../tests/test_cortex_openai_adapter.py) usan el cliente
MCP oficial y pipes reales. Los sobres Responses de esos tests son fixtures;
la prueba remota se ejecuta por separado.

| Intención | Argumentos recibidos, ambas rutas locales | Estado final, ambas rutas locales |
| --- | --- | --- |
| Conservar | `{}` | `{"nota": "original"}` |
| Borrar | `{"nota": null}` | `{"nota": null}` |
| Vaciar | `{"nota": ""}` | `{"nota": ""}` |

También se comprueban rechazo sin efecto, metadatos, allowlist, conservación del
esquema, colisiones de nombres y errores de autenticación sin fuga de secretos.

## Prueba remota y diagnóstico inicial

El [probe reproducible](../../scripts/cortex_memory/probe_openai_presence.py) hace
hasta tres solicitudes Responses reales, sin reintentos, con nuevas instancias
del servidor por caso y ruta. Usa los [vectores originales](../../tests/fixtures/cortex_ptc_presence.json).
La aplicación ejecuta la llamada devuelta por OpenAI; las expectativas no se
inyectan como argumentos en esa ruta. El primer caso directo llegó como `{}` y
conservó `"original"`. La solicitud remota terminó en `ExceptionGroup` antes de
obtener una llamada de herramienta; el informe inicial no conservó la causa hoja.

Se preserva ese [intento fallido](evidence/cortex-openai-adapter-live-20261118.json).
La [comprobación de autenticación independiente](evidence/cortex-openai-adapter-auth-20261118.json)
devolvió HTTP **401**, código **`invalid_api_key`**, usando la credencial configurada.
No se volvió a ejecutar el POST con esa credencial. El probe se mejoró para
desenvolver estos errores y registrar solo tipo/código HTTP, sin mensajes ni claves.

## Verificación remota completada

Con autorización explícita se creó una clave temporal en Default project,
restringida a Responses Write y con caducidad de un día. La
[ejecución real](evidence/cortex-openai-adapter-live-validated-20261118.json)
comenzó el 18 de noviembre de 2026 a las 17:35 CET (16:35 UTC) y completó
exactamente tres solicitudes, sin reintentos. OpenAI devolvió el modelo
`gpt-4.1-mini-2025-04-14`; el uso agregado fue de 708 tokens de entrada y 14 de
salida. No se conservaron secretos ni contenido de razonamiento.

| Intención | Argumentos recibidos por MCP directo y OpenAI | Estado final en ambas rutas | Resultado |
| --- | --- | --- | --- |
| Conservar | `{}` | `{"nota": "original"}` | PASS |
| Borrar | `{"nota": null}` | `{"nota": null}` | PASS |
| Vaciar | `{"nota": ""}` | `{"nota": ""}` | PASS |

Los seis procesos partieron de `nota="original"` y no recibieron la credencial
OpenAI. Los argumentos enviados por OpenAI atravesaron el adaptador, la firma
proyectada y el transporte MCP stdio antes de observarse en el servidor. La
comparación usó los argumentos registrados y el estado, además de la respuesta
de éxito. No se cambió el generador al no observar divergencia en estos vectores.

La clave `CORTEX Responses test authorized 2026-11-18` se revocó inmediatamente
después de las pruebas; la interfaz de OpenAI confirmó `Revoked`. Su secreto
solo se mantuvo en memoria durante la ejecución y no se copió al portapapeles.
El [registro de ejecución y revocación](evidence/cortex-openai-adapter-key-lifecycle-20261118.json)
conserva únicamente metadatos sin secretos y hashes de las fuentes leídas después
de la ejecución. El HEAD observado entonces fue
`bba00a929699dad6389b7cd4bc2e7320071a4853`; el checkout compartido avanzó desde la
base inicial indicada al comienzo del informe.

El resultado verifica estos tres vectores en esta ejecución. No demuestra
equivalencia para todo JSON Schema ni ahorro de tokens: esta ruta también
proporciona el esquema original a OpenAI.

## Reproducción y aceptación

```sh
uv run --locked pytest tests/test_cortex_openai_adapter.py tests/test_cortex_ptc_presence.py tests/test_cortex_ptc_ralph.py -q
uv run --locked ruff check 01_KISH_ENGINE/babylon60/mcp/cortex_openai_adapter.py tests/fixtures/cortex_openai_note_server.py tests/test_cortex_openai_adapter.py scripts/cortex_memory/probe_openai_presence.py
uv run --locked mypy --follow-imports=silent 01_KISH_ENGINE/babylon60/mcp/cortex_openai_adapter.py tests/fixtures/cortex_openai_note_server.py tests/test_cortex_openai_adapter.py scripts/cortex_memory/probe_openai_presence.py
```

Con una credencial válida configurada fuera del chat, el comando remoto es:

```sh
uv run --locked python scripts/cortex_memory/probe_openai_presence.py --live --model gpt-4.1-mini --output /tmp/cortex-openai-presence-new-run.json
```

El destino nuevo conserva el intento anterior. El archivo registra respuesta/modelo
devueltos por OpenAI, uso de tokens, argumentos y observaciones; excluye claves y
contenido de razonamiento. No hay ejecución automática en CI ni gasto sin `--live`.

Antes del commit se repitieron los 52 tests sobre una copia temporal del HEAD
`bba00a929699dad6389b7cd4bc2e7320071a4853` más los 12 archivos de esta tarea.
Los imports del adaptador, servidor y proyección se comprobaron dentro de esa
copia: los 52 tests pasaron sin los cambios pendientes de otras sesiones. Esta
comprobación fue local y no repitió solicitudes a OpenAI.

| id | description | status | evidence |
| --- | --- | --- | --- |
| STDIO | Tres intenciones por MCP directo y adaptador productivo | passed | Tests con cliente MCP oficial y procesos distintos |
| CONTRACT | Rechazos, esquema, nombres y metadatos | passed | Tests dirigidos del adaptador |
| OPENAI | Tres intenciones desde respuestas remotas reales | passed | Tres solicitudes reales; argumentos y estados idénticos al MCP directo |
| KEY | Credencial temporal autorizada y retirada | passed | Responses Write, caducidad de un día, revocación confirmada en OpenAI |
| CHECKS | Suite, Ruff, mypy y controles documentales finales | passed | 52 tests aprobados también sobre HEAD más archivos propios; Ruff y mypy en 5 archivos; contratos, presupuesto y topología PASS; 9 enlaces locales válidos |

Los controles documentales cubren solo el workspace; se omiten configuración
global y telemetría de ghost listeners. No certifican mediación de efectos reales.
