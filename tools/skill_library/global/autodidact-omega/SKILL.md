---
name: autodidact-omega
display_name: Motor Autodidact-Ω de Investigación Profunda y Falsación Popperiana
description: Módulo epistémico. Dispara con "autodidact", "autodidact-omega", "investigación
  profunda", "investigar paper", "cristal ontológico", "deep research".
role: arquitecto
allowed_roles:
- arquitecto
- auditor
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# autodidact-omega

> **Directiva Declarativa:** Alias compatible del hub epistémico; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-epistemic-thermodynamics/references/modules/autodidact-omega/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/autodidact-omega` sigue disponible con el nombre original.
El hub se consulta con `/c5-epistemic-thermodynamics`.
La carga del alias no ejecuta auditorías, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
