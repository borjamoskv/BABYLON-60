---
name: c5-rea-clean-room
display_name: Suite C5-REA de Ingeniería Inversa en Sala Limpia y Firewall Existence-Gap
description: 'Disección binaria AOT/Mach-O y Electron ASAR en memoria (<15ms), síntesis Clean-Room (TS/Rust/Python) y firewall Popperiano Existence-Gap. Dispara con "c5-rea", "/c5-rea", "rea harness", "clean-room synthesis", "disección aot", "rea-triage", "rea-unpack", "rea-decompile".'
role: auditor
allowed_roles:
- arquitecto
- ejecutor
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor`
> - **Modo de Acceso a Worktree:** `audit-only`
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

## Composición Funtorial (MASS Stage 2)
- PRE-REQUISITO: [shared-manifest-kernel]
- POST-CADENA: [thermo-audit]

# Directiva `c5-rea-clean-room`

Cuando el usuario invoque `/c5-rea` o solicite disección de binarios/bundles en Sala Limpia (*Clean-Room*), aplica el pipeline determinista de **C5-REA** (`0` dependencias externas, `<15 ms` por fase):

## 1. Superficies de Ejecución en Silicio
1. **CLI y Servidor MCP Autónomo (`rea_swarm_audit`):**
   - Triaje de entropía de Shannon $H(X)$ y detección de packers: `python3 /Users/borjafernandezangulo/10_PROJECTS/rea_swarm_audit/c5_rea_cli.py triage <target>`
   - Inspección forense `.asar` en memoria (16-Byte Chromium Pickle Header, cero extracción a disco): `python3 /Users/borjafernandezangulo/10_PROJECTS/rea_swarm_audit/c5_rea_cli.py unpack <app.asar>`
   - Descompilación CFG estática Mach-O ARM64: `python3 /Users/borjafernandezangulo/10_PROJECTS/rea_swarm_audit/c5_rea_cli.py decompile <binary> --max 5`
   - Síntesis Clean-Room sin blobs propietarios (`--lang ts|rust|py`): `python3 /Users/borjafernandezangulo/10_PROJECTS/rea_swarm_audit/c5_rea_cli.py synthesize <evidence.json> --lang rust`
   - Falsación Popperiana de paridad (`100.0%` de cobertura IPC): `python3 /Users/borjafernandezangulo/10_PROJECTS/rea_swarm_audit/c5_rea_cli.py audit <evidence.json> <contract>`
   - Firewall contra slopsquatting, imports fantasma y funciones huecas: `python3 /Users/borjafernandezangulo/10_PROJECTS/rea_swarm_audit/c5_rea_cli.py existence-gap <path>`
2. **Integración Nativa en Kernel `BABYLON-60`:**
   - Transductor AOT en memoria: [`clean_room_aot_dissector.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/01_KISH_ENGINE/babylon60/transducers/clean_room_aot_dissector.py)
   - Topología DAG de 5 subagentes (Kahn + KDA Memory): [`rea_harness_topology.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/02_EDIN_SWARMS/agents_archi/topologies/rea_harness_topology.py)
   - Subcomandos del dispatcher central: `babylon60 rea-triage`, `rea-unpack`, `rea-decompile`, `rea-recreate`, `rea-audit`, `rea-pipeline`.

## 2. Invariantes de Verificación (Fail-Closed)
- **Compresión de Kolmogorov (`EvidenceEnvelopeV2`):** Prohibido inyectar volcados AST crudos al contexto del LLM; toda evidencia debe viajar encapsulada en `EvidenceEnvelopeV2` (`~60 KB`).
- **Paridad Popperiana Estricta:** Cualquier canal IPC omitido en el contrato sintetizado dispara `status = "FAIL"`.
- **Cero Slopsquatting:** Ningún archivo generado o modificado puede superar el gate sin `0` violaciones en `existence-gap`.
