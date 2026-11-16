---
name: c5-silicon-stress-suite
display_name: Suite de Estrés Concurrente de Silicio y Enjambres (C5-REAL)
description: Módulo Ring-0. Dispara con "pruebas de estres", "stress test swarm",
  "estres enjambre", "concurrencia de silicio", "stress suite", "poc", "test de estres",
  "estres silicio".
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

# c5-silicon-stress-suite

> **Directiva Declarativa:** Alias compatible; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-ring0-babylon-kernel/references/modules/c5-silicon-stress-suite/MODULE.md) antes de aplicar esta habilidad.
El módulo conserva íntegros el frontmatter, los triggers, las instrucciones y los recursos.
Aplica su rol, restricciones y procedimiento únicamente a la tarea solicitada.

## Recursos y rutas

Los recursos originales permanecen en esta carpeta y también se conservan dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas originales continúan siendo válidas.

## Selección

Este alias conserva el nombre original y sus frases de activación.
Para selección explícita usa `/c5-silicon-stress-suite`.
Para consultar el hub usa `/c5-ring0-babylon-kernel`.
No cargues otros módulos sin relación con la petición.
