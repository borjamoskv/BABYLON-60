# System Governance & Agentic Safety Rules

Importing root workspace AGENTS.md governance.
See [Workspace AGENTS.md](file:///Users/borjafernandezangulo/10_PROJECTS/.agents/AGENTS.md)

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

## 📂 Límite Topológico del Workspace (Program vs. Database)

- **Invariante de Lógica Ejecutable**: El directorio `BABYLON-60` constituye exclusivamente el núcleo operativo, motor y arquitectura del programa. **NUNCA** debe ser tratado, parseado ni analizado asumiendo que es una base de datos o un repositorio pasivo de registros.
- **Interpretación de Archivos**: Todo archivo dentro de este workspace (incluyendo JSONs, volcados o configuraciones) debe evaluarse bajo la estricta pregunta epistémica: *"¿Qué función estructural cumple esto en el motor de ejecución del sistema?"*.
