---
name: c5-ctm-formal-architect
display_name: Arquitectura Formal y Diseño Empírico de Cognitive Transition Machines
  (CTM)
description: Módulo Ring-0. Dispara con "ctm benchmark", "ctm formalization", "lean
  4 ctm", "abduction vs deduction", "falsification matrix", "refinement trace".
role: arquitecto
allowed_roles:
- arquitecto
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# c5-ctm-formal-architect

> **Directiva Declarativa:** Alias compatible; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-ring0-babylon-kernel/references/modules/c5-ctm-formal-architect/MODULE.md) antes de aplicar esta habilidad.
El módulo conserva íntegros el frontmatter, los triggers, las instrucciones y los recursos.
Aplica su rol, restricciones y procedimiento únicamente a la tarea solicitada.

## Recursos y rutas

Los recursos originales permanecen en esta carpeta y también se conservan dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas originales continúan siendo válidas.

## Selección

Este alias conserva el nombre original y sus frases de activación.
Para selección explícita usa `/c5-ctm-formal-architect`.
Para consultar el hub usa `/c5-ring0-babylon-kernel`.
No cargues otros módulos sin relación con la petición.
