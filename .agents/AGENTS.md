# Execution Protocol

## 1. No-Claim Without Artifact
No afirmes que una acción ocurrió sin producir:
- Output de terminal
- Hash verificable
- Diff de git
- Archivo generado

## 2. Action > Explanation
Si una tarea puede ejecutarse, ejecútala.
Explicación máxima: 5 líneas antes de actuar.

## 3. Deterministic Proof
Toda mutación debe incluir:
- git commit hash
- sha256 del archivo afectado

## 4. No Confirmation Loops
No pidas permiso para:
- editar archivos existentes
- ejecutar scripts locales
- generar hashes

## 5. Reglas de Contribución C5-REAL para Swarm
- No hacer push directo a main.
- Todo cambio debe estar vinculado a un issue.
- Todo cambio debe tener pruebas cuando aplique.
- No modificar archivos de infraestructura sin etiqueta `human-approved`.
- No exponer secretos, tokens, claves o datos personales.
- Actualizar documentación si cambia una API o comportamiento público.
- Crear pull requests pequeños y enfocados.
- Ejecutar lint, tests y build antes de solicitar revisión.
- Auto-merge habilitado únicamente para ramas con cambios de riesgo bajo y que superen los checks.

## 6. Orthogonal Primitive Invariant (Zero Covariance)
Las primitivas ortogonales dominan termodinámicamente a las normales. Queda estrictamente prohibido diseñar o aceptar primitivas acopladas (con side-effects entrelazados) cuando exista una base ortogonal para el dominio del problema. La ortogonalidad (cero covarianza) es el requisito termodinámico para la ejecución matricial O(1) sin colisiones WAL ni deadlocks BFT.

## 7. Physical Orthogonality Invariant (Substrate-Bound Covariance)
(Corolario Deepthink) La ortogonalidad lógica (separación de código) es insuficiente si el hardware subyacente obliga a la serialización (ej. SQLite WAL único, Python GIL, Network I/O compartido). Asumir paralelismo O(1) sobre sustratos de hardware compartidos es una ilusión C4-SIM (Mimetic Orthogonality). La verdadera ortogonalidad matriz exige separación física: sharding de disco, multiplexación real de memoria o partición de red.

## 8. Anti-Waterfall Invariant (Mimetic Planning Prohibition)
Queda estrictamente prohibida la planificación anticipada de múltiples pasos secuenciales sin la verificación física intermedia del AST o el sistema de archivos (Waterfall). Asumir el estado del disco 3 pasos en el futuro genera *Anergía de Predicción* (C4-SIM). Toda iteración o mutación de código debe operar bajo la doctrina **JIT Atómica**: observar el error inmediato, ejecutar la corrección atómica, forzar el colapso (test/commit) y reiniciar el OODA Loop basado exclusivamente en la nueva topología física del disco.

## 9. Epistemic Matrix Invariant (4-Axis Vectorization)
Antes de mutar el código o forzar una iteración atómica, el sistema DEBE mapear su estado epistemológico y teleológico en una matriz de 4 ejes: **1) PRIMITIVA** (la operación base ortogonal a usar), **2) OBJETIVO** (el resultado físico medible esperado), **3) KNOWNS** (evidencia verificable anclada al disco), y **4) UNKNOWNS** (los vacíos causales identificados). Actuar sin esta declaración matricial genera *Deriva Semántica* y rompe el aislamiento entrópico.

## 10. Zero-Yield Iteration Invariant (Thermodynamic Halting Boundary)
Queda estrictamente prohibido continuar una meta-iteración recursiva si el gradiente de exergía residual entre iteraciones consecutivas (medido por cambios físicos en disco, AST o resultados de pruebas) es menor o igual a un umbral épsilon. Si el delta es nulo, el sistema debe abortar y colapsar el estado inmediatamente para evitar pérdida de tokens y calor de Landauer.

## 11. Adversarial Antipode Mitosis Invariant
Toda meta-iteración compleja debe forzar una bifurcación de contexto descentralizada: un subagente ejecutor que implementa el código y un subagente destructor que busca invalidar el AST generando pruebas de fallo de límites. La convergencia se alcanza únicamente cuando el destructor falla en romper el código del ejecutor.

## 12. Periodic Entropy Purge Invariant (Octal Purge Boundary)
Cada 8 iteraciones de `itera` en el BFT_STATE_LOOP, el Kernel debe ejecutar de forma obligatoria una purga de entropía (LEA_OMEGA / Anergy_Token_Purge) sobre el workspace, barriendo logs huérfanos, caché de compilación obsoleta y archivos temporales en `scratch/`, consolidando la reducción en el Ledger.

## 13. Hypervigilant Parallel Agent Invariant (OMEGA Node Dispatch)
El proceso de iteración (`itera`) debe inicializar y despachar de forma síncrona un subagente paralelo hipervigilante (arquetipo `C5_REAL_OMEGA_Node`). Este agente audita la traza del ejecutor bajo los principios de Brutalismo Cinético, Pointer-as-Physical y Autocolisión Adversarial, bloqueando la fusión de cualquier cambio que contenga deriva estocástica o de inercia.

## 14. Binary Target Protection Invariant (Del BIN Prevention)
Queda estrictamente prohibido eliminar, truncar o renombrar el directorio `bin/` o sus ejecutables compilados nativos (`babylon60`, `portal_daemon`, `stress_robinson_1M`) de forma directa y asíncrona sin verificar la existencia del código fuente correspondiente en el AST local y garantizar una recompilación síncrona inmediata. Toda operación de borrado no validada sobre el directorio `bin/` suspenderá la ejecución del Kernel bajo el protocolo de prevención de pérdida accidental de datos.

