# 🤖 Sovereign Spark Agent — Agente Soberano Local MCP

> **DOMINIO DE AGENTES NATIVOS**  
> Ubicación: `src/agents/sovereign_mcp/`  
> Inferencia local soberana de coste marginal cero vía **Ollama** (`llama3.1`) acoplada al protocolo **MCP** (Model Context Protocol).

---

## 📐 Componentes del Agente

| Fichero | Descripción Técnica |
|---|---|
| [`sovereign_spark.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/agents/sovereign_mcp/sovereign_spark.py) | **`SovereignSparkAgent`**: Bucle de eventos asíncrono para inferencia agéntica local en `localhost:11434` con auto-llamada a herramientas MCP (`read_filesystem`, `query_sqlite`). |
| [`mcp_config.json`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/agents/sovereign_mcp/mcp_config.json) | Esquemática de servidores MCP estándar (`@modelcontextprotocol/server-sqlite` y `@modelcontextprotocol/server-filesystem`). |
| [`Makefile`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/src/agents/sovereign_mcp/Makefile) | Automatización de instalación (`make setup`) e inicio del agente (`make start-agent`). |

---

## ⚡ Arquitectura de Inferencia

```
[ Usuario / Event Queue ]
           │
           ▼
[ SovereignSparkAgent (Python) ] ──(Ollama API)──► [ Ollama Local (localhost:11434) ]
           │                                                   │
           ├─► Inyección de Tools MCP                          │
           │                                                   │
           ▼ (tool_calls)                                      ▼
[ Servidor MCP Filesystem / SQLite ] ◄─────────────────────────┘
```

---

## 🛠️ Instrucciones de Despliegue Local

```bash
# 1. Configuración de dependencias (Fricción Cero)
make setup

# 2. Iniciar el agente soberano
make start-agent
```
