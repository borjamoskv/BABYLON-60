# ⚡ SRC/KERNEL — Subsistema Nativo del Kernel de Inferencia & Enjambres

> **DOMINIO DEL KERNEL NATIVO (PYTHON / RUST BRIDGES)**  
> Ubicación: `src/kernel/`  
> Proporciona la infraestructura central para automación web CDP, conectores de LLM externos, consenso BFT, sincronización VCS e inferencia deductiva.

---

## 📐 Catálogo de Módulos del Kernel

| Módulo | Tipo | Propósito & Capacidades |
|---|---|---|
| [`browser_cdp_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/browser_cdp_engine.py) | Python / CDP | Motor de control e interacción directa vía Chrome DevTools Protocol (CDP). Gestiona binarios de Chromium, headless mode y scraping estructurado de DOM. |
| [`kimi_client.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/kimi_client.py) | Python / API | Cliente nativo para la pasarela de inferencia Moonshot AI (Kimi K3) con manejo de llaves y remediación de errores. |
| [`quantum_sync.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/quantum_sync.py) | Python / VCS | Sincronizador determinista de repositorios con auto-detección dual de Git y Jujutsu VCS (`jj`). |
| [`bft_consensus.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/bft_consensus.py) | Python / BFT | Algoritmo de consenso tolerante a fallos bizantinos. |
| [`bft_db_async.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/bft_db_async.py) | Python / Async | Persistencia asíncrona en SQLite para el ledger BFT. |
| [`bft_falsification.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/bft_falsification.py) | Python / Popper | Motor de falsación de proposiciones para el consenso BFT. |
| [`swarm_orchestrator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/swarm_orchestrator.py) | Python / Swarm | Orquestación distribuida de enjambres multi-agente en paralelo. |
| [`sovereign_binary_analyzer.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/sovereign_binary_analyzer.py) | Python / Forensics | Auditoría in-memory y análisis estático de binarios ejecutables. |
| [`mcp_deductive_engine.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/mcp_deductive_engine.py) | Python / MCP | Motor de deducción y validación de esquemas para servidores MCP. |
| [`mcp_lifecycle_manager.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/mcp_lifecycle_manager.py) | Python / MCP | Gestor de inicio, parada y salud de procesos MCP. |
| [`mcp_sandbox_validator.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/kernel/mcp_sandbox_validator.py) | Python / Sandbox | Validación de aislamiento en sandbox para herramientas MCP. |

---

## 🧪 Pruebas Automatizadas

Este subsistema se verifica mediante la suite de tests nativos:
```bash
PYTHONPATH=packages:. pytest tests/test_kernel_native_modules.py
```
