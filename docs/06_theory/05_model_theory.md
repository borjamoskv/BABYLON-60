---
title: Teoría de modelos: hipótesis y alcance de los resultados
status: Exposicion-matematica-no-formalizada
version: 2.0.0
---

# Teoría de modelos: hipótesis y alcance de los resultados

Revisión científica: 2026-10-24. Estatus: **Exposicion-matematica-no-formalizada**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Estructuras y compacidad

Una estructura interpreta símbolos en un dominio no vacío; satisface una teoría cuando satisface todas sus sentencias. En lógica de primer orden, compacidad afirma que una teoría tiene modelo si y solo si todas sus partes finitas lo tienen. Una derivación de contradicción usa finitos axiomas: junto con completitud semántica, esto da una demostración de compacidad. Es un argumento matemático, no una prueba Lean de este documento.

Añadir a Q una constante distinta de cada numeral estándar da, por compacidad, un modelo con un elemento no estándar. La clase de todas las estructuras finitas no es axiomatizable por una teoría de primer orden, aunque sí puede imponerse un tamaño finito concreto. El espacio de Stone se construye con teorías completas o tipos apropiados, no sin más con la clase de todos los modelos.

## 2. Löwenheim–Skolem y categoricidad

Para un lenguaje contable, una teoría con modelo infinito tiene un modelo contable. En general las cotas de cardinalidad dependen del tamaño del lenguaje. Si tiene modelo infinito, hay modelos de todo cardinal infinito al menos tan grande como el lenguaje. Se corrige la afirmación sin esa restricción.

ZFC tiene un modelo contable **si tiene algún modelo**, en el marco metateórico usual. La existencia de ese modelo no se obtiene afirmando solamente que ZFC prueba conjuntos no contables. La contabilidad externa de su dominio y la ausencia interna de ciertas biyecciones son nociones diferentes.

No puede haber unicidad de todos los modelos infinitos de una teoría de primer orden entre todos los cardinales. Sí puede haber **categoricidad en un cardinal fijo**: la teoría de órdenes densos sin extremos es categórica en el cardinal contable. Se retira el veto absoluto a la categoricidad y la afirmación de que toda teoría de segundo orden es categórica; la aritmética de segundo orden con semántica plena tiene propiedades distintas de su semántica Henkin.

## 3. Lindström y Tennenbaum

Lindström caracteriza primer orden mediante compacidad y una propiedad Löwenheim–Skolem dentro de una clase de lógicas abstractas con condiciones de cierre y extensión precisadas. No se extrapola a todo formalismo imaginable. [Artículo original de Lindström (1969)](https://doi.org/10.1111/j.1755-2567.1969.tb00356.x).

Tennenbaum excluye una presentación computable de un modelo contable no estándar de PA con suma y producto computables. No dice que tales modelos carezcan de descripciones matemáticas o de cualquier acceso parcial. [Anuncio original, Notices AMS 1959, p. 270](https://www.ams.org/journals/notices/195906/195906FullIssue.pdf).

## 4. Límites de aplicación

No se deriva de estos teoremas aislamiento de procesos, protección contra agentes ni propiedad de seguridad del kernel. Esos mapeos son propuestas que necesitan una correspondencia formal con la implementación. Se retira el axioma de validez documental como supuesta prueba de teoría de modelos.
