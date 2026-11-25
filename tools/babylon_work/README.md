# Babylon Work · prototipo local 0.2

Espacio de trabajo con encargos, documentos Markdown, decisiones y recuperación
entre sesiones. La interfaz usa un servidor local autenticado y una base SQLite
independiente. Ahora puede generar documentos con modelos reales y preparar
comprobaciones mediadas por el broker de BABYLON-60. No aplica código generado
por el modelo ni ofrece una terminal libre.

## Arranque

Desde la raíz de BABYLON-60:

```bash
uv run --locked python -m tools.babylon_work.server
```

Abre la dirección que muestra el terminal e introduce su clave local. La clave
cambia al reiniciar el servidor; no es una credencial de un proveedor de IA.
La interfaz la conserva solo durante la sesión del navegador.

Opciones: `--port 8788` y `--state /ruta/absoluta/workspace.sqlite`.
El estado por defecto se guarda en `target/babylon-work/workspace.sqlite`, fuera
de las fuentes y de los ledgers productivos. Detén el servidor con `Ctrl+C`.

## Recorrido

1. Crea un encargo con título, tipo y objetivo.
2. Pulsa «Trabajar con IA», elige un modelo detectado y da una instrucción.
3. Edita el Markdown y guarda con el botón o `⌘S` / `Ctrl+S`.
4. Añade decisiones en Contexto; consulta los eventos en Actividad.
5. Pausa, recarga o reinicia el servidor y recupera el encargo.
6. Exporta el documento o confirma su revisión para marcarlo terminado.

En «Ejecución» puedes seguir los trabajos, consultar errores y preparar una
comprobación del catálogo. «Preparar extractos sin IA» conserva el modo
determinista de la primera versión.

## Modelos reales

Ollama debe estar iniciado en `127.0.0.1:11434`, con modelos ya instalados. El
servidor consulta su catálogo y sus capacidades; no descarga modelos ni inicia
Ollama automáticamente. Solo admite modelos con capacidad de generación.
La petición y los extractos se envían al servicio local.

La API de OpenAI utiliza `OPENAI_API_KEY` del entorno del servidor. La clave no
se entrega al navegador. Un catálogo accesible indica disponibilidad declarada;
la compatibilidad de generación se comprueba al realizar el trabajo. Un 401
queda visible como credencial rechazada, sin cambiar de proveedor ni reintentar.
Elegir OpenAI envía el contexto seleccionado a su API. El adaptador solicita
`store=false`; esto no constituye una garantía sobre todas las políticas de
retención del proveedor.

