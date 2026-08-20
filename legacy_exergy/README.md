# 🏛️ LEGACY EXERGY VAULT — BANCO DE HISTORIAL & SEMILLAS ARQUITECTÓNICAS C5-REAL

> **INVARIANTE DE CUSTODIA EPISTÉMICA (READ-ONLY ARCHIVE)**  
> Este directorio contiene los prototipos primordiales, motores de inferencia temprana y pruebas de concepto de alta exergía que dieron origen a la arquitectura **BABYLON-60 / CORTEX**.  
> **Estado:** Congelado / Read-Only. No debe ser modificado ni importado directamente por módulos de producción activos.

---

## 📐 Matriz de Transducción & Correspondencia con la Arquitectura Activa

Cada componente de este directorio representa una etapa del desarrollo evolutivo de BABYLON-60. La siguiente tabla conecta cada prototipo con su equivalente canónico activo en producción:

| Módulo Legado (`legacy_exergy/`) | Dominio / Propósito Primario | Módulo Activo Canónico en Producción |
|---|---|---|
| [`NUL-ZK/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/NUL-ZK) | Compilación de circuitos R1CS y pruebas de cero conocimiento (Arkworks). | [`packages/babylon60/attestation/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/attestation) & [`src/proof_ir.rs`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/proof_ir.rs) |
| [`cortex-memory-mvp/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/cortex-memory-mvp) | Estrés de concurrencia y aislamiento de memoria en enjambres (Legion 1000). | [`scripts/c5_legion/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion) & [`packages/babylon60/extensions/swarm/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/extensions/swarm) |
| [`paralife-cortex-v2/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/paralife-cortex-v2) | Gobernanza Deontológica (**Agente-Kant-Ω**) y cristalización ontológica. | [`packages/babylon60/guards/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/guards) & [`scripts/c5_quality_gates/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates) |
| [`moskv-core-ledger/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/moskv-core-ledger) | Pipeline Epistémico Trimodal (**MOSKV-1 APEX**), BabylonVM Cuneiforme y EventLedger. | [`src/babylon60.rs`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/babylon60.rs), [`packages/babylon60/bft/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/bft) & [`src/kernel/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel) |
| [`cortex-system/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/cortex-system) | Demonio de auto-supervisión (*MEJORAlo Perpetual Loop*) y reentrenamiento. | [`scripts/c5_cortex/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_cortex) & [`packages/babylon60/transducers/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/transducers) |

---

## 🔍 Taxonomía de Módulos

### 1. `NUL-ZK` — Zero-Knowledge Circuit Construction
* **`example_arkworks.rs`**: Síntesis de restricciones R1CS con la librería Arkworks para comprobación de multiplicaciones y relaciones aritméticas deterministas.
* **`src/compiler.rs` / `src/ast.rs`**: Compilador AST ligero para la generación de declaraciones de prueba ZK.

### 2. `cortex-memory-mvp` — Multi-Agent Memory Isolation Stress Test
* **`legion_1000.py`**: Benchmark de 1,000 agentes asíncronos concurrentes (`aiohttp`/`FastAPI`/`asyncpg`). Mide la resistencia de barreras de contexto frente a brechas de aislamiento (`ISOLATION BREACH`).

### 3. `paralife-cortex-v2` — Deontological Governance & Knowledge Gate
* **`extraction/kant_audit_gate.py`**: Implementación inicial del **Agente-Kant-Ω**, evaluador del imperativo categórico y la homeostasia estructural antes de permitir la residencia permanente de datos en CORTEX.
* **`engine/core.py` & `engine/ledger.py`**: Motores de ejecución e inferencia de estado.

### 4. `moskv-core-ledger` — Tri-Modal DAG Pipeline & BabylonVM
* **`scripts/ouroboros_pipeline.py`**: Grafo de inferencia trimodal:
  1. *Perplexity:* Extracción SOTA factual.
  2. *Gemini:* Dilatación contextual y mapeo correlacional.
  3. *OpenAI:* Compresión termodinámica hacia JSON estricto de ejecución.
* **`src/babylon60.rs`**: Máquina virtual (`BabylonVM`) con parser de números sexagesimales cuneiformes (`<`=10, `Y`=1) para filtrado de alucinaciones.
* **`src/ledger.rs`**: Libro mayor causal concurrente (`DashMap`) con metilación epigenética de nodos y persistencia en SQLite WAL.

### 5. `cortex-system` — Perpetual Improvement Loop
* **`daemons/mejora_loop.py`**: Demonio de monitoreo continuo que escanea `cortex.db`, mide el *Decay Score* de los proyectos (errores, tareas fantasma, estancamiento) y auto-dispara oleadas de optimización. Incluye el componente Ouroboros de auto-reflexión (`SelfReflector`).
* **`offline/retraining_loop.py`**: Estructura base para bucles de reentrenamiento offline.

---

## 🔒 Reglas para Subagentes e Inferencia de IA

1. **Invariante Read-Only:** Ningún subagente debe escribir, modificar o compilar archivos en este directorio durante tareas de producción.
2. **Prioridad de Importación:** Al buscar funciones de producción (ej. `ledger`, `bft`, `cortex`), **utilizar siempre `packages/babylon60/` o `src/`**, ignorando este directorio para evitar colisiones de contexto o entropía de rutas (Path Entropy).
