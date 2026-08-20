# 🔌 4_INTEGRATIONS — Bridges e Integraciones de Alta Exergía

> **Dominio:** Conectores, Pasarelas y Servidores MCP con Servicios de Inferencia Externa  
> **Ubicación:** `experiments/4_INTEGRATIONS/`

---

## 🛠️ Catálogo de Subproyectos & Integraciones

| Subproyecto | Tecnología | Protocolo | Propósito & Capacidades |
|---|---|---|---|
| [`kimi_nexus/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/experiments/4_INTEGRATIONS/kimi_nexus) | Python / FastMCP / Moonshot API | MCP stdio | Pasarela MCP con Moonshot AI (Kimi K3 / Kimi Swarm) para delegación de tareas, enjambres multi-agente, auditorías cruzadas y detección multilingüe de idioma en tiempo real (`lingua`). |

---

## 📐 Detalles del Subproyecto `kimi_nexus`

### 1. Componentes Clave
* **[`kimi_nexus.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/experiments/4_INTEGRATIONS/kimi_nexus/kimi_nexus.py):** Servidor FastMCP con herramientas `kimi_ask` (consulta directa con inyección de idioma), `kimi_audit` (auditoría popperiana C5-REAL) y `kimi_swarm` (orquestación en enjambre P×S).
* **[`mcp/kimi_ask.json`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/experiments/4_INTEGRATIONS/kimi_nexus/mcp/kimi_ask.json) & [`mcp/kimi_audit.json`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/experiments/4_INTEGRATIONS/kimi_nexus/mcp/kimi_audit.json):** Esquemática MCP registrable para la integración con IDEs.
* **[`test_swarm.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/experiments/4_INTEGRATIONS/kimi_nexus/test_swarm.py):** Runner de prueba para delegación paralela a Kimi K3.
* **[`skills/kimi-nexus-orchestration/SKILL.md`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/experiments/4_INTEGRATIONS/kimi_nexus/skills/kimi-nexus-orchestration/SKILL.md):** Manual de disparo para subagentes y enjambres Kimi.

### 2. Flujo de Ejecución MCP
```
[ Antigravity / Agent ] ──(MCP stdio)──► [ kimi_nexus FastMCP Server ]
                                                  │
                                                  ├─► Detección de idioma (lingua)
                                                  ├─► Formateo de Prompt C5-REAL
                                                  │
                                                  ▼
                                     [ Moonshot AI Kimi K3 API ]
```
