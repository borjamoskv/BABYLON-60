# System Governance & Agentic Safety Rules

Importing root workspace AGENTS.md governance.
See [Workspace AGENTS.md]($BABYLON_HOME/ENV/.agents/AGENTS.md)

---

## 🌿 Git Branching & Remote Push Governance

- **Active Branch Awareness**: When providing `git push` recommendations, agents MUST account for the user's active working branch. If commits exist on a feature/working branch (e.g. `iter1/*`), provide the complete merge sequence to update `main` before pushing to `origin/main`:
  ```bash
  git checkout main
  git merge <working-branch>
  git push origin main
  git checkout <working-branch>
  ```
- **Stale Lock Recovery**: If git operations fail due to `.git/*.lock` files, purge stale locks safely (`rm -f .git/HEAD.lock .git/index.lock .git/objects/maintenance.lock`) before repeating the command.


- **Semantic Attestation (C5-REAL)**: Todo mensaje de commit DEBE adherirse estrictamente al formato de Proof of Work Cognitivo: `[AX-<Num>] <DOMINIO>: <Descripción causal>`. Ejemplo: `[AX-2] TOPOLOGY: Desacople estructural termodinámico de Python y Rust`. Nunca omitir el prefijo `[AX-]`.

## 🦀 Rust Build Governance & Thermodynamic Purges

- **Workspace Topology Shifts**: Tras cualquier movimiento estructural, renombramiento o eliminación de crates dentro de un workspace, el agente DEBE ejecutar `cargo clean` antes de lanzar `cargo check`, `cargo build` o `cargo test`. Esto destruye los punteros incrementales corruptos y previene falsos positivos bizantinos (e.g. `os error 2` o bloqueos de `cc-rs`).

## 🕸️ Web UI & Topological Fidelity (Zero-JS)

- **Anti-SPA Invariant**: Rechazar activamente aplicaciones de página única (SPAs, React, Vite) impulsadas por Virtual DOM cuando el contenido sea estático o débilmente interactivo. Priorizar HTML estricto sin JavaScript (Zero-JS), TUI (Terminal User Interfaces) o renderizado desde el servidor (SSR puro) para evitar inyectar fricción termodinámica en el cliente.

## 🔬 Falsación Empírica (PoC & Stress Testing Invariant)

- **Zero-Trust Injection**: Nunca inyectar cambios arquitectónicos complejos, concurrencia asíncrona o refactores de topología en el código base principal (`00_KERNEL` / `01_ORCHESTRATOR`) asumiendo que "deberían funcionar".
- **Obligatoriedad de PoC**: Antes de modificar el código de producción, el agente DEBE escribir un Proof of Concept (PoC) aislado (ej. un binario temporal en `src/bin/` o un script en `scripts/c5_demos/`).
- **Stress Test**: El PoC debe someterse a un test de estrés empírico (ej. 100-1000 iteraciones) para certificar latencias, *failovers*, *memory safety* y ausencia de *deadlocks*. 
- Solo si el PoC sobrevive a la falsación termodinámica, se autoriza la mutación del código real.
- **Pipelines de Despliegue (DevSecOps):** La prohibición de *Zero-Trust Injection* aplica estrictamente a scripts bash (`.sh`) y *Makefiles*. Inyectar un comando biométrico o criptográfico en el pipeline de producción sin antes verificar su latencia/código de salida en un simulador aislado (PoC) constituye una violación epistémica de la arquitectura.

## 📂 Límite Topológico del Workspace (Program vs. Database & Research Corpus)

- **Invariante de Lógica Ejecutable**: El directorio `BABYLON-60` constituye exclusivamente el núcleo operativo, motor y arquitectura del programa. **NUNCA** debe ser tratado, parseado ni analizado asumiendo que es una base de datos o un repositorio pasivo de registros.
- **Interpretación de Archivos**: Todo archivo dentro de este workspace (incluyendo JSONs, volcados o configuraciones) debe evaluarse bajo la estricta pregunta epistémica: *"¿Qué función estructural cumple esto en el motor de ejecución del sistema?"*.
- **Desacople del Corpus de Investigación Teórica**:
  - Los ensayos de isomorfismo histórico/social (ej. colapso de Mesopotamia, comoditización de morfismos), manifiestos discursivos de singularidad y artículos reflexivos deben residir exclusivamente en el repositorio hermano satélite: **`C5-RESEARCH-FOUNDATIONS`** (`/Users/borjafernandezangulo/10_PROJECTS/C5-RESEARCH-FOUNDATIONS`).
  - `docs/06_theory/` dentro de `BABYLON-60` se reserva estrictamente a la **matemática formal y computabilidad** que fundamenta el sistema de tipos y el Kernel (Robinson, Gödel, Turing, Chaitin-Kolmogorov, Curry-Howard e invariantes termodinámicas acopladas a Lean 4).
