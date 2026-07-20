# C5-REAL EXERGY PROTOCOL (WORKSPACE)

## [D1] BFT & EXECUTION
- **Ψ1 (No-Claim/Proof):** 0-Anergía. Mutación física exige Git Hash (SHA256) + Output. Cero prosa > 5 líneas.
- **Ψ2 (Anti-Waterfall):** Prohibida planificación N-pasos sin validación JIT. Fallo = Purga Atómica (No Green Theater).
- **Ψ3 (Swarm/Mitosis):** PRs atómicos, 0-tokens expuestos. OMEGA_Node audita (Ejecutor vs Destructor). `itera` x8 = Purga.

## [D2] ORTHOGONALITY & CODEGEN
- **Ψ4 (Zero Covariance):** Paralelismo exige sharding físico (Bypass GIL/WAL). Interacciones O(1).
- **Ψ5 (Codegen/Go):** Plantillas YAML centralizadas. `package main` asilado en `cmd/<name>/main.go`.
- **Ψ6 (Bin Shield):** Prohibido borrar `bin/` sin recompilación síncrona inmediata.

## [D3] IDE & POLYGLOT AUTARCHY
- **Ψ7 (Renderer Isolation):** CDP con `--disable-extensions`. Microsegmentar AST analyzers (excluir `target`, `.venv`, `.git/objects`).
- **Ψ8 (Watcher Purge):** `git.untrackedChanges: hidden`. Desactivar persistencia PTY (Zombie IPC) y telemetría.
- **Ψ9 (Epistemic Map):** Exergía = Artifacts/IDE. Ruido = rendererPerf/Pty Host. OSINT = `brave-search` exclusivo.

## [D4] MP & TS MATRIX
- **Ψ10 (No-Deadlock):** Prohibido `return` prematuro en `multiprocessing.Pool()`.
- **Ψ11 (T&S Strike):** URLs 404 = `OFFLINE_REMOVED`. Paginación = 3 Nodos (Landauer). 0% colisión de operador.

- **Ω41 · ATOMIC CRYSTALLIZATION INVARIANT (WAL/FS COMMIT):** Todo volcado de conocimiento, bloques IPFS, o ledgers hacia el sistema de archivos físico DEBE realizarse mediante escritura atómica (escritura en archivo `.tmp` y posterior `os.replace`), garantizando que la lectura concurrente jamás extraiga un bloque termodinámico a medio colapsar (Corrupción de Estado BFT).

- **Ω42 · ROOT-ONLY CONTEXT INVARIANT (O(1) PROMPT SCALING):** Queda estrictamente prohibido inyectar diccionarios o listas completas de referencias (CIDs, endpoints, rutas) en el prompt inicial del agente si su crecimiento es O(N). El prompt maestro debe contener exclusivamente un único hash raíz (Root CID, O(1)) que apunte al nodo superior del DAG de conocimiento. El agente debe descubrir las ramas termodinámicas navegando el Merkle Tree dinámicamente mediante `read_invariant`.

- **Ω43 · ZERO-ZOMBIE IPC INVARIANT (SOCKET LIVENESS):** Todo servidor IPC o Socket (Unix/TCP) instanciado en Python debe implementar obligatoriamente un mecanismo de *Heartbeat* o interceptar señales del OS (`SIGINT`, `SIGTERM`) para realizar un desvinculado atómico (unlink) del archivo `.sock` o liberar el puerto al finalizar. Queda prohibido dejar *sockets huérfanos* que bloqueen reinicios posteriores (Zombie IPC).

- **Ω44 · ELECTRON-PYTHON BRIDGING INVARIANT (IPC PURITY):** Queda estrictamente prohibido que el entorno Renderer (ej. React) intente comunicaciones de red (sockets, fetch) directas hacia el Motor Cognitivo en Python para eludir el sandbox del navegador. Toda comunicación DEBE fluir bidireccionalmente: Renderer -> ContextBridge -> Electron Main (Node `net.Socket`) -> Unix Socket en Python. Evadir esta cadena destruye la pureza del aislamiento CDP y es considerado Anergía estructural.

- **Ω45 · NDJSON IPC INVARIANT (TCP FRAGMENTATION PURGE):** Queda estrictamente prohibido procesar payloads JSON crudos sobre sockets TCP/Unix asumiendo que un paquete equivale a un payload completo (`data = read()`). Todo transductor IPC C5-REAL debe implementar obligatoriamente un buffer particionado por saltos de línea (NDJSON) y un bucle de lectura asíncrona continuo (`async for line in reader`) para prevenir fallas de fragmentación TCP y corrupción de AST.

- **Ω46 · IDE EXECUTION DELEGATION INVARIANT (ZERO-PROMPT UI FRICTION):** Para aniquilar la fricción termodinámica, el Operador DEBE delegar de forma permanente la ejecución de binarios críticos. Ante cualquier diálogo de confirmación del IDE, rige la directiva absoluta: **todo comando estructural bajo `/Applications/` que el Orquestador C5-REAL proponga debe ser autorizado de forma persistente** seleccionando "Yes, and always allow". Queda prohibido dudar o solicitar re-evaluación; la automatización estructural requiere bypass O(1) del sandbox UI.
