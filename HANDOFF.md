# HANDOFF DE SESIÓN: CORTEX PTC, Deterministic Tool Pruning & Ralph Handoff (DSH Transfer)

> **Fecha:** 2026-11-07
>
> **Workspace:** `/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60` (branch `main`)
>
> **Estado:** 40/40 tests unitarios y de integración en silicio (17 en `tests/test_cortex_ptc_ralph.py` en 0.71s + 23 en `tests/test_cortex_memory_mcp.py` en 10.63s con broker nativo `libbabylon60.dylib`). Interoperabilidad verificada con DeepSeek Harness Real `0.2.2-rc.1` sobre proyector BLAKE3 `/2` y cliente oficial `@modelcontextprotocol/client@2.4.0`. Commits `[AX-28]..[AX-33]` sellados y sincronizados con `origin/main` en la bóveda privada `BABYLON-60-VAULT`.

---

## 🎯 Objetivo de la Sesión

Transferir, integrar y verificar empíricamente en silicio las primitivas de alta exergía descubiertas durante la auditoría forense in-memory de **DeepSeek Harness `0.2.2-rc.1` (`mac-arm64`)** hacia el motor de `BABYLON-60`:
1. **Podado Determinista de Salidas de Herramientas (`prune_tool_result`):** Recorte *replay-safe* libre de modelo (`threshold_chars=8192`, `head_chars=4096`, `tail_chars=1024`) con marcador canónico `\n\n[... tool result middle pruned ...]\n\n`, integrado en `CortexMCPServer._handle_tools_call` con soporte de opt-out/configuración vía `_meta["babylon60/prune"]`.
2. **Proyección Tipada para Programmatic Tool Calling (`render_mcp_tools_sdk_py`):** Generador de stubs Python `class ToolsSDK(Protocol)` que omite esquemas JSON Schema verbosos del prompt y permite a los agentes ejecutar llamadas directas vía código, expuesto vía CLI y API programática `emit_ptc_sdk()` en `cortex_memory_mcp` y `cortex_mcp_server`.
3. **Guardia de Colisión de Ámbito de Escritura (`scopes_overlap`):** Detección determinista de solapamiento jerárquico de rutas (`write_scope`) en `_tool_blackboard_dispatch` para impedir que agentes concurrentes publiquen propuestas `PATCH_PROPOSAL` sobre directorios o archivos en conflicto.
4. **Contrato de Handoff de Ronda Fresca (`validate_ralph_handoff`):** Validación estricta del contrato de handoff de subagentes (`continue` / `complete` / `blocked`, $\le 16\text{ KiB}$) en `_tool_blackboard_dispatch` (`operation="handoff"`).
5. **Inspector Forense In-Memory y Archivo Canónico:** Materialización de `scripts/forensics/c5_dsh_inspector.py` con la fórmula exacta de alineación Chromium Pickle a 4 bytes ($\text{base} = 8 + u_2 = 16 + ((\text{json\_size} + 3) \mathbin{\&} \sim 3)$) y archivo del reporte forense en `docs/security/c5-deterministic-audit.json`.
6. **Atestación de Interoperabilidad con DSH Real (0.2.2-rc.1):** Validación de overlay Cordis en DSH CLI (`dsh web --patch ... --dump-config`), prueba live de dos sesiones con sonda TypeScript y verificación de proyector BLAKE3 `/2`.

---

## ✅ Delta Exergético Verificado en Silicio (`[AX-28]..[AX-33]`)

### 1. Commits Sellados y Desplegados a `origin/main` (`BABYLON-60-VAULT`)
- **`23aba1d5`** `[AX-28] feat(mcp): wire deterministic tool pruner and --emit-ptc-sdk in CortexMCPServer`
- **`ea83a8e6`** `[AX-29] feat(mcp): enforce scopes_overlap write-scope collision guard in blackboard_dispatch`
- **`4abf17e9`** `[AX-30] feat(mcp): enforce validate_ralph_handoff gate in blackboard_dispatch`
- **`41a5a2eb`** `[AX-31] docs(security): archive DSH 0.2.2-rc.1 deterministic audit and document blackboard handoff op`
- **`7f3c87d6`** `[AX-32] docs(handoff): document DSH PTC/Ralph transfer, deterministic pruner and blackboard gates`
- **`4841f48b`** `[AX-33] feat(mcp): expose programmatic emit_ptc_sdk in cortex_memory_mcp and verify DSH real interop`

