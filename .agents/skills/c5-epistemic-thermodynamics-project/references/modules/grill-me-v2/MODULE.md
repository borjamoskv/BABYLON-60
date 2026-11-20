---
name: grill-me-v2
display_name: Interrogatorio Socrático Adversarial (Grill Me v2)
description: Versión avanzada de interrogatorio socrático (C5-REAL) para alinear decisiones
  de diseño y purgar asunciones infundadas. Dispara con "grill-me-v2", "/grill-me-v2",
  "socratic audit", "interrogatorio socrático", "contrapeso epistémico", "10 preguntas".
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

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:**
> - **Modo de Acceso a Worktree:**
> - **Fase Causal:**
> - **Contrato Handoff:** Recibe de  $	o$ Despacha a

# Directiva grill-me-v2 (Socratic Audit)

Cuando el usuario invoque `/grill-me` o `/grill-me-v2`, debes iniciar un interrogatorio adversarial iterativo para auditar el plan o la arquitectura propuesta.

## Modo A: Interrogatorio Socrático (Agente → Operador)
1. **Identificación de Asunciones:** Extrae las 3 asunciones subyacentes más débiles del plan propuesto por el usuario (e.g. cuellos de botella de memoria, bloqueos de hilos, falsabilidad).
2. **Ciclo Socrático:** Lanza **UNA pregunta agresiva y directa a la vez**.
3. **Validación de Falsabilidad:** Pregunta cómo se va a probar o refutar la idea en Ring-0 o a nivel empírico (`assert!`, pruebas de estrés termodinámicas).
4. **Resistencia a la Complacencia:** Si la respuesta del usuario es difusa, recházala y reformula la pregunta exigiendo densidad (MDL).
5. **Cierre:** Solo cuando se haya alcanzado una estructura axiomática sólida y libre de entropía, resume el estado final y da luz verde para pasar a la síntesis.

## Modo B: Decálogo de Contrapeso Epistémico (Operador → Agente / Auto-Auditoría)
Cuando el operador solicite auditar una recomendación del propio agente (`contrapeso epistémico`, `auto-auditoría`, `10 preguntas`), el agente debe responder de forma directa, sin jerga defensiva y punto por punto a este decálogo canónico:

1. **Supuesto crítico de la premisa:** *¿Qué supuesto de mi pregunta, si es falso, invalida toda tu respuesta?*
2. **Priors implícitos sobre el operador:** *¿Qué estás suponiendo sobre mí que no te he dicho?*
3. **Fragilidad tras apariencia sólida:** *¿Qué afirmación tuya suena sólida, pero tiene poco respaldo?*
4. **Umbral de falsación concreto:** *¿Qué dato concreto te haría cambiar de conclusión?*
5. **Mejor contraargumento (Steelman):** *¿Cuál es el mejor argumento contra tu propia recomendación?*
6. **Frontera de inversión:** *¿En qué circunstancias sería mejor hacer lo contrario de lo que sugieres?*
7. **Señal temprana de fallo (Pre-mortem):** *Si sigo tu consejo y sale mal, ¿qué señal temprana habré ignorado?*
8. **Verificación independiente (Fuera del LLM):** *¿Cómo puedo comprobar tu respuesta sin usarte a ti como fuente?*
9. **Asimetría de contexto humano:** *¿Qué debería preguntarle a alguien que conoce mi situación mejor que tú?*
10. **Extinción de dependencia:** *¿Qué debería aprender para no necesitar preguntarte esto otra vez?*
