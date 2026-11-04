---
title: Modelo oncológico propuesto: hipótesis y límites de la analogía
status: Revisado-sin-certificacion-cientifica
version: 2.0.0
---

# Modelo oncológico propuesto: hipótesis y límites de la analogía

Revisión: 2026-10-24. La declaración histórica de «VERIFICADO» queda retirada. Véase el [informe de auditoría](AUDIT_AXIOMS_2026.md) para evidencia, criterios y límites.

## 1. Alcance científico

Se conserva una propuesta de representar entidades y relaciones biológicas mediante grafos. Una lista de 300 clases no constituye una dinámica validada ni implica un espacio de estados finito. «Fricción tumoral», «purga», «transducción bio-silicio» y «anergía» son etiquetas de modelado o metáforas hasta definir observables, unidades y relaciones contrastadas. No se aporta aquí evidencia de eficacia terapéutica ni predicción clínica.

## 2. Rectificación de los postulados

| Postulado heredado | Hallazgo | Estatus corregido |
| --- | --- | --- |
| AX-ONCO-1: toda metástasis deriva de `DDR_Fail` en un DAG | No se aporta prueba de necesidad universal ni grafo causal identificado; un grafo de señalización puede contener ciclos. | Hipótesis de un modelo concreto, NO_VERIFICADA como ley biológica. |
| AX-ONCO-2: fricción monótonamente creciente sin Ω | No se define la fricción ni se mide su derivada. «Estrictamente creciente» tampoco equivale a derivada ≥ 0. | Hipótesis no contrastable hasta operacionalizar la variable; no ley termodinámica. |
| AX-ONCO-3: terapia isomorfa a un circuit breaker | No se definen objetos, morfismos ni inversa que demuestren un isomorfismo. | Analogía de diseño, sin equivalencia terapéutica demostrada. |

Koebel et al. observaron equilibrio de tumores ocultos mediado por inmunidad en un modelo murino, sin una intervención Ω del software. Ese resultado no mide la variable indefinida F_T, pero impide inferir crecimiento universal solo de la ausencia de un operador externo. [Estudio primario, Nature 2007, DOI 10.1038/nature06309](https://pubmed.ncbi.nlm.nih.gov/18026089/).

## 3. Retirada de los supuestos teoremas

El boceto de «control termodinámico» no define una ecuación de evolución, condiciones iniciales ni unidades. De una condición sobre Ω = 0 no se deduce que escoger Ω = k∇F_T invierta la evolución. Aun si un control redujera una función, haría falta probar que eso excluye el estado de metástasis en el modelo. Contar clases no demuestra alcanzabilidad ni estabilidad. **Resultado retirado como teorema.**

La equivalencia $\lim F_T=0\iff\int\Omega\ge\sum\mathrm{Carga}$ tampoco se deriva sin una dinámica y un balance con unidades compatibles. Una intervención acumulada grande puede coexistir con crecimiento o resistencia en otro modelo. Se retira como ecuación universal de remisión; no se propone una fórmula clínica sustitutiva sin datos.

`UNSAT` significa que no hay asignación que satisfaga las restricciones codificadas. Para excluir una trayectoria de un sistema real haría falta justificar una abstracción que cubra sus comportamientos y una codificación correcta. Un resultado SMT no demuestra eficacia farmacológica ni sustituye un ensayo clínico.

## 4. Estado formal

La estructura Lean histórica `OncologyProtocol` contenía como campos `strict_hallmark_causality`, `growing_anergy_principle` y `therapeutic_circuit_breaker`. Son obligaciones asumidas por cualquier instancia, no pruebas de que la biología las satisfaga. No había instancia construida, teorema de estabilidad ni vinculación de datos.

La extracción original falla con Lean 4.35.0 por tipos/clases numéricas sin resolver; no se configuró una dependencia que definiera los reales utilizados. Se retira el bloque como certificación. Reparar imports o tipos solo produciría una especificación condicional, no validación de las hipótesis.

## 5. Evidencia necesaria y relación con la implementación

Antes de validar un modelo hacen falta variables medibles, aristas con evidencia, reglas de actualización, parámetros, incertidumbre y contraste con datos independientes. Un resultado de simulación solo tiene el alcance de su modelo.

El [informe local de integración oncológica](../security/onco-integration-review-2026-10-24.md) describe carencias del grafo y cambios de distribución; se cita como evidencia de integración, no como revisión clínica. Esta auditoría no modifica esos cambios ni certifica el catálogo biológico. **Modelo dinámico, control de progresión y garantías terapéuticas: NO_VERIFICADOS.**
