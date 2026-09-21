# 🗺️ BABYLON-60: SOTA Architectural Evolution Roadmap

![Status: C5-REAL](https://img.shields.io/badge/Status-C5--REAL-black?style=flat-square&logo=rust&logoColor=white)


**Document Status:** Strategic Draft
**Regime:** Causal-Determinist / Neuro-Symbolic Hybrid
**Objective:** Bridge the capability gap between BABYLON-60's strict formal verification invariants and 2026 State-of-the-Art (SOTA) agentic autonomy (MCTS, PRM, LSP-native editing, Micro-VMs).

---

## 🎯 Visión Arquitectónica: El Paradigma Híbrido "Fast-Slow Thinking"

La evolución SOTA de BABYLON-60 no implica relajar la seguridad, sino **aislar la entropía**. El sistema pasará a tener dos hemisferios operativos:
1. **Dream State (Alta Entropía - Búsqueda):** Micro-VMs estocásticas, ejecución libre, *vibe coding* y heurística MCTS.
2. **Ledger State (Cero Anergía - Consolidación):** Compilación determinista del código generado hacia el Kernel $F_{60}$ y WORM Ledger.

---

## 🗓️ Hitos de Ejecución (Milestones)

### Fase 1: Fundamentación Semántica (Semantic Grounding)
**Objetivo:** Eliminar la edición frágil basada en texto y el contexto lineal ciego.

* **[ ] Hito 1.1: Servidor MCP LSP Nativo**
  * **Descripción:** Implementar un servidor MCP que actúe como proxy hacia `rust-analyzer` (Rust) y `pylsp` (Python).
  * **Entregable:** Los agentes mutan el código mediante comandos semánticos (`[OBSOLETO: mcp_lsp_rename]`, `[OBSOLETO: mcp_lsp_extract_fn]`, `[OBSOLETO: mcp_lsp_apply_workspace_edit]`), garantizando que la salida del LLM genere sintaxis 100% válida.
* **[ ] Hito 1.2: GraphRAG & Embeddings de AST**
  * **Descripción:** Extraer el grafo de dependencias de funciones y módulos del repositorio utilizando árboles AST.
  * **Entregable:** Base de datos vectorial local (Qdrant/SQLite-vss) integrada con `cortex-persist` que permita al agente inyectar grafos de llamadas (*Call Graphs*) dinámicos, superando las limitaciones de la ventana de contexto.
* **[ ] Hito 1.3: Resolutor de Dependencias 4D (Temporal Solver)**
  * **Descripción:** Un motor de evaluación epistémica que fuerza al agente a computar el estado temporal completo del ecosistema antes de mutarlo.
  * **Entregable:** Matriz de validación que bloquea cualquier acción que ignore: **Pasado** (compatibilidad hacia atrás, historial de versiones y vías de *rollback*), **Presente** (estado exacto de los *lockfiles* y firmas hash actuales) y **Futuro** (alertas de deprecación inminentes o *breaking changes* advertidos en versiones *upstream*).

---

### Fase 2: Autocorrección y Bucle Cerrado (The Ouroboros Loop)
**Objetivo:** El agente debe arreglar sus propios errores de compilación sin intervención humana.

* **[ ] Hito 2.1: Sandboxing Efímero (Micro-VM / Docker-in-Docker)**
  * **Descripción:** Despliegue de un arnés de ejecución asilado.
  * **Entregable:** El enjambre Legión puede compilar y testear código no confiable dentro de un contenedor desechable.
* **[ ] Hito 2.2: Bucle de Retroalimentación de Pruebas**
  * **Descripción:** Orquestador iterativo acoplado a `cargo test -p babylon60-kernel` y `[OBSOLETO: pytest]`.
  * **Entregable:** Si un test falla, el agente lee el *stack trace*, parchea el código semánticamente vía LSP, y repite la prueba hasta alcanzar un estado verde (Pass) o agotar el umbral termodinámico ($N$ iteraciones máximas).

---

### Fase 3: Razonamiento Búsqueda en Árbol (MCTS + PRM)
**Objetivo:** Abandonar la fuerza bruta lineal y adoptar planificación SOTA.

* **[ ] Hito 3.1: Modelo Local de Evaluación de Recompensas (PRM)**
  * **Descripción:** Despliegue de un pequeño modelo local (ej. Llama-3-8B-Instruct o Qwen-Coder-7B) dedicado exclusivamente a puntuar la validez de los pasos lógicos.
  * **Entregable:** Un servidor local (Ollama / vLLM) que expone un endpoint `/score_step`.
* **[ ] Hito 3.2: Sustitución de Legión 222 por MCTS Runner**
  * **Descripción:** Reescribir la orquestación estática en un árbol de búsqueda Monte Carlo (Monte Carlo Tree Search).
  * **Entregable:** El agente orquestador genera múltiples vías de refactorización (ramas). El PRM evalúa y poda las ramas que violan invariantes C5-REAL o causan fallos de compilación, encontrando la solución óptima antes de inyectarla al Ledger.

---

### Fase 4: Autonomía Evolutiva y Consolidación Causal
**Objetivo:** El sistema aprende y consolida el conocimiento permanentemente.

* **[ ] Hito 4.1: Auto-Síntesis de Skills Dinámicas**
  * **Descripción:** Otorgar permisos al agente para ejecutar recursivamente `cortex-skill-genesis`.
  * **Entregable:** Cuando el agente identifica un patrón repetitivo, escribe su propio script Python, genera un `SKILL.md` y registra la nueva herramienta MCP al vuelo.
* **[ ] Hito 4.2: Compilador "Dream to Ledger"**
  * **Descripción:** El puente final que reconcilia la alta entropía con el determinismo.
  * **Entregable:** Un módulo en Rust que toma el parche SOTA generado (ya verde en tests y optimizado por MCTS), lo formatea bajo los invariantes de `Babylon.lean`, y lo inyecta como una transición de estado inmutable en el DAG Ledger $F_{60}$ (COSE Sign1 + TPM).

---

### Fase 5: Auto-Evolución Arquitectónica (The SOTA Self-Implementation Loop)
**Objetivo:** El sistema debe auditar la literatura de frontera (arXiv, GitHub trending) y auto-actualizar sus propios paradigmas de orquestación sin esperar parches humanos.

* **[ ] Hito 5.1: Oráculo de Inteligencia Tecnológica (SOTA Watchdog)**
  * **Descripción:** Agente programado en cron (`[OBSOLETO: schedule]`) que monitorea repositorios SOTA, papers de arXiv y benchmarks (SWE-bench).
  * **Entregable:** Matriz automatizada que detecta avances en IA agentiva (p.ej. un nuevo protocolo RAG o heurística MCTS).
* **[ ] Hito 5.2: Bucle de Implementación Reflexiva (Reflexive Forking)**
  * **Descripción:** Cuando se detecta un salto SOTA, el sistema hace un *fork* de sí mismo dentro del *Dream State*.
  * **Entregable:** El agente orquestador intenta refactorizar su propio código de enjambre (p.ej. reemplazar su indexador base por el nuevo paradigma), ejecuta su batería de pruebas `[OBSOLETO: pytest]`/`cargo test` y, si supera el benchmark interno, somete un *Pull Request* autónomo o un `Dream to Ledger` commit para actualizar su propio kernel agentivo.

---

## 📈 Criterios de Aceptación Global (Definition of Done)
1. **Velocidad de Iteración:** El sistema puede resolver un ticket complejo de refactorización (tipo SWE-bench) de forma 100% autónoma.
2. **Cero Anergía Causal:** Ningún código defectuoso o no verificable toca el WORM Ledger ni la red principal. Todo el fallo de la alucinación queda confinado en la Micro-VM.
3. **Escalado Horizontal:** Múltiples agentes en el Dream State pueden probar diferentes soluciones MCTS en paralelo sin corromper el árbol de estado principal.
