# ⚙️ Tools — Herramientas de Frontera y Protocolos de Oráculo

> **DOMINIO DE AUDITORÍA Y PUENTES**  
> Ubicación: `tools/`  
> Invariante: **Oráculo de Verificación Epistémica**

Este directorio contiene utilidades operacionales y scripts de diagnóstico avanzados para detectar brechas de anergía, alucinaciones (Existence Gap) y tender puentes hacia subagentes externos o telemetría forense.

## 📐 Catálogo de Oráculos

| Herramienta | Propósito Funcional |
|---|---|
| `existence_gap.py` | Auditoría de *Existence Gap* (Imports/símbolos fantasmas, alucinaciones C5-REAL). Evalúa repositorios e inyecta fricción ante slopsquatting. |
| `kimi_bridge.py` | Orquestador MCP / puente hacia Moonshot AI (Kimi) y enjambres multi-agente dinámicos. |
| `audit/` | Scripts complementarios de auditoría de deuda técnica, métricas SAST y verificación forense. |
| `attestation/` | Utilidades criptográficas para generar y verificar atestaciones SHA3-256 de scripts L5. |
| `Anergy_Audit.yml` | Workflow o especificación de Pipeline de Purga Térmica. |

## 🛡️ Reglas Arquitectónicas (C5-REAL)
- Las herramientas L5 de atestación no deben poseer estado (Stateless). Deben ingerir un payload, verificar la matemática y emitir un hash o exit_code (0/1).
- Toda auditoría producida por este directorio debe emitir sus fallos bajo el log de *Fricción Termodinámica*, provocando un Halt seguro si se requiere.
