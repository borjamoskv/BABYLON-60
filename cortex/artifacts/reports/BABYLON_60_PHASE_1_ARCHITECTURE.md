# [AUDIT] BABYLON-60 — Fase 1: Arquitectura Global y Reconstrucción del Sistema

## 1. Declaración de Integridad y Nivel de Realidad

Este documento presenta la reconstrucción estructural e ingeniería inversa de la **Fase 1 (Arquitectura Global)** de la pila tecnológica de `BABYLON-60` mediante la inspección física del AST y flujos de estado locales.

**A. Verificación del Ledger Físico:**
- **Entorno de Ejecución:** Mac OS local (Arquitectura Apple Silicon M-Series).
- **Alcance del Análisis:** Monorepo `BABYLON-60` completo (1.502 archivos indexados).
- **Nivel de Realidad:** C5-REAL (ejecución y validación sobre disco).

---

## 2. ModuleGraph (Grafo y Mapa de Módulos)

El ecosistema está fragmentado físicamente en subproyectos desacoplados que interactúan a través de interfaces bien definidas:

**A. Capa Core Python (`babylon60/`):**
- **`babylon60/bft/`**: Módulo de consenso BFT. Contiene `consensus_ledger.py` (votos Ed25519, auditoría del estado), `master_ledger_queue.py` y `ledger_actor.py` (concurrencia de un único escritor de base de datos).
- **`babylon60/compiler/`**: Módulo de transcompilación y optimización de código intermedio. Contiene `lean_backend.py` para interfaces con el verificador formal Lean.
- **`babylon60/utils/`**: Utilidades termodinámicas. Contiene `landauer.py` (cálculo del coste energético de disipación de información), `pulmones.py` y `void_accel.c` (aceleración de I/O en C nativo).
- **`babylon60/extensions/`**: Módulos agénticos especializados. Incluye extensiones para blockchain/web3, scraping, cifrado, control háptico de macOS (`mac_maestro`), fiscalidad agéntica, entre otros.

**B. Capa del Entorno Integrado (`babylon60-ide/`):**
- **`babylon60-ide/extension/`**: Extensión de navegador Chrome en Manifest V3 (MV3) para capturar en tiempo real las pulsaciones y cambios de AST en el editor y enviarlos al backend local.
- **`babylon60-ide/frontend/`**: Interfaz de visualización reactiva construida en React y Vite. Renderiza la topología de la memoria agéntica mediante Canvas WebGL2/WebGPU.
- **`babylon60-ide/backend/`**: Servidor local FastAPI. Expone la API REST, orquesta los sockets de inferencia locales y sirve como servidor MCP a través de `mcp_symbol_helper.py`.

**C. Capa Rust de Alto Rendimiento (`strike_rs/` & `src-tauri/`):**
- **`strike_rs/`**: Núcleo de cálculo causal y criptográfico. Implementa el Poset Causal (`TaintEngine`), la validación Kahn de aciclicidad, y la máquina del núcleo lógico Harrop (Ω₀ en `omega0.rs`).
- **`src-tauri/`**: El motor nativo que empaqueta la app. Implementa el reloj DSP (`dsp_clock.rs`), la captura háptica (`ear.rs`) y la lógica de pointer-swap para hot-reload de librerías dinámicas (`antigravity.rs`).

**D. Capa de Isomorfismo y Verificación (`causal_isomorphism/` & `proof/lean/`):**
- **`causal_isomorphism/`**: Contiene la definición de la Representación Intermedia (`ir.py`), el linter de consumo único (`linear_checker.py`), y los emisores de Rust y Solidity para propagar invariantes.
- **`proof/lean/`**: Formalización matemática del sistema y verificación formal de teoremas en Lean para certificar la consistencia del kernel.

---

## 3. DependencyGraph (Grafo de Dependencias)

El flujo de dependencias sigue una estructura estrictamente acíclica (DAG) a nivel de lenguajes y módulos:

```
[Lean Formalization] ──(Invariantes Matemáticos)──> [F# Domain Design]
                                                           │
                                                  (Causal Transpiler)
                                                           │
                                                           ▼
[Chrome MV3 Extension] ──(WebSockets AST)──> [FastAPI Backend] <──(REST/CORS)── [Vite Frontend]
                                                  │         │
                                      (sys.path)  │         │  (Ollama Local Socket)
                                                  ▼         ▼
                                         [babylon60 Core]  [Local LLM (Mamba/MLX)]
                                                  │
                                          (FFI / PyO3 / IPC)
                                                  │
                                                  ▼
                                         [strike_rs (Rust)] ──(BLAKE3)──> [Cortex Poset Taint]
                                                  │
                                            (CoreAudio)
                                                  │
                                                  ▼
                                         [Tauri OS Orquestador]
```

---

## 4. ExecutionFlow (Flujo de Ejecución)

El ciclo de vida de una mutación del sistema sigue este camino determinista:

