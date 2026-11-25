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
1. **CLI y Servidor MCP Autónomo (`rea_swarm_audit`):** dependencia externa, no incluida en la distribución. Preferir las herramientas MCP expuestas en la sesión. Para la CLI, localizar el checkout elegido y fijar `REA_CLI` a la ruta absoluta comprobada de su `c5_rea_cli.py`; consultar su ayuda antes de usar estos ejemplos. Si falta esa dependencia, declarar la vía no disponible y continuar el análisis estático pertinente, sin inventar una ruta del autor.
   - Triaje de entropía de Shannon $H(X)$ y detección de packers: `python3 "$REA_CLI" triage <target>`
   - Inspección forense `.asar`: `python3 "$REA_CLI" unpack <app.asar>`
   - Descompilación CFG estática Mach-O ARM64: `python3 "$REA_CLI" decompile <binary> --max 5`
   - Síntesis Clean-Room sin blobs propietarios: `python3 "$REA_CLI" synthesize <evidence.json> --lang rust`
   - Comparación de paridad IPC: `python3 "$REA_CLI" audit <evidence.json> <contract>`
   - Comprobación de imports y referencias: `python3 "$REA_CLI" existence-gap <path>`
2. **Integración Nativa en Kernel `BABYLON-60`:** requiere un checkout elegido por el usuario; las rutas siguientes se resuelven desde su raíz y no son recursos incluidos en este skill. Verificar que existen antes de utilizarlas.
   - Transductor AOT en memoria: `01_KISH_ENGINE/babylon60/transducers/clean_room_aot_dissector.py`
   - Topología DAG de 5 subagentes (Kahn + KDA Memory): `02_EDIN_SWARMS/agents_archi/topologies/rea_harness_topology.py`
   - Subcomandos del dispatcher central: `babylon60 rea-triage`, `rea-unpack`, `rea-decompile`, `rea-recreate`, `rea-audit`, `rea-pipeline`.

## 2. Invariantes de Verificación (Fail-Closed)
- **Compresión de Kolmogorov (`EvidenceEnvelopeV2`):** Prohibido inyectar volcados AST crudos al contexto del LLM; toda evidencia debe viajar encapsulada en `EvidenceEnvelopeV2` (`~60 KB`).
- **Paridad Popperiana Estricta:** Cualquier canal IPC omitido en el contrato sintetizado dispara `status = "FAIL"`.
- **Cero Slopsquatting:** Ningún archivo generado o modificado puede superar el gate sin `0` violaciones en `existence-gap`.
