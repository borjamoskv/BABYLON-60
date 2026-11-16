---
name: c5-enki-60
display_name: Motor Aritmético de Precisión Sexagesimal ENKI-60
description: Módulo Ring-0. Dispara con "enki", "enki-60", "cálculo sexagesimal",
  "aritmética base 60", "precisión sexagesimal".
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

# c5-enki-60

> **Directiva Declarativa:** Alias compatible; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-ring0-babylon-kernel/references/modules/c5-enki-60/MODULE.md) antes de aplicar esta habilidad.
El módulo conserva íntegros el frontmatter, los triggers, las instrucciones y los recursos.
Aplica su rol, restricciones y procedimiento únicamente a la tarea solicitada.

## Recursos y rutas

Los recursos originales permanecen en esta carpeta y también se conservan dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas originales continúan siendo válidas.

## Selección

Este alias conserva el nombre original y sus frases de activación.
Para selección explícita usa `/c5-enki-60`.
Para consultar el hub usa `/c5-ring0-babylon-kernel`.
No cargues otros módulos sin relación con la petición.