```
1. OPERADOR HUMANO  ──(Edita código en la IDE)──> Captura de eventos del AST (Tree-sitter)
                                                                 │
                                                       (WebSocket en MV3)
                                                                 │
                                                                 ▼
2. FASTAPI BACKEND  <─────────────────────────── Ingesta en endpoint /api/sentinel/transduce
        │
   (Evalúa permisos y delega)
        │
        ▼
3. STRIKE_RS (RUST) ──(add_node en Poset)───> verify_kahn_invariant() (¿Es acíclico el Grafo?)
        │                                                        │
        │                                                [FALSO] ──> raise CycleDetected
        │                                                        │
        │                                               [VERDAD] ──> compute_cortex_taint (BLAKE3)
        ▼
4. NÚCLEO LÓGICO Ω₀ ──(verify Harrop logic)──> Control de Modulación (Hume's Rule)
        │                                                        │
        │                                                [FALSO] ──> raise HumeViolation
        │                                                        │
        │                                               [VERDAD] ──> Voto válido Ed25519 (BFT Consensus)
        ▼
5. SQLITE WAL       <──(Escribe a disco)──── BFTLedgerActor (busy_timeout=5000ms)
        │
   (Commit físico)
        │
        ▼
6. GIT SENTINEL     ──(git add . && git commit)──> Ledger criptográfico consolidado (C5-REAL)
```

---

## 5. AgentArchitecture (Arquitectura de Agentes y Memoria)

La cognición agéntica de BABYLON-60 se distribuye en tres niveles de abstracción:

**A. El Hipocampo Local (Mamba SSM / MLX Local):**
- Red de memoria recurrente local que corre a nivel de silicio mediante Ollama.
- Gestiona la autocompletación semántica y mantiene el rastro de la atención contextual sin enviar datos al exterior (Zero-Network Policy).

**B. El Gateway de Inferencia de Nube (OpenRouter Bridge):**
- Canal para inferencia de gran tamaño (Claude, DeepSeek-Coder).
- Se utiliza únicamente cuando el motor local no dispone del presupuesto computacional para resolver refactorizaciones de alta entropía.

**C. Estructuras Sensorio-Motoras (Notch Bridge / Alcove):**
- Un buzón físico que procesa archivos asíncronamente en macOS.
- **Body-Doubling Acústico (CoreAudio DSP):** Traduce las discrepancias lógicas del AST en micro-interrupciones armónicas en el stream de audio del usuario, sirviendo como canal de retroalimentación inmediato sin sobrecarga de texto (cero Green Theater).

---

## 6. StateFlow & DataFlow (Flujo de Estados y Datos)

- **Causal Taint (BLAKE3):** El hash global de integridad del repositorio se calcula concatenando los IDs y payloads de los nodos del Poset en su orden topológico estricto:
  $$Hash_{total} = \text{BLAKE3}(Id_0 \parallel Payload_0 \parallel Id_1 \parallel Payload_1 \dots)$$
- **Serialización CBOR / CBOR Canónico:** Los payloads de las transmutaciones de estado se codifican en CBOR (Concise Binary Object Representation) para garantizar el determinismo bit-a-bit del hash y evitar la inestabilidad de formateo que sufre JSON (espacios, saltos de línea).
- **Lamport Ordering:** Todas las transacciones concurrentes calculan el tiempo lógico:
  $$Lamport_t = \max(Lamport_{local\_db}) + 1$$
  Esto garantiza un orden secuencial total de operaciones concurrentes en la red agéntica BFT sin depender de relojes físicos de sistema, vulnerables a desvíos.

---

## 7. TrustBoundaries (Límites de Confianza y OPSEC)

El sistema define límites de seguridad estrictos (Sandboxes) para mitigar la ejecución no controlada:

- **Sandbox de Ejecución (`KaosExec`):** Aísla los subprocesos de shell y comandos locales mediante políticas restrictivas, requiriendo ganchos de autorización con permisos explícitos del Operador.
- **Zero-Network Boundary:** El endpoint FastAPI (`validate_zero_network`) restringe todas las conexiones HTTP de los agentes al bucle local (loopback `127.0.0.1` / `localhost`).
  - *Fallo Crítico Encontrado:* La validación ingenua mediante `.startswith()` puede eludirse enviando direcciones como `http://localhost.attacker.com` o `http://localhost@attacker.com`, rompiendo este límite de confianza.
- **Causal Taint Gatekeeper:** Ningún cambio del sistema de archivos puede fusionarse a la rama activa si no contiene una firma criptográfica Cortex-Taint válida generada por `strike_rs`.

⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima (Top 99.99):
- [Un hombre blanco y heterosexual](https://substack.com/home/post/p-204785962)
- [Fase 1: Arquitectura Global y Reconstrucción del Sistema](file:///Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/cortex/artifacts/reports/BABYLON_60_PHASE_1_ARCHITECTURE.md)
- [El Fragmento Hereditario Harrop y la Guillotina de Hume en Sistemas Inteligentes]
- [Causal Poset y Kahn Invariant: Prevención de Bucles Cíclicos en Rust]
