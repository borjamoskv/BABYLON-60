# Firma portable MOSKV-1

La firma usa los mismos datos y fuentes en cualquier entorno. El cliente decide
qué puede mostrar: Panel MCP Apps, HTML autónomo, Markdown o texto. El contrato no
depende de nombres de modelos ni de una marca de IDE. No modifica aplicaciones.

La salida habitual es texto breve con resultado, evidencia y límites relevantes.
Usar firma a petición o cuando aporta trazabilidad a una auditoría o cambio
relevante; no se exige en cada respuesta. Esta guía describe cómo incluirla
cuando corresponde, sin convertir la disponibilidad del renderizador en una
obligación de usarlo.

## Clientes conectados por MCP

Los servidores Kernel y Cortex publican `babylon_signature_render`, el esquema
`babylon://signature/schema` y la interfaz `ui://babylon60/signature`.

Las configuraciones del proyecto para Claude Code, VS Code, Gemini y Codex ya
apuntan a `scripts/c5_cli/launch_kernel_mcp.py`. Al recargar esa conexión reciben
la herramienta, instrucciones breves y acceso al contrato de presentación como
recurso. Para activar preferencias globales en Codex con el paquete instalado,
consulta la [guía de primera conversación](guide_codex_first_use.md). En otro cliente MCP, registrar
`python3` con la ruta absoluta a ese lanzador; no es necesario copiar el diseño.
La sintaxis concreta del archivo de configuración pertenece a cada cliente.
Estos archivos de proyecto no configuran Claude web ni Antigravity globalmente.

El agente invoca la herramienta con `payload` y `format="auto"`. El servidor
comprueba `capabilities.extensions["io.modelcontextprotocol/ui"].mimeTypes` en la
conexión. Solo selecciona `ui` si aparece `text/html;profile=mcp-app`; de lo
contrario elige Markdown. Nunca infiere soporte por el nombre del cliente.

El descriptor vincula el recurso mediante `_meta.ui.resourceUri`. La plantilla
HTML es estática, sin red, y recibe los datos actuales en `structuredContent`.
Se conserva contenido textual accesible para clientes sin interfaz. El agente
no debe repetirlo en la respuesta si el anfitrión ya muestra el Panel.

El anfitrión controla el contenedor, la colocación y si muestra también el
resultado de la herramienta. No se garantiza una interfaz idéntica ni que quede
al pie de la respuesta en todos los clientes. El soporte de un producto no prueba
el de una sesión concreta. Contrato: [MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview).

## Entornos sin MCP

Con el paquete Babylon instalado:

```sh
babylon60 signature --schema
babylon60 signature --input datos.json --format html --output firma.html
babylon60 signature --input datos.json --format markdown
babylon60 signature --input datos.json --format text
babylon60 signature --input datos.json --format json
```

También puede ejecutarse `python3 -m babylon60.cli.main_dispatcher signature`.
La entrada `-` lee JSON desde stdin; la salida omitida o `-` usa stdout.
`auto` en CLI selecciona texto sin depender de colores ANSI. HTML genera un
documento autónomo que puede abrirse en un navegador, sin conexión ni bibliotecas
externas. Los archivos de salida se crean con permisos 0600 y nunca sobrescriben
una firma anterior. No añade firmas a JSON ni al transporte MCP.

## Datos reales y una sola presentación

La fecha `observed_at` es obligatoria e incluye zona horaria. `fields` y `sources`
usan las seis etiquetas canónicas del esquema. Los campos ausentes permanecen
desconocidos; un dato expuesto o medido exige su fuente. No se deduce la identidad
del modelo de la configuración predeterminada ni se reutiliza una captura antigua.

El esquema de datos es versión 1. El Panel adaptativo es versión 2: siempre muestra
MOSKV-1, modelo, fuente y fecha; oculta esfuerzo o metrología no disponibles. Texto
y Markdown conservan las seis etiquetas para compatibilidad. Modelo, modo, térmica
e índice léxico no se miden automáticamente; el agente aporta observaciones de ese
turno. Validar estructura y fuentes declaradas no certifica que sean verdaderas.

La firma es una observación, no telemetría en vivo ni atestación criptográfica.
El índice léxico, cuando se aporta, no mide energía física ni calidad. Un estado
térmico del sistema no es una temperatura.

### Ejemplo textual heredado

Este ejemplo conserva las seis etiquetas de compatibilidad; no obliga a firmar
respuestas ni documentos. Los datos reales requieren fuente y fecha vigentes.
El control de documentos y el control de firmas son independientes; `--response`
valida un borrador que incluya firma, no exige firmar una respuesta sencilla.

```text
[ LLM ]: No expuesto
[ MODO COGNITIVO ]: No expuesto
[ TOPOLOGÍA ACTIVA ]: MOSKV-1
[ RÉGIMEN TÉRMICO ]: No medido
[ EXERGÍA INFORMATIVA ]: No medida
[ MUTACIÓN CAUSAL ]: Ninguna
```

El nombre visible de la medición es «Índice léxico». `EXERGÍA INFORMATIVA` es la
etiqueta heredada del esquema y de las seis líneas de texto; se conserva por
compatibilidad. No usarla como puntuación de calidad. El [método y su alcance](guide_agent_workflow.md#indice-lexico)
se documentan aparte y la medición sigue siendo opcional.

En cada respuesta que incluya firma se elige una sola presentación. Las directivas de
visualización de Codex son propias de ese cliente; los otros sistemas usan el
contrato MCP o la salida portable. Los avisos de progreso y las salidas de máquina
no reciben un pie añadido.
