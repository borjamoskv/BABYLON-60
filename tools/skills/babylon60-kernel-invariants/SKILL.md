---
name: babylon60-kernel-invariants
canonical_alias: kernel-invariants-audit
description: Audita SPSC, SQLite L0, tiempo causal, LARSA y Rust–Lean. Dispara con
  "kernel-invariants-audit", "babylon60-kernel-invariants".
display_name: Auditoría de Invariantes del Kernel BABYLON-60
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# babylon60-kernel-invariants

> **Directiva Declarativa:** Alias compatible; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/.agents/skills/c5-ring0-babylon-kernel-project/references/modules/babylon60-kernel-invariants/MODULE.md) antes de aplicar esta habilidad.
El módulo conserva íntegros el frontmatter, los triggers, las instrucciones y los recursos.
Aplica su rol, restricciones y procedimiento únicamente a la tarea solicitada.

## Recursos y rutas

Los recursos originales permanecen en esta carpeta y también se conservan dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas originales continúan siendo válidas.

## Selección

Este alias conserva el nombre original y sus frases de activación.
Para selección explícita usa `/babylon60-kernel-invariants`.
Para consultar el hub usa `/c5-ring0-babylon-kernel-project`.
No cargues otros módulos sin relación con la petición.
