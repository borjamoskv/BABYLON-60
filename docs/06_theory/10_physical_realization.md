---
title: B60: ejemplos de ejecución y límites de la evidencia
status: Ejemplos-sin-garantia-universal
version: 2.0.0
---

# B60: ejemplos de ejecución y límites de la evidencia

Revisión científica: 2026-10-24. Estatus: **Ejemplos-sin-garantia-universal**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Universalidad no demostrada por un ejemplo

Existe [fibonacci.b60](../../tools/examples/fibonacci.b60). Ejecutar Fibonacci o disponer de saltos y bucles no demuestra completitud de Turing: hacen falta una semántica, recursos idealizados no acotados y una simulación de un modelo universal. Una máquina de estados finita también puede ejecutar versiones acotadas de ese ejemplo.

La universalidad de B60 queda **NO_VERIFICADA en esta revisión**. Rice no prohíbe comprobar ninguna propiedad de ningún contrato particular; excluye ciertos decisores totales sobre todos los programas universales. Tampoco obliga a usar BFT o una arquitectura específica.

## 2. Fuzzing y serialización

Las afirmaciones históricas de millones de casos, «determinismo absoluto» y O(N) no incluyen aquí un registro reproducible ligado a versión, hardware y carga. Se reclasifican como NO_VERIFICADAS. Un fuzzer puede encontrar contraejemplos en una muestra; que no los encuentre no prueba universalidad del determinismo ni inmunidad a efectos físicos.

Ordenar representaciones puede ayudar a canonizar, si son inequívocas y cubren todos los datos pertinentes. No prueba consenso, seguridad de hashes ni semántica del grafo. Ni la completitud Σ₁ ni Chaitin determinan esa decisión de serialización.

## 3. Ejemplo de sincronización de contadores

El programa [counter_sync.b60](../../tools/examples/counter_sync.b60) se ejecuta con `cargo run --locked --bin babylon60-dsl -- tools/examples/counter_sync.b60`. Dos corrutinas intercambian señales `COUNTER_SYNC` y `COUNTER_ACK`, incrementan sus contadores hasta 59 y terminan con `HALT`.

Las regresiones de [babylon60-dsl](../../src/babylon60_tests.rs) cubren el umbral sexagesimal, el máximo observado de R10, el límite de despachos y la sensibilidad del hash a los campos del evento. Las [pruebas del CLI](../../tests/b60_dsl_cli.rs) ejecutan el binario y verifican sus exportaciones locales en directorios temporales; CI ejecuta ambos grupos. Las exportaciones usan el formato `B60-events-v2` y BLAKE3, por lo que sus hashes cambian respecto al formato anterior. Son archivos ordinarios sin firma; `proof.ir` describe eventos y no implica haber ejecutado un comprobador formal.

El ejemplo usa registros `i128` y un planificador cooperativo en un hilo. Su repetibilidad para esta entrada no demuestra propiedades físicas, ausencia universal de bloqueos ni corrección de otros intérpretes.

## 4. Estado formal

Se retira el axioma genérico de validez documental. No se ha demostrado aquí universalidad de B60, seguridad física ni solución de un problema del Milenio. Las fuentes Lean existentes se describen con su alcance acotado en [09_formal_ontology_lean.md](09_formal_ontology_lean.md).
