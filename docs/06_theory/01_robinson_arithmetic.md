---
title: Aritmética de Robinson: resultados y alcance
status: Exposicion-matematica-no-formalizada
version: 2.0.0
---

# Aritmética de Robinson: resultados y alcance

Revisión científica: 2026-10-24. Estatus: **Exposicion-matematica-no-formalizada**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Sistema Q

Q es una teoría finitamente axiomatizada de primer orden sobre los naturales, sin esquema de inducción. Sus símbolos no lógicos son 0, S, + y ·. Es una teoría débil suficiente para importantes resultados de representabilidad e indecidibilidad; «mínima» no significa que se haya demostrado un mínimo absoluto entre todos los sistemas o codificaciones posibles.

| Axioma | Fórmula, con cierre universal |
| --- | --- |
| Q1 | $Sx\ne0$ |
| Q2 | $Sx=Sy\Rightarrow x=y$ |
| Q3 | $x\ne0\Rightarrow\exists y\ x=Sy$ |
| Q4 | $x+0=x$ |
| Q5 | $x+Sy=S(x+y)$ |
| Q6 | $x\cdot0=0$ |
| Q7 | $x\cdot Sy=(x\cdot y)+x$ |

Son **axiomas definitorios de Q**, no mediciones ni pruebas de BABYLON-60. Q3 no sustituye lógicamente al esquema de inducción.

## 2. Resultados matemáticos con hipótesis

Q demuestra cada sentencia Σ₁ verdadera en el modelo estándar ℕ. Esto permite representar cómputos finitos mediante codificaciones adecuadas; no proporciona un algoritmo total que decida todas las sentencias Σ₁ ni una cota de tiempo lineal. La representabilidad de funciones computables exige especificar la fórmula y la noción de representación; no implica que Q demuestre la totalidad de toda función total computable.

La indecidibilidad esencial afirma que toda extensión **consistente y efectivamente axiomatizable** de Q es indecidible. La omisión de efectividad era un error: la teoría completa de ℕ no es efectivamente axiomatizable. Q no demuestra todas las identidades universales verdaderas de la aritmética, por ejemplo la identidad izquierda de la suma, pese a demostrar sus instancias numerales.

Presburger, con suma y sin multiplicación general, es decidible; PA añade inducción a un lenguaje con suma y producto y, bajo consistencia, es incompleta. Se retira la fila de «aritmética de Skolem» con sucesor: la firma utilizada no era la habitual de la teoría multiplicativa decidible.

## 3. Correspondencia con ingeniería

**Propuesta, NO_VERIFICADA:** representar transiciones y comprobar testigos finitos. Ni la Σ₁-completitud ni siete axiomas convierten un kernel en verificador universal O(1) por paso. Hay que definir formato, semántica, coste de aritmética y correspondencia con el código.

El bloque histórico `document_epistemic_validity` postulaba la validez de cualquier objeto. Se retira como prueba de Q o del runtime. Este documento es exposición matemática, no una formalización Lean de los resultados citados.

## 4. Referencias

R. M. Robinson, *An Essentially Undecidable Axiom System*, congreso de 1950, actas publicadas en 1952, pp. 729–730; A. Tarski, A. Mostowski y R. M. Robinson, *Undecidable Theories* (1953). Referencias bibliográficas de los resultados, no certificados de implementación.
