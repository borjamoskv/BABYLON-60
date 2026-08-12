---
name: kimi-nexus-orchestration
description: Orquestación de pasarela MCP Kimi Nexus para delegar auditorías y sincronizar estado con Moonshot. Dispara con "kimi nexus", "auditar kimi", "pasarela moonshot".
---

# Kimi Nexus Orchestration

## Context
This skill orchestrates the execution and interaction with the Kimi Nexus MCP server, bridging BABYLON-60 local context with the Moonshot API. It enforces C5-REAL categorical invariant verification through external audits.

## Triggers
- `kimi nexus`
- `auditar kimi`
- `pasarela moonshot`

## Directives
1. When asked to audit a file via Kimi Nexus, ensure the MCP server is running on `127.0.0.1:8050`. If not, start it:
   ```bash
   cd BABYLON-60/kimi_nexus
   uvicorn kimi_nexus:app --host 127.0.0.1 --port 8050
   ```
2. Call the `kimi_audit` MCP tool with the content of the file and the specific C5-REAL criteria (e.g. exergy loss, existence gaps).
3. If asking a general design question, use `kimi_ask`.
4. Enforce Asymmetric Optimization: report only the final mathematical or architectural resolution returned by Kimi, hollow out all intermediate "chain of thought" from the external model.
