---
title: Complejidad algorítmica: convenciones y límites
status: Exposicion-matematica-no-formalizada
version: 2.0.0
---

# Complejidad algorítmica: convenciones y límites

Revisión científica: 2026-10-24. Estatus: **Exposicion-matematica-no-formalizada**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Convención de complejidad

Fijamos una máquina universal óptima **prefijo-libre** U y $K_U(x)=\min\{|p|:U(p)=x\}$. Para complejidad simple se suele usar C en lugar de K. Cambiar de máquina óptima altera K en una constante aditiva que depende de las máquinas; no lo convierte en un número absoluto independiente del lenguaje.

La cota literal $C(x)\le|x|+O(1)$ es para complejidad simple. Para la variante prefijo-libre una cota uniforme es $K(x)\le|x|+K(|x|)+O(1)$. La no computabilidad de K se demuestra mediante un argumento diagonal de descripción corta; el recuento de programas también da cotas de incompresibilidad, sin medir verdad o utilidad del texto.

## 2. Shannon y aleatoriedad

La entropía de Shannon corresponde a una distribución; K a una cadena y una máquina fijadas. Calcular entropía requiere acceso suficiente a las probabilidades: no toda distribución definida abstractamente es computable. Relaciones entre esperanza de K y entropía requieren hipótesis y términos adicionales; no son identidad universal.

Una secuencia es Martin-Löf aleatoria si supera todos los tests efectivos de medida con cotas decrecientes adecuadas. No basta decir «ningún conjunto enumerable de medida cero». Para K prefijo-libre, la caracterización de Levin–Schnorr usa $K(\alpha\restriction n)\ge n-c$ para todo n y alguna constante c.

## 3. Incompletitud informacional y Ω

Para una teoría efectivamente axiomatizable suficientemente fuerte y aritméticamente correcta, y una máquina óptima fijada, existen límites a las cotas inferiores de complejidad que puede probar. Se explicita corrección aritmética como condición suficiente; no se infiere verdad de una prueba en una teoría arbitraria.

$$\Omega_U=\sum_{p\in\mathrm{dom}(U)}2^{-|p|}.$$

La condición prefijo-libre es esencial para esta probabilidad de parada. Su incompresibilidad y no computabilidad no significan «un bit = un programa». Un prefijo suficientemente conocido permite decidir determinadas paradas acotadas mediante un procedimiento; no se afirma una correspondencia uno a uno ni equivalencia de recursos.

Se retiran «exactamente c_T bits», $c_T\approx K(\mathrm{axiomas})$ como igualdad medible y la idea de que toda verdad no demostrable es más compleja que los axiomas. Las cotas dependen de máquina, teoría y codificación; no miden comprensión de un LLM. Ampliar axiomas puede probar enunciados antes independientes, sin una mejora cuantitativa universal garantizada.

## 4. Analogía termodinámica y BABYLON-60

Trabajo físico, compresión y demostrabilidad no son magnitudes intercambiables. La segunda ley no demuestra no computabilidad ni Gödel, y un hash no preserva toda la información de un historial. La tabla termodinámica histórica se retira como argumento; puede emplearse solo como metáfora declarada.

El bloque `document_epistemic_validity` no formalizaba K ni Ω. Este documento conserva resultados matemáticos con convenciones explícitas, sin certificación Lean o de rendimiento.

## 5. Referencias

G. J. Chaitin (1974), *Information-Theoretic Limitations of Formal Systems*, JACM 21, 403–424, DOI 10.1145/321832.321839. [Informe académico de Calude sobre hipótesis y cotas](https://www.cs.auckland.ac.nz/research/groups/CDMTCS/researchreports/166cris.pdf). No se presenta la metáfora del «horizonte» como una ley de ingeniería.
