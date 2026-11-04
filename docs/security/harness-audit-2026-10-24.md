# BABYLON-60: clasificación del harness y verificación pública

Fecha de revisión: 24 de octubre de 2026, Europe/Madrid.

**Conclusión:** BABYLON-60 combina memoria, autorización de efectos, evidencia y
orquestación LLM. La oferta de la web se integra con agentes existentes; el código
también contiene un orquestador propio. «No es un harness» es demasiado categórico
sin definir el término y el componente. La descripción más precisa con esta
evidencia es **capa de memoria y control para agentes, con orquestación LLM propia**.

El espejo público supera la verificación de sus 16 artefactos y AX0 compila con
Lean 4.34.0-rc2. Esto acredita integridad del paquete y una propiedad del modelo
formal. No certifica la seguridad del ejecutor ni una release autenticada.

## Alcance y aceptación

La petición adjunta aceptaba ejecutar el verificador público y escribir una
comparación con hooks de Claude Code, Docker MCP Gateway, permisos de Cursor y
Git con aislamiento. Se revisaron fuentes primarias, código y artefactos; se
ejecutaron el verificador, Lean y dos controles negativos en un clon temporal.
La aceptación exige resultados leídos, fuentes identificadas y límites explícitos.

La revisión inicial creó este informe y su [evidencia](evidence/harness-audit-2026-10-24/source-provenance.json).
El árbol local tenía 13 rutas modificadas o nuevas antes de empezar; se preservan.
Durante la revisión inicial no se ejecutó la suite de runtime, ni inferencia remota,
ni despliegue, commit o push.
Las capacidades de terceros se comparan según su documentación, sin ensayos aquí.
La continuación solicitada revisa los validadores de documentos y presupuesto,
añade regresiones CLI y actualiza el cierre documentado al final del informe.

## Qué significa harness en esta comparación

Se usa *agent harness* para el entorno que organiza la ejecución del agente:
invocación del modelo, contexto, herramientas, observaciones y continuidad del
trabajo. La implementación puede repartir esas funciones entre procesos.
Memoria y políticas pueden formar parte de ese entorno; no tienen que quedar
fuera de la categoría por definición. Es una definición operativa, no una norma
universal. [Referencia de Anthropic](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents).

| Componente observado | Evidencia | Clasificación acotada |
| --- | --- | --- |
| CORTEX / Guard / NEMESIS de la web | Integración anunciada con agentes y herramientas existentes | Memoria, autorización y evidencia complementarias al agente |
| `SwarmOrchestrator.execute_dag` | Construye mensajes, limita concurrencia, llama al cliente y recoge resultados | Orquestador de tareas LLM; componente de harness |
| `RobustLLMClient.call` | Construye peticiones al proveedor, interpreta respuestas y gestiona reintentos | Invocación real del modelo cuando está configurado |
| Espejo `babylon60-verification` | Verificador de archivos y proyecto Lean mínimo | Paquete de verificación, no ejecutor de agentes |

