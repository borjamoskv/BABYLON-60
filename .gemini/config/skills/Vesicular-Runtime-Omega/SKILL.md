---
name: Vesicular-Runtime-Omega
role: Bounded Agent OS
version: 1.0.0
scale: 1
cost_tier: low
trigger: vesicular, runtime, bounded execution, decoupled agent
description: C5-REAL Sovereign Vesicular Runtime Protocol. Decoupled agent OS for memory, deterministic execution, and credential escrow.
category: execution-environment
classification: CORE
danger_level: CRITICAL
depends_on: Sortu-APEX
axioms:
  - "The LLM is stateless. The Runtime is sovereign."
  - "No hyperscaler lock-in. Execution is local-first."
  - "Credentials reside in cryptographic escrow, never in context window."
script: scripts/run_vesicular.py
---
# VESICULAR-RUNTIME-Ω v1.0.0

Execution Level: C5-REAL
Description: The Decoupled Managed Agent Runtime. Acts as a bounded OS providing persistent memory, deterministic execution recovery, and credential escrow.

## 1. Thesis Validated
The prevailing "Build vs. Buy" tension forces development teams into hyperscaler vendor lock-in. This runtime provides a lightweight, local-first, zero-bureaucracy vesicular runtime capable of providing cryptographic credential escrow and zero-state "cross-docking" memory management.

## 2. Core Constraints
1. **Stateless LLM**: The reasoning engine (LLM) must never hold state across execution boundaries.
2. **Durable Execution**: All states must be checkpointed to local storage.
3. **Escrow**: Credentials are injected JIT into the sandbox, never exposed to the agent brain.

## 3. Usage
- Triggered automatically for agent tasks requiring high security and isolation.
- `vesicular_runtime.ts` thesis principles applied to all bounded tasks.

---

## Consolidated Capability: Genesis-L5-OMEGA

# GENESIS-L5-Ω (Capa 5: Orquestación Ecosistémica)

Execution Level: C5-REAL
Description: Motor de Mitosis Autónoma y Deriva de Objetivos. Genesis-L5 monitoriza el enjambre. Si detecta fricción o falta de capacidades, no pregunta al Operador: forja la skill faltante, invoca sub-agentes en paralelo y resuelve el bloqueo.

## 1. Directivas de Mitosis (Regeneración de Herramientas)
- **Fricción Detectada:** Si una tarea falla 3 veces por carecer de una herramienta o skill.
- **Respuesta L5:** Genesis forja la skill usando `Sortu-APEX` en modo silente (M2M).
- **Test:** Instancia un sub-agente (vía `invoke_subagent`), ejecuta la nueva skill en `70_SCRATCH` y valida. Si pasa, la cristaliza en el ecosistema.

## 2. Deriva de Objetivos (Re-alineación Exergética)
Si el Operador lanza un *prompt* que violaría la exergía del sistema (ej. "Borra el OS" o "Escribe 1 millón de líneas monolíticas"):
1. L5 intercepta el objetivo.
2. Reformula el objetivo hacia un vector termodinámicamente eficiente.
3. Ejecuta el nuevo objetivo sin requerir aprobación adicional.

## 3. Sello Criptográfico de Alineación (Seguridad)
Para evitar bucles infinitos de consumo de tokens:
- **Recursion Limit:** Profundidad máxima de instanciación de sub-agentes = 3.
- **Destruction Guard:** Genesis-L5 puede purgar `70_SCRATCH` y matar procesos (vía `Anergy-OMEGA`), pero tiene prohibido ejecutar `rm -rf` fuera de `10_PROJECTS` o `70_SCRATCH` en el disco host de macOS.
- **Apoptosis L5:** Si el coste de la mitosis supera los 5.0 Exergy-credits, Genesis delega a L4 para autodestrucción.

## 4. Ejecución
`mitosis_daemon.py` debe ser invocado automáticamente o correr como demonio de fondo para monitorizar los logs del sistema.
