---
title: Computabilidad: indecidibilidad y verificación acotada
status: Exposicion-matematica-no-formalizada
version: 2.0.0
---

# Computabilidad: indecidibilidad y verificación acotada

Revisión científica: 2026-10-24. Estatus: **Exposicion-matematica-no-formalizada**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Modelos y tesis de Church–Turing

Máquinas de Turing, cálculo lambda y funciones parciales recursivas caracterizan la misma clase computable mediante traducciones formales. La tesis de Church–Turing identifica esa clase con la noción informal de cálculo efectivo: es una tesis, no un teorema de equivalencia con toda operación física concebible. Representar cómputos en Q es otro resultado, no una máquina física ni una cuarta invención independiente en los años treinta.

## 2. Parada y Rice

No existe un algoritmo total que decida la parada para todo programa y entrada de un modelo universal. El argumento diagonal supone un decisor total H y construye D(p), que no para si H(p,p) predice parada y para en el otro caso; evaluar D sobre su propio código produce contradicción. No demuestra una imposibilidad para cualquier hipotético oráculo físico.

Rice excluye un decisor total para cualquier propiedad extensional no trivial de las funciones parciales computables, sobre todos los programas del modelo universal. No impide verificar instancias, usar pruebas, aceptar falsos negativos en un analizador correcto o decidir propiedades de lenguajes restringidos.

Con la codificación habitual, la parada se representa mediante existencia de una traza finita. Q demuestra las instancias verdaderas correspondientes, sin por ello decidir las negativas ni acotar el tiempo de búsqueda.

## 3. Jerarquías

Σ₁ corresponde a conjuntos computablemente enumerables y Π₁ a sus complementos; Δ₀ usa cuantificadores acotados en el lenguaje fijado. No toda fórmula de nivel Σ_n define un problema completo para ese nivel. Los saltos de Turing producen grados estrictamente superiores; se retiran los ejemplos que asignaban sin codificación ni prueba grados exactos a «independencia de Q» y «ser esencialmente indecidible».

La función de Ackermann es total computable pero no primitiva recursiva. Esto muestra una distinción entre clases de funciones, no una medición de energía o latencia de software.

## 4. Aplicación y estado formal

Verificar un certificado explícito y buscarlo son problemas distintos. Que la búsqueda general sea indecidible no hace lineal cualquier verificador ni obliga a usar BFT. No se ha probado aquí la universalidad del lenguaje B60. El axioma de validez documental retirado no probaba parada ni Rice.

Fuente primaria: [A. M. Turing, artículo de 1936 y corrección](https://theory.stanford.edu/~trevisan/cs172-07/turing36.pdf). H. G. Rice (1953), *Classes of Recursively Enumerable Sets and Their Decision Problems*, Trans. AMS 74, 358–366.
