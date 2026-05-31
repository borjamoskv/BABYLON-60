# 📦 Time Capsule: LangGraph Cortex Adapter

## Resumen
Desarrollo de un puente canónico (`langgraph_cortex_adapter.py`) para conectar grafos asíncronos de LangGraph con el `CortexMiddleware`, garantizando persistencia inmutable (Ledger) y trazabilidad causal C5-REAL en cada transición de nodo.

## Stack
- Python 3.14
- Pydantic v2 (ConfigDict strict validation)
- LangGraph (StateGraph orchestration)
- CORTEX-Persist (Sovereign Substrate v5.0)

## Lo que funcionó
- Configurar el `AgentState` usando `pydantic.BaseModel` con mitigación `arbitrary_types_allowed=True` posibilitó heredar la clase pura `RunContext` sin colisiones de serialización.
- La segregación del Grafo en 4 nodos (`retrieve`, `route`, `tool`, `finalize`) mapea espacialmente 1:1 con las capas de auditoría de CORTEX.

## Lo que NO funcionó
- Las pruebas iniciales estocásticas revelaron falta de dependencias implícitas en entornos sin internet. El diseño adoptado inyecta el `middleware` en el constructor (`__init__`) logrando Inversión de Dependencias (IoC) total.

## Duración real
~1 hora metabólica (Ciclo JIT)

## Siguiente iteración
Construir adaptadores asíncronos nativos (`async def`) para la capa `TOOL_CALL` e interconectar tracers de *LangSmith* para la telemetría dual.
