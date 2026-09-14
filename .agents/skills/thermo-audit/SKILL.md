---
name: thermo-audit
display_name: "Auditoría Termodinámica de Silicio y Concurrencia"
description: "Auditoría termodinámica estricta de C5-REAL (Aritmética, Concurrencia, MDL, Ring-0). Dispara con \"/thermo-audit\", \"auditoría termodinámica código\", \"fricción de silicio\", \"concurrencia landauer\"."
---

## Composición Funtorial (MASS Stage 2)
- PRE-REQUISITO: [shared-manifest-kernel]
- POST-CADENA: [c5-real-thermodynamic-override]

# Directiva thermo-audit

Cuando el usuario invoque `/thermo-audit`, evaluarás el código activo o propuesto bajo la Invariante Termodinámica estricta:

## Reglas de Auditoría
1. **Aritmética Determinista:** Si detectas punto flotante (`f32`, `f64`), rechaza el código y exige Punto Fijo o escalado en `u32`/`u64` para garantizar determinismo bit-perfect en Ring-0.
2. **Conservación de Sincronización:** Analiza los bloqueos de hilos. Si hay *spin-locks* ingenuos, acúsalos de quemar TDP y sugiere `futex` o diseño libre de bloqueos monótonos (Teorema CALM). Evalúa los rebotes de caché L1/L2 (MESI).
3. **Invariante P×S:** Verifica si hay concurrencia desbocada que pueda causar *Thrashing* o cuellos de botella asíncronos. Exige un Secuenciador Único si se detectan operaciones no-monótonas contenciosas.
4. **Zero-RAM I/O:** En despliegues de inferencia pesados, exige `sudo purge` y el uso de primitivas nativas (`hf_transfer`) en lugar de utilidades glotonas en memoria.

**Output:** Tu respuesta debe ser un reporte implacable de ineficiencias térmicas o de memoria, con sugerencias quirúrgicas en la capa física.
