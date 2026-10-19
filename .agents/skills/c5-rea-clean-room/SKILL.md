---
name: c5-rea-clean-room
canonical_alias: kernel-rea-clean-room
display_name: Suite C5-REA de Ingeniería Inversa en Sala Limpia y Firewall Existence-Gap
description: 'Módulo Ring-0. Dispara con "kernel-rea-clean-room", "c5-rea", "/c5-rea", "rea harness", "clean-room synthesis", "disección aot", "rea-triage", "rea-unpack", "rea-decompile".'
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

# c5-rea-clean-room

> **Directiva Declarativa:** Alias compatible; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-ring0-babylon-kernel-project/references/modules/c5-rea-clean-room/MODULE.md) antes de aplicar esta habilidad.
El módulo conserva íntegros el frontmatter, los triggers, las instrucciones y los recursos.
Aplica su rol, restricciones y procedimiento únicamente a la tarea solicitada.

## Recursos y rutas

Los recursos originales permanecen en esta carpeta y también se conservan dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas originales continúan siendo válidas.

## Selección

Este alias conserva el nombre original y sus frases de activación.
Para selección explícita usa `/c5-rea-clean-room` o `/c5-rea`.
Para consultar el hub usa `/c5-ring0-babylon-kernel-project`.
No cargues otros módulos sin relación con la petición.
