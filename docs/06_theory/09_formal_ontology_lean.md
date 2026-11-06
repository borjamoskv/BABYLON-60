---
title: Modelos Lean: semántica, supuestos y correspondencia
status: Modelo-formal-de-alcance-limitado
version: 2.0.0
---

# Modelos Lean: semántica, supuestos y correspondencia

Revisión científica: 2026-10-24. Estatus: **Modelo-formal-de-alcance-limitado**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Fuentes existentes y alcance

Existen [Babylon.lean](../../proof/lean/Babylon.lean) y [BabylonTrace.lean](../../proof/lean/BabylonTrace.lean). Se inspeccionó su contenido y se comprobó localmente su compilación con el alcance registrado en la auditoría. Eso no certifica que todo el runtime implemente esos modelos ni que las denominaciones físicas de sus comentarios sean correctas.

Los fragmentos históricos de este documento con `F60_Val := ℚ`, `State` y `Step` eran ilustraciones dependientes de definiciones/imports no suministrados en el bloque. Se retiran como supuesto extracto certificado del código vigente. La aritmética natural usada por algunos modelos actuales tampoco equivale automáticamente a racionales normalizados.

## 2. Contraejemplos y propiedades pendientes

- Una lista de eventos con identificadores de padres no impone por tipo ausencia de ciclos, unicidad de identificadores ni existencia de padres. Necesita invariantes adicionales.
- Un contador natural no establece por sí solo causalidad entre máquinas ni consenso en una red asíncrona.
- La relación ilustrada `Step.assign` permitía elegir registros y valores arbitrarios. Que una relación sea inductiva no la hace una función determinista: pueden existir varios estados sucesores.
- Usar racionales evita ciertos redondeos del modelo, pero requiere representación, precisión no acotada o control de límites y serialización; no demuestra ausencia de fallos BFT, de desbordamientos en otro lenguaje ni de errores de hardware.
- Verificar términos no tiene cota universal O(N); alcanzabilidad solo hereda indecidibilidad después de demostrar expresividad suficiente o una reducción pertinente.

## 3. Trazas frente a memoria física

El `step` inspeccionado en BabylonTrace trata números de secuencia, identificador de escritor y acciones. Para `read` comprueba que la secuencia **declarada por el evento** sea par y no futura; no modela payload, cargas de memoria ni dos lecturas de versión. El teorema llamado `no_torn_reads_universal` tiene el alcance de ese predicado, no una garantía general de ausencia de torn reads en el Seqlock Rust.

Una prueba de un modelo abstracto requiere un teorema de refinamiento o correspondencia y un modelo de memoria para justificar propiedades de la implementación. No se demuestra aquí esa bisimulación. Tampoco una prueba de tipo `Step s₁ s₂` es por sí misma una firma criptográfica o autorización.

## 4. Estatus formal

Se retira `document_epistemic_validity`: no probaba ontología ni ejecución. Los resultados efectivamente compilados y sus hipótesis se enumeran en el [informe](AUDIT_SCIENTIFIC_STATUS_2026.md); el modelo no se presenta como certificación de toda la plataforma. El [módulo Curry–Howard](06_curry_howard.md) delimita la diferencia entre términos, axiomas y validación del mundo.
