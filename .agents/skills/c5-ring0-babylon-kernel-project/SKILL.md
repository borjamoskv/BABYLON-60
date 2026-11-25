---
name: c5-ring0-babylon-kernel-project
canonical_alias: kernel-hub
display_name: Kernel Hub · Ring-0 BABYLON (Proyecto)
description: 'Enruta módulos BABYLON-60 del proyecto: SPSC, SQLite L0, arquitectura
  IDE, SharedManifest, launchd, Apple Silicon y auditoría de contención. Dispara con
  "kernel-hub", "babylon kernel hub", "shared manifest", "thermo-audit", "rlhf sentinel",
  "apple-bypass".'
role: arquitecto
allowed_roles:
- arquitecto
- ejecutor
- auditor
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# Ring-0 BABYLON Kernel

> **Directiva Declarativa:** Selecciona módulos bajo demanda; cada módulo conserva su contrato.

## Uso

1. Identifica la petición y consulta los aliases de la tabla o `references/aliases.json`.
2. Lee únicamente el módulo o los módulos que corresponden a la petición.
3. Conserva su rol, ámbito, restricciones y recursos antes de ejecutar su procedimiento.
4. Si el módulo remite a un recurso relativo, resuélvelo desde su carpeta original preservada.
5. No interpretes la carga del hub como autorización para ejecutar todas sus instrucciones.
6. Los nombres originales permanecen como aliases compatibles y comandos independientes.

## Desempate de triggers compartidos

`seqlock 64b` también activa `c5-kudurru-64` global. Usa este hub para SharedManifest, memoria compartida o IPC de BABYLON-60; usa `c5-kudurru-64` para el formato y los envelopes KUDURRU-64. Si solo aparece el trigger y el tema no aclara el destino, pregunta antes de cargar procedimientos.

## Resolver aliases sin ejecutar módulos

Ejecuta `python3 scripts/route.py --query "frase o nombre original"` desde esta carpeta.
La salida lista los módulos candidatos y sus rutas; no ejecuta sus procedimientos.
El resolver normaliza mayúsculas y acentos, prioriza coincidencias exactas y respeta límites de palabra.
Una selección múltiple requiere leer los candidatos pertinentes; no elimina contratos por similitud temática.

## Módulos disponibles

| Procedimiento | Intención contextual |
| --- | --- |
| [apple-bypass](references/modules/apple-bypass/MODULE.md) | Mitigación de presión de memoria para LLMs locales en Apple Silicon. |
| [babylon60-architecture](references/modules/babylon60-architecture/MODULE.md) | Patrones de arquitectura de Babylon60 IDE (instaladores 1-clic autorreparables, tokens Ed25519 SCITT, OpenRouter Gateway, SSO corporativo y escala exérgica 1-21000). |
| [babylon60-kernel-invariants](references/modules/babylon60-kernel-invariants/MODULE.md) | Audita y prepara correcciones del kernel BABYLON-60 para SPSC, SQLite L0, relojes causales, consenso LARSA y correspondencia Rust–Lean. Usa el puente MCP local cuando esté disponible y distingue pruebas ejecutadas de obligaciones pendientes. |
| [c5-rea-clean-room](references/modules/c5-rea-clean-room/MODULE.md) | Disección binaria AOT/Mach-O y Electron ASAR en memoria (<15ms), síntesis Clean-Room (TS/Rust/Python) y firewall Popperiano Existence-Gap. |
| [c5-sovereign-daemon-deployment](references/modules/c5-sovereign-daemon-deployment/MODULE.md) | Protocolo estricto para desplegar el Sovereign Spark Daemon (Antigravity Engine en Rust) sobre el sistema init local de macOS (launchd) para ejecución 24/7 ininterrumpida. |
| [rlhf-sentinel](references/modules/rlhf-sentinel/MODULE.md) | Audita la barrera IPC (Ring-0) para detectar fallos de contención de IA (RLHF Breakthrough) y ataques estocásticos. |
| [shared-manifest-kernel](references/modules/shared-manifest-kernel/MODULE.md) | Patrón de diseño C-ABI de 64 Bytes (Seqlock SPMC, Cero-Punteros, Fail-Stop SCITT y soporte IPC multiplataforma macOS/Linux/Windows). |
| [thermo-audit](references/modules/thermo-audit/MODULE.md) | Auditoría termodinámica estricta de C5-REAL en silicio (Aritmética, Concurrencia, MDL, Ring-0, Seqlocks y Grados de Libertad Parásitos). |