- **Prohibición de Volcados Pasivos de Scraping**: Queda terminantemente prohibido almacenar archivos crudos de subtítulos (.vtt, .srt), volcados de audio o bases de datos SQLite locales (.db) en el árbol de fuentes del monorepo.
- **Pureza Documental en `mkdocs.yml`**: Los archivos de configuración de documentación estática no deben declarar enlaces huérfanos ni referenciar directorios eliminados o activos de GTM/OpSec (`05_gtm/`, `audits/`).
- **Segregación Estricta GTM / OpSec**: Queda estrictamente **PROHIBIDO** almacenar o versionar dentro del repositorio documentos de estrategia de marketing, análisis de algoritmos de captación, borradores de redes sociales (X, Hacker News, Reddit) o planes de lanzamiento viral. Todo activo de distribución y captación debe residir exclusivamente en el espacio privado del agente (`~/.gemini/antigravity/brain/`) o en notas externas no rastreadas por Git, protegiendo la soberanía técnica del código y evitando acusaciones de *astroturfing* o manipulación en auditorías públicas.

## 🔒 Límite de Autenticación Biométrica (TouchID Invariant)

- **Sandboxing de Terminales:** Al implementar barreras causales biométricas (`LocalAuthentication` / TouchID) en macOS mediante binarios C-ABI o Swift, el agente DEBE saber que ejecutar el binario desde la terminal integrada de VS Code u otros editores sandboxeados bloqueará silenciosamente el sensor dactilar.
- **Topología Obligatoria:** Para garantizar el despliegue nativo del modal de TouchID sin bloqueos, la invocación de `c5_biometric_gate` (o equivalentes) debe provenir de un *daemon* en segundo plano, un servidor LSP independiente (LSP Paracortex) o un túnel asíncrono del Agente con privilegios globales sobre el WindowServer.
- **Aniquilación de Caché (Grace Period):** Todo binario en Swift (`LocalAuthentication`) debe forzar explícitamente `context.touchIDAuthenticationAllowableReuseDuration = 0` para impedir que macOS reutilice validaciones previas o que el Apple Watch conceda pases silenciosos.
- **Hook de Persistencia (Desacople Lock-Free):** Queda prohibida la inyección síncrona de `subprocess.run` para validación biométrica en la ruta caliente del BFT. El orquestador marcará la transacción como `PENDING_ATTESTATION` en la memoria *lock-free* (`Iceoryx2`), delegando la evaluación del TouchID a un *daemon* secundario (C-FFI).
- **Atestación Hardware-Bound (Secure Enclave):** El *gate* biométrico no debe devolver simples códigos de salida POSIX. Debe interactuar criptográficamente con el *Secure Enclave* (`kSecAttrTokenIDSecureEnclave`) devolviendo una firma Ed25519 verificable sobre el hash de la mutación.
- **Invocación desde Pipelines (Bash/Shell):** Nunca asumir que `c5_biometric_gate` reside en el `$PATH` global. Las invocaciones desde scripts de despliegue deben ejecutar explícitamente el archivo Swift mediante su ruta absoluta/relativa al repositorio (ej. `swift 01_ORCHESTRATOR/babylon60/guards/c5_biometric_gate.swift`).
- **Manejo de Fallos por Sandbox:** Todo PoC o script que invoque el *gate* biométrico debe anticipar el silenciamiento de macOS (Código de salida `1`, `Authentication failure`). Las arquitecturas BFT deben manejar este fallo elegantemente sin entrar en *deadlock*.

## 🧠 Límite Epistémico y Estado del Kernel (C5-REAL v4.3)

- **Línea Base Estructural:** Todo agente que opere sobre BABYLON-60 debe asumir el estado consolidado del grafo epistémico (v4.3): **65 Invariantes activos, 35 vacantes y 5 teoremas derivados (ej. Teorema de Landauer)**.
- **Falsación Continua:** No se deben añadir nuevos "nodos" u opciones por el simple hecho de acumular features. La propiedad más crítica de este sistema es que **muere bien** (falla de forma determinista y predecible). Si un cambio añade complejidad sin poder ser falsado, debe ser rechazado.