La [web](https://babylon60.com/) respalda la primera fila. Las dos siguientes se
observan tanto en el [código público fijado](https://github.com/borjamoskv/BABYLON-60/blob/c54d3453ec538597ef9e66e48011d676864f0421/02_EDIN_SWARMS/agents_archi/orchestrator/swarm.py#L281)
como en el [árbol local](../../02_EDIN_SWARMS/agents_archi/orchestrator/swarm.py).
En la revisión pública, `execute_dag` empieza en la línea 353 y la llamada al
cliente está en la 380. Ese método hace una llamada por tarea y agrega respuestas;
no demuestra por sí solo un bucle general de herramientas y observaciones.
El cliente también tiene una respuesta `AIR-GAP MOCK` sin credenciales remotas:
ejecutar esa rama no demostraría inferencia real. No se invocó ninguna de las dos.

## Tres revisiones que no deben confundirse

| Superficie | Revisión observada | Interpretación |
| --- | --- | --- |
| Repositorio público principal | `c54d3453ec538597ef9e66e48011d676864f0421` | GitHub lo muestra como público; contiene código, tests y EDIN |
| Espejo de verificación | `a4657d9fcfeff49791ae75486cd03f3509a2c1f7` | Es el clon sobre el que se ejecutó esta revisión |
| Workspace local | `a620e383d695e82d14b57066967194b8c8a3022b` más cambios | Rama `codex/integration-review-20261023`; no equivale a la publicación |

El espejo declara origen `a25ff274308fbe74c10be6b0fc7513da93b78887`, 143 rutas
sucias y una ejecución de claims con sufijo `+dirty:cc512bce910ae7bd`.
Su `tracked_source_matches` es `false`: los resultados registrados no atestan
todos los bytes del árbol utilizado para generar la publicación.
Véanse el [manifiesto conservado](evidence/harness-audit-2026-10-24/mirror-manifest.json)
y la [documentación pública](https://babylon60.com/documentacion/).

La web etiqueta el repositorio central como privado bajo solicitud/NDA, pero
la [página pública de GitHub](https://github.com/borjamoskv/BABYLON-60) y su API
devuelven visibilidad pública. Se pudo leer el archivo de EDIN a un SHA fijado.
Esto refuta la afirmación de que ese código es necesariamente privado. No implica
que el repositorio público contenga la revisión exacta del snapshot posterior.

## Resultados reproducidos

| Comprobación | Resultado observado | Qué permite concluir |
| --- | --- | --- |
| `python3 verify.py` | Salida 0; 16 artefactos coherentes | Integridad contra el manifiesto empaquetado y vínculo CLAIMS/sitrep |
| Verificador con SHA-256 publicado | Salida 0 | Coherencia con el digest de la misma publicación; no identidad independiente |
| `lake build` | Salida 0; AX0 construido; 3 jobs | Lean acepta el modelo con la versión fijada |
| Pin SHA-256 deliberadamente incorrecto | Salida 1 | Se rechaza el manifiesto que no coincide con el pin |
| Un comentario añadido a una copia de `CLAIMS.toml` | Salida 1 | Se detecta la alteración de ese artefacto |

Las salidas completas están en [verificación](evidence/harness-audit-2026-10-24/verification-results.json)
y [controles negativos](evidence/harness-audit-2026-10-24/negative-controls.json).
No se instalaron dependencias: Lean 4.34.0-rc2 ya estaba disponible; Lake generó
su manifiesto y productos de compilación únicamente en el clon temporal.

El [teorema AX0](https://github.com/borjamoskv/babylon60-verification/blob/a4657d9fcfeff49791ae75486cd03f3509a2c1f7/proof/lean/AX0.lean#L145)
demuestra `validateTrace trace .Proposed = true → countDispatches trace ≤ 1`.
El modelo tiene cinco estados y cuatro eventos; no representa valores de nonce,
firmas, archivos, persistencia ni concurrencia del ejecutor. La interpretación
como protección de un nonce requiere una correspondencia adicional con el
runtime. El teorema universal declara dependencia de `propext`; los ejemplos
concretos comprobados declaran ausencia de axiomas. Esto no invalida la prueba,
pero no debe describirse todo el resultado universal como simple reflexión `rfl`.

## Correcciones al análisis pegado

| Afirmación o inferencia | Dictamen tras la revisión |
| --- | --- |
| BABYLON no llama al modelo | Incorrecto para todo el proyecto: EDIN contiene la invocación al proveedor |
| El mini-harness es interno y privado | Incorrecto como afirmación actual absoluta: el archivo de orquestación es público |
| No existe verificación independiente | Excesivo: integridad y AX0 se reproducen sin el monorepo local; no certifican runtime |
| El informe NEMESIS tiene una firma falsa | El campo histórico tiene 16 bytes y coincide con el prefijo del hash; no es una firma Ed25519 verificable. El dato no demuestra intención de engañar ni invalida por extensión toda firma del sistema |
| La release está sin firmar | Confirmado para el `RELEASE_MANIFEST.json` del espejo: firma, algoritmo y clave pública son `null` |
| El crash test es simulado | Confirmado para el informe histórico `SIGKILL_SIMULATED`; no describe todas las suites posteriores de claims |
| Nueve auditadas y cero fallos son cifras incompatibles | No: el sitrep registra 9 `verified`, 19 `partial` y cero `failed_claims`; son categorías distintas |
| La prueba formal es solo una promesa | Excesivo: AX0 compila. La correspondencia con el runtime queda fuera de esta prueba |
| Seis invariantes están STALE | Es la clasificación publicada del conjunto histórico; no equivale a seis contraejemplos reproducidos aquí |

Los hallazgos de los archivos se conservan en [datos derivados](evidence/harness-audit-2026-10-24/artifact-findings.json).
Los informes históricos registran 19 × 100 intentos y 250 iteraciones simuladas;
se trata de resultados publicados, no reejecutados. Las declaraciones posteriores
de SIGKILL real tampoco se reejecutaron aquí. La presencia humana Secure Enclave
permanece `NO_VERIFICADO` en el paquete. [Límites publicados](https://babylon60.com/pruebas-y-limites/).

La consulta DNS A a `1.1.1.1` devolvió `NXDOMAIN` para `babylon60.co`; eso describe
la respuesta de ese resolvedor, no acredita falta de registro ni typosquatting.
GitHub informa creación del repositorio público el 18 de octubre: no fecha el
inicio del desarrollo. `NOASSERTION` es el identificador devuelto por GitHub;
existe un archivo LICENSE con condiciones propias. No se emite una conclusión
jurídica. El importe de 15.000 no se confirmó: las peticiones directas para leer
datos estructurados devolvieron HTTP 403. [Registro de consultas](evidence/harness-audit-2026-10-24/web-facts.json).

## Comparación funcional

| Opción | Función y frontera | Límite relevante |
| --- | --- | --- |
| BABYLON | Memoria, propuesta de autorización ligada al efecto y evidencia; EDIN orquesta LLM | La revisión del espejo no acredita mediación completa ni runtime de la revisión actual |
| Claude Code con hooks | `PreToolUse` permite bloquear, pedir autorización o permitir llamadas dentro del agente | La política debe cubrir las rutas relevantes; el aislamiento de filesystem/red se configura aparte |
| Docker MCP Gateway | Organiza servidores MCP y ejecuta los servidores en contenedores con recursos y accesos configurados | No aporta el bucle LLM; no limita automáticamente procesos que operen fuera del gateway; la salida de red no se deniega globalmente por defecto |
| Cursor | Integra agente, modos de aprobación y sandbox para comandos compatibles | Auto-review usa un clasificador; las llamadas permitidas pueden ejecutarse fuera del sandbox. Debe revisarse el modo efectivo |
| Git y entorno aislado | Git conserva revisiones; el sandbox o VM limita recursos alcanzables | Git/worktrees no son confinamiento y no deshacen efectos externos; la protección depende del aislamiento añadido |

Fuentes de la comparación: [hooks](https://code.claude.com/docs/en/hooks),
[sandbox de Claude Code](https://code.claude.com/docs/en/sandboxing),
[seguridad de Docker MCP Gateway](https://github.com/docker/mcp-gateway/blob/main/docs/security.md),
[modos de Cursor](https://cursor.com/docs/agent/security/run-modes) y
[Git worktree](https://git-scm.com/docs/git-worktree).
No se midieron latencia, coste, resistencia a ataques ni facilidad de uso entre
productos. Estas capas pueden combinarse; la tabla no establece un ganador.

Para decidir si BABYLON aporta control adicional, la prueba decisiva sería fijar
una revisión limpia y ejecutar el mismo efecto protegido por todas sus rutas:
tool call, shell directo, MCP alternativo, reutilización y reinicio. Registrar
el efecto realmente observado, no solo ALLOW/DENY, y vincular código, política,
resultado y clave de confianza. Es un criterio de aceptación propuesto, no una
campaña ejecutada ni una garantía de producción.

## Reproducción mínima

En una carpeta de trabajo nueva, con Git, Python y el toolchain de Lean indicado:

```sh
git clone https://github.com/borjamoskv/babylon60-verification.git
cd babylon60-verification
git checkout --detach a4657d9fcfeff49791ae75486cd03f3509a2c1f7
python3 verify.py
python3 verify.py --expected-manifest-sha256 82f77891b6e9301134855b3d57fedc036d33e2ccaf81f052afcc79c5c061cabb
lake env lean --version
lake build
```

El SHA-256 procede de la misma publicación; no sustituye una clave independiente.
Para repetir los controles negativos, usar un pin de 64 ceros y, en otra copia
desechable, añadir un comentario a CLAIMS.toml sin actualizar el manifiesto:
ambas ejecuciones deben salir con código 1.

## Cierre actualizado: topología y presupuesto corregidos

En la continuación del 24 de octubre se reprodujeron los dos fallos originales:
la topología exigía firmas en documentos de instrucciones, y la CLI de presupuesto
no aceptaba `--workspace-only`. Durante la revisión llegaron correcciones
concurrentes de ambos validadores. Se conservaron y se verificaron sin restaurar
versiones anteriores ni editar las reglas del operador.

- **Topología:** separa la estructura de los documentos de la firma solicitada con
  `--response`; conserva comprobaciones de archivos, symlinks y referencias MCP.
  Se comprobaron documentos sin firma, rechazo de documentos vacíos o con fences
  abiertos, enlaces incorrectos y distinción entre índice Git y árbol de trabajo.
- **Presupuesto:** `--workspace-only` excluye reglas globales, cuenta una vez cada
  documento raíz y mantiene los límites y los errores de reglas locales. La
  telemetría solo se omite mediante `--skip-ghost-listeners`. Se corrigió además
  el mensaje de éxito local: ya no afirma ausencia de duplicados entre ámbitos
  cuando el global no se ha inspeccionado.
- **Preservación:** no se modificaron dependencias, lockfiles ni el índice Git del
  operador. Las pruebas de `--staged` usan un repositorio temporal. Los cambios
  concurrentes de reglas y runtime quedan fuera de las ediciones de esta entrega.

| Control ejecutado | Resultado |
| --- | --- |
| `python3 scripts/guards/verify_active_topology.py` | PASS, salida 0 |
| `python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners` | PASS, salida 0; 9.890 bytes inspeccionados; reglas globales y telemetría `NOT_CHECKED` |
| `python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only` | PASS, salida 0; 62 documentos, 41 archivos Python y enlaces/anclas de 15 documentos de gobernanza |
| Pytest dirigido con `uv run --locked` | 168 tests y 103 subtests pasan; incluye 10 regresiones CLI nuevas |
| Ruff sobre validadores y regresiones | PASS |
| Autoprueba del validador de firmas | 6.400 comprobaciones pasan |

Las [salidas actuales](evidence/harness-audit-2026-10-24/followup-controls.json)
sustituyen el estado pendiente, sin borrar las
[salidas históricas de topología](evidence/harness-audit-2026-10-24/quality-gates.json)
ni el [error histórico de CLI](evidence/harness-audit-2026-10-24/concurrent-document-gates.json).
Los controles documentales no certifican runtime ni repiten las pruebas del espejo.
Los enlaces locales, estructura y JSON de esta entrega se registran en
[documento](evidence/harness-audit-2026-10-24/document-checks.json).

## Selección para el commit local

La revisión del diff separó las correcciones de esta tarea de la ampliación
concurrente de gobernanza. El commit incorpora únicamente la validación de
instrucciones sin firma obligatoria, el modo de presupuesto `--workspace-only`
con su mensaje de alcance, las diez regresiones CLI y este informe con evidencias.
Las reglas, CI, hooks, módulos nuevos de gobernanza, cambios de runtime y
ampliaciones del recuento permanecen fuera de la selección. Los archivos de
trabajo de los validadores conservan sus cambios concurrentes completos.

Se materializó el contenido seleccionado sobre `a620e383d695e82d14b57066967194b8c8a3022b`
en una carpeta temporal. Pasan allí los 168 tests y 103 subtests, Ruff, los controles
de presupuesto y semántica y 6.400 comprobaciones de firmas. La versión seleccionada
de topología pasa contra el índice temporal y contra el árbol del operador.
La ejecución reutilizó el entorno Python existente con `uv run --locked --no-sync
--active`, sin instalar paquetes ni cambiar lockfiles.

El presupuesto de esa selección conserva el recuento previo de AGENTS.md:
4.108 bytes. Los 9.890 bytes y las 15 verificaciones documentales de la tabla
anterior corresponden al árbol compartido ampliado; no se atribuyen al commit
mínimo. Se conservan ambos resultados con sus ámbitos en la
[evidencia de selección](evidence/harness-audit-2026-10-24/commit-selection.json).
La autorización comprende un commit local, sin push.
