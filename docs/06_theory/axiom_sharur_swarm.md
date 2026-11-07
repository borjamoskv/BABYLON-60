---
title: Sharur: concurrencia, reducción y supuestos de terminación
status: Especificacion-condicional-no-certificada
version: 2.0.0
---

# Sharur: concurrencia, reducción y supuestos de terminación

Revisión científica: 2026-10-24. Estatus: **Especificacion-condicional-no-certificada**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Modelo propuesto

Sea W un conjunto finito de entradas y α una función que devuelve conjuntos de hallazgos. Limitar trabajadores, auditar una instantánea y recoger errores son requisitos de diseño. Los nombres «1000 agentes», «10k» o «SHARUR-3600» no son conteos activos ni capacidad medida.

Una partición requiere $\bigcup_k W_k=W$ y $W_i\cap W_j=\varnothing$ para todo i ≠ j. La antigua intersección conjunta vacía no implicaba disjunción por pares.

## 2. Resultado de reducción con hipótesis explícitas

Si α es determinista sobre una instantánea fija, cada trabajo termina, todos sus resultados se recogen y la reducción es unión de conjuntos, entonces $V=\bigcup_{w\in W}\alpha(w)$ no depende del orden de llegada. El argumento usa asociatividad y conmutatividad de la unión. No se aplica sin más a listas ordenadas, timestamps, lecturas cambiantes, efectos compartidos o timeouts dependientes de la planificación. Es una derivación matemática condicional, no prueba de un scheduler concreto.

La finitud de W y capturar excepciones **no garantizan terminación**: basta un trabajo que no retorna ni lanza excepción. Exigen además límites o supuestos de terminación, planificación y recuperación. Se retira el corolario de ausencia universal de livelock.

## 3. Recursos y complejidad

La cota de trabajos activos depende de cómo se implemente el pool y de sus presupuestos; no garantiza ausencia de saturación. Trabajos totales, hilos, procesos y peticiones remotas son unidades distintas. Leer sin escribir el árbol auditado tampoco implica «entropía física cero»: hay consumo de recursos y pueden existir otros escritores.

Como estimación ideal, con trabajo total L, p trabajadores y duración máxima l_max, $T_p\ge\max(L/p,l_{max})$; comunicación, contención y planificación añaden coste. No se deduce tiempo constante al crecer W con p fijo, ni el hardware concede un número rígido universal de hilos. La fórmula histórica con límite igual a O(·) se retira como supuesto teorema.

## 4. Estado Lean

La estructura histórica `SharurSwarm` compila como declaración aislada con Lean 4.35.0. Sus campos `strict_concurrency_bound` y `zero_mutability_invariant` son obligaciones suministradas al construir una instancia. `granular_fail_fast` repetía una consecuencia del segundo campo y no modelaba excepciones, aislamiento de procesos ni plazos.

Se retira el bloque como certificado de un enjambre real; no se ha construido aquí una instancia ni probado el scheduler. Un conjunto vacío de hallazgos solo significa que los predicados ejecutados no encontraron casos en su cobertura, no que el repositorio sea correcto globalmente.