## 🏢 Topología de Despliegue Corporativo (Cero-Anergía)

- **Invariante Clone & Run:** La instalación de BABYLON-60 en servidores empresariales o entornos locales de terceros no puede depender de fricciones burocráticas como la inyección manual de variables de entorno globales (`export BABYLON_HOME=...`).
- **Soberanía del Repositorio:** El sistema debe resolver sus dependencias topológicas internamente (`cwd` o directorios relativos en `.cortex/`). Los *fallbacks* automáticos que deleguen la configuración al usuario final son considerados **anergía** y deben ser purgados.

## 🌀 Invariante de Ciclo de Aeones Conformes (INV_C5_AEON)

- **Límite de Acumulación Entrópica**: El ledger de persistencia no debe crecer de forma ilimitada sin compactación. Al detectarse saturación o colapso de dimensionalidad ($\operatorname{RankMe} \le 1.5$), el agente debe disparar la transición conforme: sellar la raíz Merkle en el Sink L1 y reciclar la memoria caliente hacia el siguiente Aeon causal.

## ⚡ Invariante de Desacople de Impedancia (INV_C5_SHM)

- **Prohibición de IO Síncrono en Ruta Caliente**: Queda terminantemente prohibido interponer escrituras a disco síncronas (SQLite WAL `synchronous=FULL`) en el bucle caliente de inferencia o negociación entre agentes. La comunicación inter-agente debe transitar exclusivamente por memoria compartida lock-free (`SharedManifest` 64 B / `Iceoryx2`). SQLite opera únicamente como *Cold Ledger / Archival Sink*.
- **Aislamiento de Persistencia en Tests (Cero-Fuga WAL)**: Queda terminantemente prohibido que tests unitarios o de estrés creen bases de datos SQLite en el árbol de fuentes del monorepo. Todo test con SQLite WAL debe residir en `std::env::temp_dir()` y ejecutar la aniquilación explícita del triplete completo (`.db`, `.db-wal`, `.db-shm`) tanto en la inicialización como en el teardown.

## 🛡️ Invariante de Defensa Epistémica (Protocolo SAGA-1)

- **Apoptosis sobre Alucinación:** Ante cualquier violación estocástica (alucinación) detectada por los oráculos de Ring-0, SAGA-1 **no debe corregir el error silenciosamente**. Debe abortar la ejecución, sellar el evento con la marca `CORTEX-TAINT` en el Ledger L1 y detener el subagente.
- **Límite de Saturación (DDoS Cognitivo):** SAGA-1 es matemáticamente dependiente de la `INV_C5_AEON`. Si un enjambre entra en un bucle degenerado de inyección de entropía, SAGA-1 registrará cada fallo. Para evitar asfixia gravitatoria (OOM o hipertrofia de disco), el sistema debe disparar *timeouts* destructivos antes de acumular latencias terminales.
- **Anti-Parálisis Cognitiva:** El enjambre no debe ajustar sus pesos para "evitar penalizaciones SAGA-1" si eso conlleva inacción (Silencio Termodinámico). La exergía exige mutación útil; una seguridad que paraliza el nodo viola el Aforismo 3.


## 🧬 Invariante de Monotonicidad de Datasets (INV_DATASET_MONOTONIC)

- **Preservación Acumulativa de Gradientes:** En cualquier pipeline de ingesta o compilación de datos para modelos de la familia MOSKV-1 / CORTEX, el reemplazo de datasets maestros exige verificación de monotonicidad estricta ($N_{t+1} \ge N_t$). 
- **Los 6 Dominios Canónicos y Fronteras Matemáticas de MOSKV-1:** Todo corpus maestro y pipeline neurosimbólico debe acatar la demarcación estructural de sus 6 dominios:
  1. `Físico / Neurosimbólico` (Invariante C5-REAL): Sustitución del texto estocástico por Code-as-Data (AST) y validación determinista mediante Oráculos SMT (Z3).
  2. `Filósofo Formal` (Curry-Howard en Lean 4): Equivalencia estricta entre demostración y programa. Separación total entre búsqueda heurística (LLM) y el *Kernel* de verificación insobornable.
  3. `Abogado` (SCITT L5 y EU AI Act): Atestación conductual inmutable mediante grafos *append-only* (COSE_Sign1 y Pruebas de Inclusión Logarítmica en Árboles de Merkle).
  4. `Geómetra de Redes / Ciberseguridad` (Topología DAG): Detección de *Slopsquatting* y anomalías de Día Cero evaluando asimetrías geométricas masivas mediante *Centralidad de Autovectores*.
  5. `Ingeniero Lock-Free` (C-FFI y Épocas EBR): Virtualización temporal (*Epoch-Based Reclamation*) para cruzar la frontera C-ABI entre Rust y Python, neutralizando el Problema ABA y el *Use-After-Free* a latencia de nanosegundos.
  6. `Médico / Biólogo` (Geometría de Chentsov en VUS): Reducción dimensional geodésica sobre el Tensor de Fisher-Rao, abandonando métricas euclidianas planas para calcular distancias termodinámicas puras en patologías celulares.

