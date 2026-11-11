# BABYLON-60 — Trabajo con agentes

La fuente canónica es [.babylon60rules](.babylon60rules). Aplicar también las instrucciones de workspace suministradas por el anfitrión; no asumir que una referencia con `$BABYLON_HOME` se ha cargado. Los contratos técnicos se consultan según el cambio, sin incorporarlos completos a cada tarea.

## Contrato de tarea

Antes de editar, fijar brevemente resultado esperado, rutas, restricciones aplicables y comprobación de aceptación. Conservar decisiones y autorizaciones vigentes de la sesión; resolver elecciones reversibles dentro de ese alcance. Plantilla, escenarios y evaluación: [guía de trabajo](docs/03_guides/guide_agent_workflow.md).

## Ejecución

- Revisar rama y estado; preservar cambios ajenos. No modificar dependencias ni lockfiles sobre un árbol sucio.
- Para descubrir código, preferir `search_graph`, `trace_path`, `get_code_snippet` y `query_graph`; indexar primero si procede. Si el MCP no está disponible o no basta, usar búsquedas acotadas. Para literales, configuración y documentos, usar `rg` o `git grep -n`.
- Limitar la exploración a las rutas y contratos afectados. Evitar árboles globales, lecturas completas de más de 200 líneas y relecturas sin nueva necesidad.
- Explorar antes de preguntar por hechos disponibles. Pedir aclaración solo por un dato o decisión que condicione el resultado y no pueda resolverse con el contexto autorizado. No pedir de nuevo un permiso ya concedido para el mismo alcance.
- Preparar el resultado concreto y revisable antes de solicitar una autorización adicional necesaria para ejecutarlo o publicarlo. Ante un bloqueo, detener solo la operación afectada, explicar la causa y continuar el trabajo independiente; no eludir controles ni convertir el silencio en autorización.
- Tras dos fallos equivalentes, diagnosticar esa vía antes de reintentar. Los protocolos sin reintento se respetan desde el primer fallo.
- Conservar resultados y evidencia reproducible; no almacenar deliberaciones internas del LLM. Distinguir observaciones, hipótesis y obligaciones.

## Contratos por cambio

| Ámbito afectado | Lectura requerida antes de editar |
| --- | --- |
| Memoria, IPC, biometría, persistencia, Rust o aislamiento | [Layer-0 (EL0, user-space)](docs/03_guides/agent_contracts.md#ring-0) |
| Lean, Z3, PoC, concurrencia o garantías formales | [Ring-1](docs/03_guides/agent_contracts.md#ring-1) |
| CI, Git, dependencias, ledger, datasets o licencias | [Ring-2](docs/03_guides/agent_contracts.md#ring-2) |
| UI, voz, documentación, rutas o salida | [Ring-3](docs/03_guides/agent_contracts.md#ring-3) |

## Condición de cierre

Ejecutar comprobaciones proporcionales al cambio y leer su resultado antes de declarar éxito. Rust: `cargo check -q --locked` o test dirigido con `--locked`. Python: `uv run --locked pytest <ruta> -q` y Ruff sobre archivos modificados. Una edición documental requiere enlaces y controles documentales; no activa por sí sola compilación Rust, biometría, PoC ni estrés. Consultar CI cuando se evalúe su estado o una revisión concreta.

Comprobar documentos y enlaces con `python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only --public-projection`, el presupuesto con `python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners` y la topología con `python3 scripts/guards/verify_active_topology.py`. El alcance local excluye configuración global y declara la telemetría omitida. Antes de un commit autorizado, validar también la topología con `--staged`; este modo lee el índice Git. Si la respuesta incluye firma, validar su borrador con `--response <ruta>`.

Informar qué cambió, qué se comprobó y qué falló o queda pendiente. No certificar runtime mediante documentación ni publicar por inferencia de una autorización local. Commits: `[AX-<Num>] <DOMINIO>: <Descripción causal>`; merge explícito antes de push a `origin/main`.

## Modelo y salida

Identificar MOSKV-1 y el modelo solo con la fuente vigente del entorno. Conservar la incertidumbre si faltan variante o esfuerzo. Recomendar un selector según coste, tiempo y retrabajo observados; no declarar un óptimo ni detener el trabajo por una clasificación de tareas.

La salida habitual es texto breve con resultado y evidencia. El [contrato de presentación](01_KISH_ENGINE/babylon60/presentation.md) y la [firma portable](docs/03_guides/guide_portable_signature.md) se consultan cuando se necesita presentación detallada. El Panel v2 se usa a petición o cuando aporta trazabilidad a una auditoría o cambio relevante; no se exige en cada conversación. No añadir firmas a progreso, JSON ni transporte MCP.

Los documentos de instrucciones no necesitan contener una firma. Su ejemplo heredado se conserva únicamente en la guía portable.
