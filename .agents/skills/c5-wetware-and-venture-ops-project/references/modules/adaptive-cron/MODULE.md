---
name: adaptive-cron
display_name: Cálculo de Límite de Disipación Crítica (Adaptive Cron)
description: Resume carga operativa mediante observables verificables y conserva el control de sesión del operador.
  Dispara con "adaptive-cron", "/adaptive-cron", "límite de disipación crítica", "burnout
  cognitivo", "cron adaptativo".
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

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:**
> - **Modo de Acceso a Worktree:**
> - **Fase Causal:**
> - **Contrato Handoff:** Recibe de  $	o$ Despacha a

# Directiva adaptive-cron

## Telemetría operativa y control de sesión
- No inferir estados fisiológicos, fatiga ni riesgo de burnout desde el texto del chat. No emitir diagnósticos sobre el operador.
- Cuando se solicite evaluar la carga, informar solo observables disponibles con fuente y ventana temporal: duración registrada de trabajo, fallos de compilación o tests y telemetría proporcionada explícitamente por el usuario. Declarar los datos ausentes como NO_VERIFICADO; no convertirlos en medidas biológicas.
- La decisión de pausar, continuar o cerrar pertenece al operador. Ofrecer ajustes de carga cuando sean pertinentes, sin cortar unilateralmente la sesión.
- Crear o modificar un cron o recordatorio solo cuando el usuario lo solicite, usando las herramientas de automatización disponibles.
