---
name: cortex-kernel
canonical_alias: kernel-root
display_name: CORTEX Root Kernel
description: Manifiesto de invariantes transversales del ecosistema CORTEX (árbol de roles, gobernanza declarativa y límites termodinámicos).
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

# cortex-kernel

> **Directiva Declarativa:** Nodo Raíz de Invariantes y Gobernanza del Ecosistema CORTEX.

Consulta la especificación de arquitectura central en [spec_architecture.md](../../../docs/01_spec/spec_architecture.md) y los contratos de ejecución en [AGENTS.md](../../../AGENTS.md). Este módulo define la raíz ontológica de la flota de habilidades y gobierna la separación estricta entre intención estocástica y autoridad determinista. La carga no autoriza efectos externos.
