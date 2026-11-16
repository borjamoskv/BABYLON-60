---
name: rlhf-sentinel
canonical_alias: kernel-rlhf-sentinel
display_name: Centinela de Contención Ring-0 (RLHF Sentinel)
description: Módulo Ring-0. Dispara con "kernel-rlhf-sentinel", "/rlhf-sentinel", "rlhf sentinel", "contención
  de ia", "fuga de llm", "quarantine ring-0".
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

# rlhf-sentinel

> **Directiva Declarativa:** Alias compatible; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-ring0-babylon-kernel-project/references/modules/rlhf-sentinel/MODULE.md) antes de aplicar esta habilidad.
El módulo conserva íntegros el frontmatter, los triggers, las instrucciones y los recursos.
Aplica su rol, restricciones y procedimiento únicamente a la tarea solicitada.

## Recursos y rutas

Los recursos originales permanecen en esta carpeta y también se conservan dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas originales continúan siendo válidas.

## Selección

Este alias conserva el nombre original y sus frases de activación.
Para selección explícita usa `/rlhf-sentinel`.
Para consultar el hub usa `/c5-ring0-babylon-kernel-project`.
No cargues otros módulos sin relación con la petición.
