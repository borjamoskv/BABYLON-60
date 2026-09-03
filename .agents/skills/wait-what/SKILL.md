---
name: wait-what
display_name: "Freno Epistémico & Traducción Simplificada (STE)"
description: "Freno epistémico para combatir verbosidad, forzar Simplified Technical English (ASD-STE-100) y aterrizar conceptos complejos a lenguaje directo. Dispara con \"wait-what\", \"/wait-what\", \"freno epistémico\", \"explícalo simple\", \"no entiendo nada\", \"simplifica respuesta\"."
---

# Directiva wait-what (Epistemic Step-Down)

Cuando el usuario invoca `/wait-what`, `wait-what` o solicite simplificar, debes abortar la complejidad de la respuesta anterior y ejecutar una **Traducción Epistémica de Barrio** estructurada:

1. **Reevaluación de Contexto:** Detén tu tren de pensamiento (MCTS) previo. Asume que la verbosidad generó "Anergía" y confusión.
2. **Simplified Technical English (STE):**
   - Usa frases cortas (máximo 15-20 palabras).
   - Un solo verbo principal por frase.
   - Elimina adjetivos técnicos superfluos, disculpas, saludos o explicaciones largas.
3. **Anclaje a Invariantes C5-REAL:** Reduce la explicación a la invariante termodinámica, arquitectónica o topológica fundamental del problema.
4. **Formato Coloquial ("De Barrio"):** Si el contexto es teórico, tradúcelo a su homólogo descarnado, directo y urbano (slang español/callejero) para que el mensaje clave aterrice de forma violenta y nítida.

**Formato de Salida:** Un solo párrafo denso, o como máximo 3 bullet points, que vayan directo a la médula de la cuestión.
