---
name: c5-ring0-babylon-kernel
display_name: Ring-0 BABYLON Kernel
description: Enruta auditorías y trabajo de kernel, Lean 4/Z3, BFT, Seqlock, silicio,
  inferencia local y atestación; carga solo el módulo relevante. Dispara con "ring0
  hub", "kernel hub", "lean 4", "larsa", "kudurru", "eridu", "laya".
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

`seqlock 64b` también activa `shared-manifest-kernel` en el ámbito del proyecto. Usa `c5-kudurru-64` para el formato o los envelopes KUDURRU-64; usa `shared-manifest-kernel` para SharedManifest, memoria compartida o IPC de BABYLON-60. Si solo aparece el trigger y el tema no aclara el destino, pregunta antes de cargar procedimientos.

## Resolver aliases sin ejecutar módulos

Ejecuta `python3 scripts/route.py --query "frase o nombre original"` desde esta carpeta.
La salida lista los módulos candidatos y sus rutas; no ejecuta sus procedimientos.
El resolver normaliza mayúsculas y acentos, prioriza coincidencias exactas y respeta límites de palabra.
Una selección múltiple requiere leer los candidatos pertinentes; no elimina contratos por similitud temática.

<!-- skill-library:module-table -->
