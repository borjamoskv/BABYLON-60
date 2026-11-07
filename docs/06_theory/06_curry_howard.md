---
title: Curry–Howard: correspondencias y fronteras de confianza
status: Exposicion-matematica-no-formalizada
version: 2.0.0
---

# Curry–Howard: correspondencias y fronteras de confianza

Revisión científica: 2026-10-24. Estatus: **Exposicion-matematica-no-formalizada**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Correspondencia matemática

En cálculos concretos, las proposiciones corresponden a tipos, las pruebas a términos y la normalización a evaluación. La conexión categórica requiere categorías con la estructura correspondiente; no toda categoría cartesiana cerrada contiene por ello coproductos o todos los tipos dependientes.

Una prueba es un término del tipo de su proposición, **relativo a los axiomas y reglas del sistema**. No todo programa, especialmente uno con recursión general o efectos, constituye una prueba de terminación o corrección. [Wadler (2015), *Propositions as Types*](https://www.pure.ed.ac.uk/ws/portalfiles/portal/20001186/propositions_as_types.pdf).

## 2. Comprobación y búsqueda

El chequeo de tipos es decidible en sistemas cuidadosamente diseñados; no hay aquí una cota universal O(N). Buscar habitantes en sistemas suficientemente expresivos puede ser indecidible; en sistemas más débiles puede ser decidible. Σ₁-completitud permite enumerar pruebas hasta encontrar las de instancias verdaderas, sin algoritmo total para todas las entradas ni garantía de rapidez.

El ejemplo histórico `add_zero_right` solo reutilizaba un supuesto `q4`, con `QNat`, `QAdd` y `QZero` sin definir. Se retira como ejemplo ejecutable, no como refutación del axioma Q4. Tampoco se confunde el tipo nativo Nat de Lean, que tiene inducción, con un modelo abstracto de Q.

## 3. HoTT y univalencia

En teoría de tipos homotópica, la univalencia relaciona equivalencia de tipos e identidad mediante estructura y reglas concretas. No vuelve iguales sin más a cualesquiera objetos descritos como «similares» ni identifica indistinguibilidad por 1-WL con isomorfismo de grafos. Lean ordinario no incorpora por defecto toda la teoría homotópica. [Contexto del programa de fundamentos univalentes, IAS](https://www.ias.edu/ideas/2013/awodey-coquand-univalent-foundations).

## 4. Aplicación propuesta

Usar certificados de transiciones en BABYLON-60 es una propuesta de arquitectura. Su seguridad exige definir semántica, checker, axiomas confiados, parser y vínculo con el ejecutable. Una firma criptográfica autentica un mensaje bajo condiciones; no es una prueba de la proposición contenida.

Se retira `document_epistemic_validity`, que solo asumía la validez del documento. No se declara formalizado Curry–Howard ni demostrada una complejidad del checker por este texto.
