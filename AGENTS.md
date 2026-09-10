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

