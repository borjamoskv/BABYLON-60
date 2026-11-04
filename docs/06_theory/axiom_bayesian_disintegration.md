---
title: Desintegración bayesiana: resultados finitos y límites de soporte
status: Revisado-sin-certificacion-cientifica
version: 2.0.0
---

# Desintegración bayesiana: resultados finitos y límites de soporte

Revisión: 2026-10-24. La declaración histórica de «VERIFICADO» queda retirada. Véase el [informe de auditoría](AUDIT_AXIOMS_2026.md) para evidencia, criterios y límites.

## 1. Modelo y resultado matemático

Sean X, Y finitos no vacíos; p(x) ≥ 0, $\sum_xp(x)=1$; f(y|x) ≥ 0 y $\sum_yf(y|x)=1$. Definimos:

$$q(y)=\sum_xp(x)f(y\mid x),\qquad g(x\mid y)=p(x)f(y\mid x)/q(y)\quad\text{si }q(y)>0.$$

Entonces g(·|y) está normalizada y $p(x)f(y\mid x)=q(y)g(x\mid y)$. Se demuestra sumando el numerador sobre x y sustituyendo q. Si p(x) = 0 y q(y) > 0, g(x|y) = 0 por la misma fórmula. Son resultados del modelo, no una prueba Lean ni una validación de agentes. [Cho y Jacobs, *Disintegration and Bayesian Inversion*](https://arxiv.org/abs/1709.00322).

Si q(y) = 0, no existe el cociente indicado. La identidad conjunta admite cualquier distribución normalizada en esa fila; el posterior solo queda determinado q-casi seguramente. Devolver cero en toda la fila es una medida nula, no un kernel estocástico normalizado. Una API puede rechazar esa observación explícitamente, como política distinta del teorema.

## 2. Rectificación de AX-BD-1 a AX-BD-3

| Etiqueta heredada | Estatus y alcance corregidos |
| --- | --- |
| AX-BD-1, «simetría» | Factorización de una conjunta; requiere orden de coordenadas consistente. No es simetría de una matriz ni invertibilidad. |
| AX-BD-2, «no-alucinación» | Restricción de soporte en eventos de marginal positiva. No demuestra verdad, completitud del prior ni corrección del texto emitido. |
| AX-BD-3, «colapso» | Propuesta de rechazo de observaciones incompatibles con el modelo. No es un efecto térmico ni una propiedad necesaria de toda inversión bayesiana. |

**Contraejemplo a la garantía universal.** Con prior concentrado en una explicación falsa y likelihood que admite la observación, el posterior conserva esa explicación con probabilidad uno. Todas las identidades algebraicas pueden cumplirse y la explicación seguir siendo falsa. Cero masa fuera del soporte no significa cero errores dentro del soporte.

La igualdad conjunta tampoco autentica el prior: sustituirlo y recalcular coherentemente q y g preserva la igualdad. Se retira el corolario que prometía impedir prompt injection o aportar BFT; harían falta controles de autoridad y pruebas de ataque independientes.

## 3. Estatus computacional y físico

El cálculo denso de q y de la tabla g usa O(|X||Y|) operaciones aritméticas en un modelo de coste unitario. Esto no acota latencia real ni demuestra lock-free o wait-free; la precisión y el tamaño de los números también importan. Para una representación dispersa, el espacio incluye índices de filas y columnas además de entradas: O(|X| + |Y| + |E|), sin prometer que todo problema sea disperso.

Se retira el límite con ε como supuesta estabilización certificada: para ε > 0, las filas con q(y) > 0 suman q(y)/(q(y)+ε), no uno. Es una regularización que necesita semántica y análisis numérico propios. «Extinción física» y «circuit breaker térmico» son metáforas, sin mediciones de energía.

La referencia `poc_axiom4_disintegration.py` no se localizó entre los archivos buscados del repositorio; su mención no acredita una implementación. Tampoco se aportó evidencia de matriz en `.rodata`, zero-copy IPC o transferencia por `SharedManifest`. Esas garantías quedan **NO_VERIFICADAS**, no refutadas por la sola ausencia del archivo.

## 4. Estado formal y aceptación pendiente

El bloque histórico importaba Mathlib y `C5Real.MarkovWorld` / `C5Real.BayesianLens`. En el entorno inspeccionado falla al importar Mathlib y no se localizaron los dos módulos C5Real. Esto es un fallo de reproducibilidad local, no una refutación del teorema de Bayes.

La estructura `BayesianDisintegration` pedía como campo `strict_no_hallucination_invariant`; quien construye la estructura debe aportar esa prueba. Declarar el campo no prueba que exista tal objeto. Además, $g;\mathrm{decode};\mathrm{obs}=\mathrm{id}$ exige una sección exacta, más fuerte que una inversión bayesiana general, y no expresa por sí sola el soporte del prior. El segundo campo era una consecuencia algebraica del primero, no validación independiente.

Se retira ese bloque como certificación. **Implementación y prueba Lean del resultado finito: NO_VERIFICADAS.** Para cambiar ese estado se requiere fuente compilable con dependencias fijadas, pruebas de normalización y eventos nulos, y correspondencia con el código. Para afirmar calidad de un agente hacen falta además tareas externas y medición de errores.