Se contrastaron los formatos con la documentación de
[Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md) y
[OpenAI](https://developers.openai.com/api/docs/guides/text).
Se conserva únicamente la respuesta final, no los campos de razonamiento.

## Comprobaciones protegidas

La biblioteca existente `target/debug/libbabylon60.dylib` se usa si está
disponible. Puedes seleccionar otra mediante `--capability-library`, desde el
arranque del servidor. No se aceptan bibliotecas ni comandos desde el navegador.

El catálogo inicial permite ejecutar las pruebas del espacio de trabajo o
comprobar la sintaxis JavaScript. Antes de ejecutar se conserva una solicitud
exacta con comando, directorio, revisión, hash del documento, fuentes y binario.
El modelo no puede ampliarla ni conceder su propia autorización.

La firma reutiliza el [verificador de Babylon](../../01_KISH_ENGINE/babylon60/verification/verification_gate.py)
y su [adaptador de atestación](../../01_KISH_ENGINE/babylon60/verification/hardware_attestation.py).
El [despachador](../../01_KISH_ENGINE/babylon60/mcp/effect_dispatch.py) usa el
broker Rust y consume la autorización antes del efecto. No se sustituye por
un booleano de la interfaz o una fila de aprobación sin firma.

El operador debe provisionar `BABYLON_ENCLAVE_PINNED_PUBKEY` por un canal de
confianza antes de arrancar el servidor, según la
[guía de autorización](../../docs/03_guides/guide_signed_authorization.md).
No se infiere esa identidad copiando la clave de una respuesta del helper.
Sin clave válida no se intenta la biometría ni se ejecuta el comando.

Cada solicitud admite un intento de firma. Un rechazo, error o resultado
ambiguo queda registrado sin reintento automático. Tras reiniciar el servidor,
los trabajos pendientes quedan interrumpidos y las solicitudes deben prepararse
de nuevo. Una firma previa no se traslada a la sesión nueva.

Las comprobaciones ejecutan código de repositorio confiable con permisos del
anfitrión. La mediación de autorización no constituye un sandbox del sistema
operativo. El catálogo no permite ejecutar código o shell generado por la IA.

El editor conserva los cambios sin guardar ante errores del servidor. Si otra
ventana ha modificado la misma revisión, el servidor rechaza la escritura con
409. Conserva tu texto antes de recargar; no hay fusión automática.

## Base reutilizada y referencia de diseño

- [Conexión SQLite de Babylon](../../01_KISH_ENGINE/babylon60/database/core.py):
  `connect_sync` con WAL, `synchronous=FULL`, claves foráneas y plazo de espera.
- [Presentación del proyecto](../../README.md),
  [arquitectura](../../docs/01_spec/spec_architecture.md),
  [modelo de seguridad](../../docs/01_spec/spec_security_model.md) y
  [trabajo con agentes](../../docs/03_guides/guide_agent_workflow.md): catálogo
  cerrado de fuentes reales. La apertura por descriptores rechaza symlinks en
  todos los componentes de cada ruta.
- Ingeniería inversa local: `WORK-REVERSE v2` y expediente C5-REA de
  `com.openai.codex`, build 21828. Se adoptan los patrones de separación entre
  interfaz y ejecución, persistencia explícita y documentos junto al trabajo.
  La implementación es propia; no incorpora código ni recursos del cliente
  analizado. Su expediente deja pendiente la fase dinámica.

## Contrato del prototipo

Resultado: un recorrido local de creación, preparación, edición, guardado,
recuperación y exportación de documentos con fuentes identificables.

Rutas de implementación: `tools/babylon_work/`, pruebas del prototipo y la
clasificación `work_run_checks` en el despachador. No se cambian dependencias,
lockfiles ni fuentes Rust. Estado y evidencia en `target/` o temporales de tests.

Aceptación: persistencia tras recrear el servidor, escritura concurrente
rechazada, fuente desconocida o con symlink rechazada, API sin autorización o
desde otro origen rechazada y recorrido de edición comprobado en navegador.

## Límites

La IA recibe extractos acotados, las decisiones y el borrador guardado, no todo
el repositorio. Su respuesta es una propuesta pendiente de revisión. Los trabajos
se ejecutan en segundo plano y se conservan tras recargar. Si la revisión cambia
durante la inferencia, el resultado se guarda por separado sin sobrescribirla.
Una respuesta parcial tampoco sustituye al borrador anterior.
Las fuentes se seleccionan por secciones y términos del encargo. En tareas de
instalación, un filtro literal señala comandos que no aparecen en los extractos
y conserva ese resultado para revisión sin aplicarlo automáticamente. Este
filtro no comprueba todas las afirmaciones, opciones de CLI o requisitos.
«Terminado» en un trabajo de IA significa que entregó su respuesta; el documento
sigue pendiente de revisión y no se certifica su exactitud.

El control del escritorio y la ejecución de comandos arbitrarios no se integran.
La biometría requiere el aprovisionamiento y el helper reales del equipo; los
tests con claves software no acreditan Secure Enclave. El historial de SQLite no se
declara WORM, consenso BFT o atestación criptográfica. BLAKE3 identifica el
contenido de las fuentes; no demuestra que sus afirmaciones sean verdaderas.

El servidor escucha únicamente en `127.0.0.1`, verifica Host y Origin, exige
una clave efímera para las APIs y aplica una CSP sin recursos de terceros.
Es un prototipo para uso local, no un servicio publicado de producción.

## Verificación

```bash
uv run --locked pytest tests/test_babylon_work.py -q
BABYLON60_TEST_CAPABILITY_LIBRARY="$PWD/target/debug/libbabylon60.dylib" uv run --locked pytest tests/test_babylon_work_runtime.py tests/test_fl_mcp01_dispatch.py -q -rs
uv run --locked ruff check tools/babylon_work tests/test_babylon_work.py tests/test_babylon_work_runtime.py
uv run --locked mypy tools/babylon_work --follow-imports=skip
node --check tools/babylon_work/work.js
node --check tools/babylon_work/runtime-ui.js
```

Los controles documentales del repositorio se ejecutan por separado según
[AGENTS.md](../../AGENTS.md#condición-de-cierre). Estas pruebas no certifican
propiedades del kernel ni del cliente objeto de ingeniería inversa.
