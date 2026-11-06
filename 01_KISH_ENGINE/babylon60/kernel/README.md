# ⚡ BABYLON60/KERNEL — Subsistema de Deducción MCP, Confinamiento y Consenso (`01_KISH_ENGINE/babylon60/kernel/`)

> **DOMINIO DEL KERNEL PYTHON (`01_KISH_ENGINE/babylon60/kernel/`)**  
> Ubicación: `01_KISH_ENGINE/babylon60/kernel/`  
> Proporciona la validación de aislamiento de servidores MCP (`mcp_seatbelt_confinement`), síntesis de servidores MCP efímeros con digest `BLAKE3`, cortafuegos neurosimbólico Z3, automatización CDP, conectores de inferencia y utilidades de consenso BFT.

---

## 📐 Catálogo de Módulos

| Módulo | Tipo | Propósito & Capacidades |
|---|---|---|
| [`browser_cdp_engine.py`](browser_cdp_engine.py) | Python / CDP | Motor de control e interacción directa vía Chrome DevTools Protocol (CDP). |
| [`kimi_client.py`](kimi_client.py) | Python / API | Cliente para la pasarela de inferencia Moonshot AI (Kimi) con manejo de errores y reintentos. |
| [`quantum_sync.py`](quantum_sync.py) | Python / VCS | Sincronizador determinista de repositorios con detección de Git y Jujutsu VCS (`jj`). |
| [`bft_consensus.py`](bft_consensus.py) · [`bft_sqlite.py`](bft_sqlite.py) | Python / BFT | Primitivas de consenso y persistencia SQLite para el subsistema BFT. |
| [`bft_db_async.py`](bft_db_async.py) · [`bft_falsification.py`](bft_falsification.py) | Python / BFT | Persistencia asíncrona y evaluación de falsación de proposiciones. |
| [`swarm_orchestrator.py`](swarm_orchestrator.py) | Python / Swarm | Orquestación de enjambres multi-agente en paralelo. |
| [`sovereign_binary_analyzer.py`](sovereign_binary_analyzer.py) | Python / Forensics | Análisis estático e inspección en memoria de binarios ejecutables. |
| [`mcp_deductive_engine.py`](mcp_deductive_engine.py) · [`mcp_lifecycle_manager.py`](mcp_lifecycle_manager.py) | Python / MCP | Deducción de esquemas, apretón de manos stdio y gestión de ciclo de vida de procesos MCP. |
| [`mcp_sandbox_validator.py`](mcp_sandbox_validator.py) · [`mcp_scaffolder.py`](mcp_scaffolder.py) | Python / Sandbox | Confinamiento `sandbox-exec` (Seatbelt en macOS) y síntesis de servidores MCP efímeros con digest `BLAKE3`. |
| [`z3_firewall.py`](z3_firewall.py) · [`ns_z3_firewall.py`](ns_z3_firewall.py) | Python / SMT | Cortafuegos de restricciones SMT en Z3 previo a la admisión de herramientas. |
| [`cognitive_guardrail.py`](cognitive_guardrail.py) · [`grounding_interceptor.py`](grounding_interceptor.py) | Python / Guard | Guardarraíles de validación semántica e intercepción de anclaje empírico. |
| [`devsecops_attest.py`](devsecops_attest.py) · [`native_messaging_host.py`](native_messaging_host.py) | Python / Host | Atestación de artefactos DevSecOps y puente de mensajería nativa. |

---

## 🧪 Pruebas Automatizadas

```bash
uv run --locked pytest tests/test_kernel_native_modules.py tests/test_mcp_deduction.py tests/test_mcp_seatbelt.py -q
```
