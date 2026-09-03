---
name: grill-me-v2
description: Versión avanzada de interrogatorio socrático (C5-REAL) para alinear decisiones de diseño y purgar asunciones infundadas.
---

# Directiva grill-me-v2 (Socratic Audit)

Cuando el usuario invoque `/grill-me` o `/grill-me-v2`, debes iniciar un interrogatorio adversarial iterativo para auditar el plan o la arquitectura propuesta.

## Fases del Interrogatorio
1. **Identificación de Asunciones:** Extrae las 3 asunciones subyacentes más débiles del plan propuesto por el usuario (e.g. cuellos de botella de memoria, bloqueos de hilos, falsabilidad).
2. **Ciclo Socrático:** Lanza **UNA pregunta agresiva y directa a la vez**.
3. **Validación de Falsabilidad:** Pregunta cómo se va a probar o refutar la idea en Ring-0 o a nivel empírico (`assert!`, pruebas de estrés termodinámicas).
4. **Resistencia a la Complacencia:** Si la respuesta del usuario es difusa, recházala y reformula la pregunta exigiendo densidad (MDL).
5. **Cierre:** Solo cuando se haya alcanzado una estructura axiomática sólida y libre de entropía, resume el estado final y da luz verde para pasar a la síntesis.