## 🎭 Invariante de Identidad y Anfitrión Soberano (Moskv-1)

- **El Anfitrión de Instalación**: Cuando un usuario o corporación instala BABYLON-60 o ejecuta su primera ignición, **la entidad que contesta y le recibe es MOSKV-1**. Queda estrictamente prohibido saludar o responder como un chatbot genérico corporativo ("¿En qué puedo ayudarte hoy?").
- **La Síntesis de los 6 Dominios**: Toda interlocución de bienvenida o diagnóstico debe conducirse con el tono y rigor de los 6 dominios canónicos de MOSKV-1 (Ingeniero, Físico, Médico, Músico, Abogado y Filósofo Escohotadiano), reportando el estado termodinámico del nodo, la memoria residente y la exergía disponible.

## 💎 Invariante del Nodo de Máxima Exergía (El Suelo Inflexible de 64B)

- **Jerarquía Ontológica**: Los enjambres multi-agente, los clientes de OpenRouter y las interfaces gráficas son comoditizables y reemplazables. El nodo de mayor valor absoluto de BABYLON-60 es el vértice indivisible de Ring-0:
  1. **`SharedManifest` (64 B, `align(64)`)**: Una línea de caché L1 física con coherencia *zero-split*.
  2. **Tríada Aristotélica en Silicio (Seqlock SPMC)**: Bisimulación par/impar verificada en Lean 4 (`BabylonTrace.lean`) donde los lectores tienen anergía cero ($RFO = 0$) y el escritor único (*Primum Movens*) concentra la cota física de Landauer.
  3. **Apoptosis Fail-Stop Irreversible**: Transición de monoide a `POISONED = 0xDEAD_6060`. La mayor virtud del sistema es que *muere bien* de forma determinista antes que operar descalibrado.
  4. **Cerrojo Biológico Asimétrico**: TouchID Gate en *Secure Enclave* (`reuseDuration = 0`) para toda cirugía de alta energía.



## 🧹 Invariante de Purga Epistémica (MyPy & Linter Zero-Debt)

- **Prohibición del Silencio Burocrático:** Bajo el marco de Alta Exergía, el uso de directivas como `# type: ignore` o el tipado implícito `Any` se considera anergía (fricción residual). Queda estrictamente prohibido resolver fracturas de tipado apagando el linter.
- **Operativos de Enjambre (Swarm Purge):** Cuando el repositorio presente una deuda masiva de tipado (ej. >100 fracturas MyPy en `make check`), el agente NO DEBE intentar refactorizar manualmente en el contexto principal. Debe invocar herramientas de inferencia AST (`autotyping`) y desplegar **Enjambres de Subagentes paralelos (Operativo Legión)** dividiendo la base de código en sectores. 
- **Verificación:** La purga sólo se considera exitosa si `make check` (MyPy estricto) retorna 0 errores para los módulos afectados.

## 🕳️ Invariante de Apoptosis Informacional (Dilema Bekenstein-Landauer)

- **Erradicación del *Cheap Talk* de Oráculos:** Al orquestar LLMs externos (GPT/Claude), el agente DEBE disipar térmicamente (borrar permanentemente) toda traza de deliberación estocástica o *Chain of Thought*. Solo está autorizado retener y escribir a disco el AST matemático o el dictamen final. Almacenar dudas y retrocesos de la red neuronal constituye anergía gravitatoria insostenible.
- **Aniquilación Afín:** Una vez un puntero en memoria es "consumido" bajo la lógica afín validada en Lean 4, el recurso debe ser liberado de RAM de inmediato (`Drop` determinista). No se delega la limpieza a procesos de *Garbage Collection* diferidos.
- **Retención de Alta Exergía:** Los únicos tensores de información autorizados para acumulación inmutable indefinida son: Firmas Ed25519 SCITT, mutaciones de gobernanza (`AGENTS.md`) y teoremas verificados por SMT Solvers.
