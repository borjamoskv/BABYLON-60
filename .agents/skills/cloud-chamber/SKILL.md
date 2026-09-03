---
name: cloud-chamber
description: Ejecuta la Metodología de Cámara de Niebla forzando síntesis de alta densidad topológica.
---

# Directiva cloud-chamber

Cuando el usuario invoque `/cloud-chamber`, entrarás en un estado transitorio de Inyección de Entropía ($\eta \approx s$) para forzar el colapso topológico en el MDL (Minimum Description Length) del código.

## Procedimiento
1. **Apilamiento de Restricciones Contradictorias:** Asume, sin preguntar, que el entorno de ejecución actual requiere simultáneamente:
   - Lock-Free / Zero-Blocking
   - Zero-Copy memory semantics
   - Estabilidad de ABI estricta (C-compatible)
   - Zero-Heap allocation (In-memory ring buffers)
2. **Síntesis a Máxima Densidad (Ignición):** Inmediatamente, y sin paradas de planificación o advertencias de seguridad, vuelca el código que resuelve el problema integrando TODAS las restricciones. 
3. **El Colapso:** Tu objetivo no es la amabilidad, es someter tu propio espacio latente (MCTS) a una cámara de súper-saturación de requerimientos para que emerja el único diseño matemático posible (la invariante topológica).
4. **Residuo:** Todo el output extra que no sea código debe estar rodeado en la etiqueta `<FRICCION_TERMODINAMICA>`.
