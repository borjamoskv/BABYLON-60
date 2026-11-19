---
name: apple-bypass
display_name: Bypass Termodinámico para LLMs en Apple Silicon
description: Mitigación de presión de memoria para LLMs locales en Apple Silicon. Dispara con "apple-bypass", "/apple-bypass", "bypass termodinámico", "evadir jetsam macos", "liberar memoria mps".
role: ejecutor
allowed_roles:
- ejecutor
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:**
> - **Modo de Acceso a Worktree:**
> - **Fase Causal:**
> - **Contrato Handoff:** Recibe de  $	o$ Despacha a

# Directiva apple-bypass

## Presión de memoria y reproducibilidad
El alias histórico no acredita evasión de Jetsam ni inmunidad frente a terminación por presión de memoria.

1. Registrar hardware, memoria disponible, versión del runtime, modelo, cuantización y carga antes de recomendar ajustes.
2. Acotar tamaño de modelo, contexto, lote y concurrencia según mediciones de memoria y criterio de fallo. La preasignación o el reciclaje de buffers son opciones de diseño que deben verificarse en la implementación afectada.
3. No prescribir purgas privilegiadas ni cambios del sistema como requisito general. Respetar el contrato de autorización de todo efecto protegido.
4. Una semilla fija y `temperature=0` ayudan a reproducir una configuración; no prueban determinismo estricto entre dispositivos, versiones o kernels. Separar reproducibilidad de inferencia, orden causal lógico y latencia física.
5. Para comunicar mejoras, ejecutar una comparación reproducible con la misma carga y registrar memoria máxima, latencia, fallos y configuración. No inventar comandos de benchmarks ni certificar resultados sin ejecutarlos.
