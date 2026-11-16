---
name: c5-information-thermodynamics
display_name: Termodinámica de la Información y Geometría Estadística (Fisher-Chentsov)
description: Módulo epistémico. Dispara con "entropía de shannon", "divergencia kl",
  "kullback leibler", "fisher information", "teorema de chentsov", "landauer limit",
  "information geometry", "amari natural gradient", "flujo de wasserstein", "audita
  entropía".
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

# c5-information-thermodynamics

> **Directiva Declarativa:** Alias compatible del hub epistémico; conserva el contrato del módulo original.

## Cargar el módulo

Lee [las instrucciones originales](../c5-epistemic-thermodynamics/references/modules/c5-information-thermodynamics/MODULE.md) antes de aplicar esta habilidad.
Conserva sus triggers, rol, restricciones, procedimiento y alcance.
Carga únicamente los recursos pertinentes a la petición.

## Recursos y rutas

Los recursos originales permanecen junto a este alias y se conservan completos dentro del hub.
Resuelve las referencias relativas desde el archivo del módulo que hayas leído.
Mantén el directorio de trabajo del proyecto elegido por el usuario.
Las rutas absolutas del paquete original continúan disponibles.

## Invocación

El comando `/c5-information-thermodynamics` sigue disponible con el nombre original.
El hub se consulta con `/c5-epistemic-thermodynamics`.
La carga del alias no ejecuta auditorías, scripts, búsquedas ni comunicaciones por sí misma.
El procedimiento del módulo se aplica únicamente dentro del trabajo solicitado.
