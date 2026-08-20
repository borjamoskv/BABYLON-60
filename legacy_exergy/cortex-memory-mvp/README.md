# ⚡ cortex-memory-mvp — Swarm Agent Isolation Stress Test (Legion 1000)

> **ESTADO:** Congelado / Vault Histórico  
> **Transducción en Producción:** [`scripts/c5_legion/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_legion) y [`packages/babylon60/extensions/swarm/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/extensions/swarm)

---

## 📐 Estructura de Ficheros

| Fichero | Descripción Técnica |
|---|---|
| [`legion_1000.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/cortex-memory-mvp/legion_1000.py) | Benchmark de concurrencia y aislamiento estricto de memoria para 1,000 agentes simultáneos. |

---

## 🧪 Metodología del Test de Aislamiento

El script ejecuta un bucle de vida asíncrono (`aiohttp` + `asyncio.Semaphore(500)`):
1. **Generación de Identidad:** Cada agente genera un `agent_id` único e aislado (`legion_agent_<hex>`).
2. **Escritura de Memoria:** Persiste registros telemáticos privados en el endpoint `/memory/add`.
3. **Consulta & Verificación:** Realiza búsquedas vectoriales/contextuales en `/memory/query` y valida que **únicamente** reciba sus propios registros de telemetría.
4. **Detección de Brechas:** Si un agente recupera contexto perteneciente a otro índice, dispara un aviso crítico de `ISOLATION BREACH`.