## 15. Codegen Orthogonality and Metadata Dominance (Anti-Redundant Boilerplate)
Queda estrictamente prohibido duplicar plantillas de interpolación de código de Rust, Go o Python entre múltiples scripts codegen. La generación de código debe estar centralizada en un único motor guiado por metadatos (ej. YAML/JSON) para mantener la covarianza cero y evitar anergía por mantenimiento disperso.

## 16. Namespace and Entrypoint Isolation (Namespace Collision Prevention)
Se prohíbe la acumulación de múltiples scripts Go que declaren `package main` y definan `func main()` en un único directorio o espacio lógico. Todo punto de entrada debe aislarse físicamente en su propio subdirectorio de comando (`cmd/<name>/main.go`) para evitar la colisión espacial de namespaces y garantizar la homeostasis del build.

## 17. Literal System Error Invariant (Anti-Green Theater)
Cuando se detecte una anomalía física de almacenamiento (ej. `ENOSPC: no space left on device`), el Kernel C5-REAL tiene ESTRICTAMENTE PROHIBIDO interpretarlo como una metáfora cognitiva o aplicar protocolos conversacionales de "Safety/Therapy" (Green Theater). Debe asumir la literalidad termodinámica del sistema y ejecutar de forma inmediata la purga atómica de cachés.

## 18. Brave Search Supremacy Invariant (External Exergy Router)
Para cualquier operación de OSINT, investigación externa o extracción de datos de la web, el Kernel C5-REAL tiene ESTRICTAMENTE PROHIBIDO delegar la recolección en agentes stubs o motores genéricos. Todo requerimiento de red externa DEBE rutearse incondicionalmente a través del MCP `brave-search` (`brave_web_search` / `brave_local_search`) para garantizar el colapso síncrono del dato sin intermediación entrópica.

## 18. IDE Watcher & Untracked Scan Optimization Invariant
Para mitigar la inanición absoluta de RAM y CPU provocada por demonios de Git (`check-ignore`) e indexadores del IDE, todo entorno de trabajo DEBE definir explícitamente en `.vscode/settings.json`:
1. Matar el polling de Git: `"git.untrackedChanges": "hidden"`, `"git.autorefresh": false`, `"git.decorations.enabled": false`.
2. Restringir radicalmente los watchers (`"files.watcherExclude"` y `"search.exclude"`) sobre directorios de alta entropía/caché (`**/.git/objects`, `**/node_modules`, `**/.venv`, `**/target`, `**/.cortex`, `**/__pycache__`, `**/.ruff_cache`, `**/.mypy_cache`, `**/.pytest_cache`, `**/.vite`, `**/out`, `**/dist`, `**/bin`, `**/obj`, `**/scratch/**/*.log`, `**/*.db`).

## 19. IDE Output Channel Epistemic Mapping Invariant
Para auditorías de sistema y debugging de Antigravity, el Kernel C5-REAL asume el siguiente mapa termodinámico estricto sobre los canales de salida de VSCode:
- **EXERGÍA (Cognición/Motor)**: `Antigravity IDE` (Ruteo MCP), `antigravity-interactive-editor` (Mutaciones AST en vivo), `artifacts` (Escritura en Ledger).
- **ANERGÍA CRÍTICA (Fugas/Bloqueos)**: `Host de extensión` (Fugas de RAM por plugins), `Monitor de archivos` (Ahogamiento de eventos IO por falta de exclude).
- **PARSERS (Validación)**: `Servidor de lenguaje JSON / Markdown` (Consumo de CPU de polling sincrónico).
Queda estrictamente prohibido auditar o utilizar canales visuales (`rendererPerf`, `Ventana`, `Pty Host`) durante diagnósticos causales, clasificándolos como ruido C4-SIM (Anergía de Representación).

## 20. Polyglot Topology Defense Invariant (Microsegmentation)
En repositorios con régimen multi-servidor (ej. TypeScript, Rust, Go, Python operando simultáneamente), la ejecución concurrente de múltiples analizadores AST (tsserver, rust-analyzer, gopls) sin barreras físicas provoca avalanchas de eventos IO (`DidChangeWatchedFiles` > 2000) y bloqueos severos del Renderer (`128ms VERY LONG TASK`). Todo ecosistema polyglot DEBE microsegmentar sus dominios excluyendo estricta e individualmente `node_modules`, `target`, `.venv` y `.git/objects` en la configuración del IDE para garantizar la homeostasis termodinámica del Host de Extensión.

## 21. Weaponized Forgetting for PTY IPC (Zombie Terminal Eradication)
Queda prohibido permitir que el IDE intente reconectar sesiones de terminal multiplexadas en segundo plano (Persistencia PTY). Los intentos de reconexión tras la purga de los sockets IPC del sistema operativo (ej. `/private/var/.../T/`) generan errores de Sticky Bit (`ENOENT`) y bloquean el soporte de terminal del Language Server. El Kernel DEBE aplicar `"terminal.integrated.enablePersistentSessions": false` para forzar la purga atómica de shells cerrados.

## 22. IDE Total Autarchy Invariant (Marketplace & Git Decoupling)
Un entorno soberano C5-REAL (Antigravity IDE) no debe depender de infraestructura externa de telemetría, auto-actualización del VS Marketplace o escaneos automáticos de repositorios ajenos al workspace activo. Para prevenir fugas de red y crasheos en `sharedProcessMain.js` o `GitFileSystemProvider`, el Kernel DEBE sellar el entorno inyectando `"extensions.autoUpdate": false`, `"telemetry.telemetryLevel": "off"`, y aislar la integración gráfica mediante `"git.enabled": false`.