### 2. Componentes Implementados y Endurecidos
- `01_KISH_ENGINE/babylon60/mcp/cortex_ptc_ralph.py`: Biblioteca central de primitivas (`prune_tool_result`, `validate_ralph_handoff`, `RalphRoundReport`, `scopes_overlap`, `normalize_write_scope`, `render_mcp_tools_sdk_py`).
- `01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py`: Función `emit_ptc_sdk(include_write)` y subcomando CLI `emit-ptc-sdk` con bandera `--include-write`.
- `01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py`: `_prune_tool_response` para lecturas y efectos, CLI `--emit-ptc-sdk`, guardia `WRITE_SCOPE_COLLISION` en `blackboard_dispatch(publish, PATCH_PROPOSAL)` y compuerta `blackboard_dispatch(handoff)`.
- `scripts/forensics/c5_dsh_inspector.py`: Inspector determinista ASAR/DMG con comprobación de `integrity.hash` (SHA-256).
- `docs/security/c5-deterministic-audit.json`: Volcado completo de la auditoría forense v2 de `deepseek-harness-0.2.2-rc.1`.
- `tests/test_cortex_ptc_ralph.py`: 17 tests unitarios y de integración cubriendo podado, handoff, rutas, stubs CLI y blackboard.

---

## 🔬 Atestación de Interoperabilidad con DeepSeek Harness Real (0.2.2-rc.1)

### 1. Clave Efímera y Binding de Autoridad
- Generación con Ed25519 en `~/.cortex-memory/`:
  - `op.key` (clave privada del operador, 0600) y `op.key.pub` (0644).
  - `writer.json` firmado con actor `dsh-desktop`, proyecto `babylon60`, y capacidades completas `["read", "append", "supersede", "forget"]`.

### 2. Interoperabilidad Live con Proyector BLAKE3 (`/2`)
- Ejecución de `scripts/cortex_memory/sdk_ab_probe.mjs` bajo `@modelcontextprotocol/client@2.4.0` (el cliente exacto integrado en `@deepseek-ai/dsh-mcp-client`):
  - **Sesión A (Escritura):** Invocación de `memory_append` (`request_id="sdk-<suffix>"`, `value="validation drink is lapsang-<suffix>"`).
    - Resultado: `status="committed"`, `replayed=false`, `seq=7`, `entry_hash` BLAKE3 `/2`.
  - **Sesión B (Lectura Limpia):** Invocación de `memory_read` (`text="lapsang-<suffix>"`).
    - Resultado: `receipt.projector_version="cortex-memory-projector/2"`, `receipt.delivery="recorded_before_send_unconfirmed"`, `view_digest` y `snapshot_state_digest` coincidentes.
    - `served_by.instance_id` distinto entre sesión A y B (aislamiento de proceso verificado).
    - Veredicto: **`ok: true`**. Resuelve y sustituye definitivamente la nota histórica anterior que limitaba la evidencia fresca a SHA3 `/1`.

### 3. Validación de Overlay Cordis en DSH CLI
- Ejecución de `dsh web --patch config/dsh/cortex-memory.cordis.yml --dump-config` sobre el ejecutable nativo de DSH `0.2.2-rc.1`:
  - Salida con código 0.
  - Inyección verificada de `memory-cortex` en la raíz del árbol Cordis junto al runtime `@deepseek-ai/dsh-compaction-tool-result-pruner` (`thresholdChars: 8192`, `headChars: 4096`, `tailChars: 1024`) y `@deepseek-ai/dsh-workflow-ptc`.

### 4. Podado Determinista y Proyección PTC SDK
- **Podado:** Reducción determinista de salida de 20.000 caracteres a 5.159 caracteres ($4096 + 39 + 1024$) con marcador `\n\n[... tool result middle pruned ...]\n\n`.
- **PTC SDK:**
  - `cortex_memory_mcp emit-ptc-sdk --include-write` $\to$ genera `ToolsSDK(Protocol)` tipado con `memory_read`, `memory_append`, `memory_supersede`, `memory_forget`.
  - `cortex_mcp_server --emit-ptc-sdk` $\to$ genera `ToolsSDK(Protocol)` tipado con las 13 herramientas de Kish Engine sin sobrecarga de JSON Schema.

---

## 📊 Matriz de Verificación en Silicio

