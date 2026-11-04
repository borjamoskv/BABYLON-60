---
title: Gödel, Rosser y Löb: hipótesis y límites
status: Exposicion-matematica-no-formalizada
version: 2.0.0
---

# Gödel, Rosser y Löb: hipótesis y límites

Revisión científica: 2026-10-24. Estatus: **Exposicion-matematica-no-formalizada**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Diagonalización

Para una fórmula ψ con una variable libre hay una sentencia γ tal que $Q\vdash\gamma\leftrightarrow\psi(\ulcorner\gamma\urcorner)$, con una codificación aritmética adecuada. Es un resultado de sintaxis formal; no demuestra autorreferencia física ni capacidad de un agente de reconocer toda verdad.

## 2. Incompletitud

**Gödel–Rosser:** una teoría consistente, efectivamente axiomatizable y que extienda Q es incompleta. La formulación que solo exige consistencia usa la mejora de Rosser; no debe confundirse con la prueba original de independencia de la sentencia gödeliana bajo condiciones más fuertes. Se retira el diagrama que infería inconsistencia de ambas ramas para la sentencia original sin esas hipótesis. [Rosser (1936), artículo original](https://www.cambridge.org/core/journals/journal-of-symbolic-logic/article/abs/extensions-of-some-theorems-of-godel-and-church/0461E34DC1F219C459EE84CC2FA89068).

Para el segundo teorema damos una condición suficiente explícita: T es una extensión consistente y efectivamente axiomatizable de PA, con predicado estándar de demostrabilidad que satisface las condiciones de derivabilidad. Entonces $T\nvdash\mathrm{Con}(T)$, para la formulación habitual de consistencia. No toda cadena de texto llamada «consistencia» satisface el teorema.

## 3. Condiciones de derivabilidad y Löb

Para el predicado estándar Prov_T se requieren, en las formulaciones correspondientes: internalizar teoremas, distribuir demostrabilidad sobre implicación e internalizar la propia demostrabilidad. Bajo esas condiciones, si $T\vdash\mathrm{Prov}_T(\ulcorner\phi\urcorner)\to\phi$, entonces $T\vdash\phi$.

Esto no prohíbe toda verificación de programas, todo razonamiento externo ni toda mejora de un sistema. Tampoco implica que un humano posea una prueba de su propia consistencia.

## 4. Estatus de la aplicación a BABYLON-60

Separar quien propone y quien verifica es una **decisión de diseño** compatible con límites formales. Gödel no obliga a un protocolo `CRITICAL_HALT`, no demuestra su implementación y no determina una jerarquía de privilegios del sistema operativo. Para trasladar los teoremas hay que identificar teoría, codificación y predicado de demostrabilidad concretos.

Se retira el axioma genérico `document_epistemic_validity`: no formalizaba diagonalización, incompletitud ni Löb. No se aporta aquí una prueba Lean de esos resultados.

## 5. Referencias

K. Gödel (1931), *Über formal unentscheidbare Sätze…*, 38, 173–198; B. Rosser (1936), artículo enlazado; M. H. Löb (1955), *Solution of a Problem of Leon Henkin*, JSL 20, 115–118.
