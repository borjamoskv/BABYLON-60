---
name: cortex-skill-composer
display_name: Componedor & Orquestador de Cadenas de Skills
description: Módulo CORTEX. Dispara con "componer skills", "skill chain", "cadena
  de habilidades", "pipeline de skills", "cortex skill composer", "orquestación de
  habilidades", "skill pipeline".
role: arquitecto
allowed_roles:
- arquitecto
- ejecutor
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# cortex-skill-composer

> **Directiva Declarativa:** Alias compatible del hub CORTEX; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-cortex-swarm-orchestrator/references/modules/cortex-skill-composer/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/cortex-skill-composer` sigue disponible con el nombre original.
El hub se consulta con `/c5-cortex-swarm-orchestrator`.
La carga del alias no ejecuta agentes, scripts, purgas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