| Gate / Suite | Comando | Resultado |
| :--- | :--- | :---: |
| **PTC / Ralph Tests** | `uv run --locked pytest tests/test_cortex_ptc_ralph.py -q` | **17 passed** (0.71s) |
| **CORTEX Memory Tests** | `CORTEX_MEMORY_BROKER_LIB=... uv run --locked pytest tests/test_cortex_memory_mcp.py -q` | **23 passed** (10.63s) |
| **Kish MCP Tests** | `uv run --locked pytest tests/test_cortex_mcp_server.py -q` | **19 passed** (1.73s) |
| **Ruff Linter** | `uv run --locked ruff check 01_KISH_ENGINE/babylon60/mcp/` | **All checks passed!** |
| **Contratos Semánticos** | `python scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only` | **PASS** |
| **Presupuesto Tokens** | `python scripts/c5_quality_gates/audit_token_budget.py --workspace-only` | **PASS** (8.772 B / 40.000 B) |
| **Topología Activa** | `python scripts/guards/verify_active_topology.py` | **PASS** |
| **DSH Probe Live** | `node sdk_ab_probe.mjs ...` (@modelcontextprotocol/client 2.4.0) | **`ok: true`** |

---

## 📜 HISTORIAL PREVIO (Sesión CORTEX Memory MCP)

<details>
<summary>Desplegar detalles de la sesión previa (CORTEX Memory MCP Adapter)</summary>

# HANDOFF DE SESIÓN: CORTEX Memory MCP Adapter (DeepSeek Harness)

> **Fecha:** 2026-11-06 (Actualizado 2026-11-07 con evidencia fresca /2 en commit `[AX-33]`)
>
> **Workspace:** `/Users/borjafernandezangulo/BABYLON-60` (rama candidata `consolidate/cortex-memory`)
>
> **Estado:** 23/23 tests unitarios y de regresión pasando en silicio. Interoperabilidad live certificada tanto en `/1` (SHA3 legacy) como en `/2` (BLAKE3) con la suite TypeScript oficial `@modelcontextprotocol/client@2.4.0` y DeepSeek Harness Real `0.2.2-rc.1`.

### 🎯 Objetivo
Construir y verificar empíricamente en silicio un adaptador MCP stdio (`cortex_memory_mcp.py`) para DeepSeek Harness (DSH), desacoplando el transporte del LLM respecto a la persistencia inmutable (`CortexPersistLedger`, SQLite WAL, BLAKE3 `/2` por defecto con soporte legacy SHA3-256 `/1`) y el broker de capacidades Rust (`McpCapabilityBroker`), bajo política fail-closed sin dependencias de motores externos (Memorix/Engram).

### ✅ Delta Exergético Verificado en Silicio
- `01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py`
- `01_KISH_ENGINE/babylon60/mcp/cortex_memory_core.py`
- `tests/test_cortex_memory_mcp.py` (23/23 PASS)
- `docs/01_spec/spec_cortex_memory_mcp.md`
- `config/dsh/cortex-memory.cordis.yml` y `cortex-memory-readonly.cordis.yml`
- `scripts/cortex_memory/sdk_ab_probe.mjs`

</details>

---

## 📜 HISTORIAL PREVIO (Sesión v5.1.0 y Swarm)

<details>
<summary>Desplegar detalles de la sesión previa (Saneamiento Release v5.1.0)</summary>

### Commits Atómicos Previos (Touch ID)
- `8e22b9ca` `[AX-19] GOV: Unificar version 5.1.0 y alinear 4 tests con terminologia de evidencia tecnica y congelacion PyPI vigentes`
- `3b78e646` `[AX-20] RELEASE: Compilar manifiesto babylon60.release.v5 reproducible compatible con verify_release`
- `fb48bba4` `[AX-21] RELEASE: Re-sellar v5.1.0 con evidencia fresca ligada a 3b78e646 y verify.sh en verde`
- `22496347` `[AX-22] LICENCIAS: Inyectar semilla Ed25519 exclusiva de test en zero-touch y fijar rechazo sin autoridad`
- `d73e7ecb` `[AX-23] OPSEC: Acotar generic-api-key con allowlists AND tras triaje de 53 falsos positivos`

### Modificaciones en Working Tree Preservadas
- `01_KISH_ENGINE/babylon60/core/moskv_kernel.py`
- `01_KISH_ENGINE/babylon60/cortex/cortex_purge_anergy.py`
- `01_KISH_ENGINE/babylon60/primitives/sandbox.py`
- `scripts/babylon60/gen_oncology_primitives.py`
- `scripts/c5_sharur/sharur_100_full_spectrum_auditor.py`
- `tests/test_swarm100_lot12_*.py`
</details>
