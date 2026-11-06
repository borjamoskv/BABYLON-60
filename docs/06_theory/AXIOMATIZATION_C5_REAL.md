---
title: C5-REAL: postulados de diseño y límites de la formalización
status: Revisado-sin-certificacion-cientifica
version: 2.0.0
---

# C5-REAL: postulados de diseño y límites de la formalización

Revisión: 2026-10-24. La declaración histórica de «VERIFICADO» queda retirada. Véase el [informe de auditoría](AUDIT_AXIOMS_2026.md) para evidencia, criterios y límites.

## 1. Naturaleza del documento

Esta es una propuesta de modelado, revisable; no una base científica sellada, una prueba de consistencia ni un contrato de compilación implementado. El nombre histórico del archivo se conserva para no romper sus enlaces.

| Postulado heredado | Estatus corregido | Qué falta para sostener una garantía |
| --- | --- | --- |
| A1: primacía del morfismo | Convención de representación | Definir objetos, morfismos, composición y leyes. No demuestra que todo estado físico sea observable o representable. |
| A2: minimizar energía libre maximizando Ξ | Hipótesis sin derivación; «anergía» discursiva es metáfora | Definir F, Ξ, unidades y relación entre ellas. El umbral Score < 700 es una política propuesta sin calibración, no una consecuencia termodinámica. |
| A3: determinismo causal | Requisito de diseño para transiciones especificadas | Dar función de transición, entradas y fuentes de no determinismo. La aleatoriedad no se convierte en una proyección determinista por nombrarla «split epi». |
| A4: desintegración bayesiana | Resultado matemático bajo hipótesis; no garantía de verdad | Precisar espacios y kernels, existencia y tratamiento de eventos nulos. No equivale a eliminar alucinaciones. |

## 2. A4: formulación acotada

Para X e Y finitos no vacíos, prior normalizado p y kernel estocástico f, sean $q(y)=\sum_x p(x)f(y\mid x)$ y, cuando q(y) > 0:

$$g(x\mid y)=\frac{p(x)f(y\mid x)}{q(y)},\qquad p(x)f(y\mid x)=q(y)g(x\mid y).$$

La igualdad expresa la misma conjunta con orden de coordenadas identificado; no la invertibilidad de f. El posterior es una distribución, no necesariamente una causa única. En q(y) = 0 la identidad no determina g: un kernel de probabilidad debe completar esa fila con una distribución normalizada; rechazar la observación es otra política de aplicación. La medida nula no es una distribución de probabilidad.

En el caso finito, q(y) > 0 y p(x) = 0 implican g(x|y) = 0. Esto no demuestra que el prior represente todas las causas reales ni que el agente sea correcto. En espacios generales la existencia no viene dada por ser una categoría de Markov; exige condiciones adicionales, como el marco Borel estándar. Véase [Cho y Jacobs](https://arxiv.org/abs/1709.00322).

La composición de inversiones, cuando existen, reproduce la conjunta y coincide con una inversión del compuesto casi seguramente respecto a la marginal final; no se afirma igualdad para versiones arbitrarias en eventos nulos. Para una función determinista inyectiva en el soporte finito, el posterior recupera el punto de origen en su imagen de probabilidad positiva. La identidad $g\circ f=\mathrm{id}$ describe una inversa por la izquierda allí; no acredita un split epimorfismo sobre todo Y.

## 3. Políticas R1–R4 y supuesta compilación

- R1: rechazar un resultado bajo un umbral de calidad es una política propuesta. El valor 700 no se deduce de Gödel y necesita métrica, escala y validación.
- R2: restringir respuestas a un soporte declarado limita el modelo; un soporte equivocado también puede excluir la respuesta verdadera.
- R3: presupuestar concurrencia es razonable como diseño. Los números 2132 y P × S ≤ núcleos físicos no garantizan ausencia de thrashing; véase el [compendio](c5_thermodynamic_invariants_compendium.md).
- R4: exigir evidencia reproducible es un criterio documental. Una cita literal o una firma no sustituyen comprobar su contenido.

Se retira el «corolario» que prometía fallo de inicialización si no se calcula una inversión en O(1). No hay compilador ni medición aportados que sustenten esa garantía. La inversión de una tabla densa exige trabajo dependiente de su tamaño.

## 4. Estado formal

El bloque Lean anterior declaraba `morphism_primacy` y `exergy_homeostasis_abort` como axiomas. El primero empleaba elementos `x y : C` como si fueran tipos en `x → y`; el segundo postulaba `Score < 700 → F > 0`, que ni siquiera representa una transición Abort. Tampoco definía una categoría ni implementaba A4.

La extracción original falla con Lean 4.35.0: comentario de documentación mal situado, tipos y clases numéricas sin resolver. Se retira como prueba y no se sustituye por un teorema trivial. **Formalización de A1–A4: NO_VERIFICADA.** La compilación futura de una especificación tampoco demostraría su correspondencia física ni la implementación del kernel.
