---
name: c5-ring0-babylon-kernel-project
canonical_alias: kernel-hub
display_name: Kernel Hub · Ring-0 BABYLON (Proyecto)
description: 'Enruta módulos BABYLON-60 del proyecto: SPSC, SQLite L0, arquitectura IDE, SharedManifest, launchd, Apple Silicon y auditoría de contención. Dispara con "kernel-hub", "babylon kernel hub", "shared manifest", "thermo-audit", "rlhf sentinel", "apple-bypass".'
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

## Módulos de ámbito workspace

| Módulo íntegro | Nombres y triggers conservados |
| --- | --- |
| [babylon60-kernel-invariants](references/modules/babylon60-kernel-invariants/MODULE.md) | `babylon60-kernel-invariants`, `/babylon60-kernel-invariants` |
| [babylon60-architecture](references/modules/babylon60-architecture/MODULE.md) | `babylon60-architecture`, `/babylon60-architecture`, `arquitectura babylon60`, `patrones ide babylon`, `babylon60 ide` |
| [shared-manifest-kernel](references/modules/shared-manifest-kernel/MODULE.md) | `shared-manifest-kernel`, `/shared-manifest-kernel`, `shared manifest`, `seqlock 64b`, `ring-0 shm`, `ipc lock-free` |
| [c5-sovereign-daemon-deployment](references/modules/c5-sovereign-daemon-deployment/MODULE.md) | `c5-sovereign-daemon-deployment`, `/c5-sovereign-daemon-deployment`, `desplegar sovereign daemon`, `launchd rust daemon`, `daemon 24/7` |
| [apple-bypass](references/modules/apple-bypass/MODULE.md) | `apple-bypass`, `/apple-bypass`, `bypass termodinámico`, `evadir jetsam macos`, `liberar memoria mps` |
| [thermo-audit](references/modules/thermo-audit/MODULE.md) | `thermo-audit`, `/thermo-audit`, `auditoría termodinámica código`, `fricción de silicio`, `concurrencia landauer`, `silicon concurrency audit`, `grados de libertad parásitos`, `potencia causal` |
| [rlhf-sentinel](references/modules/rlhf-sentinel/MODULE.md) | `rlhf-sentinel`, `/rlhf-sentinel`, `rlhf sentinel`, `contención de ia`, `fuga de llm`, `quarantine ring-0` |
| [c5-rea-clean-room](references/modules/c5-rea-clean-room/MODULE.md) | `c5-rea-clean-room`, `kernel-rea-clean-room`, `c5-rea`, `/c5-rea`, `rea harness`, `clean-room synthesis`, `disección aot`, `rea-triage`, `rea-unpack`, `rea-decompile` |
