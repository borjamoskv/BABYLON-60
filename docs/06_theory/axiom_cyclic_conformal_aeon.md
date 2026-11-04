---
title: Ciclos Aeon: reinicio de estado y límites termodinámicos
status: Modelo-discreto-sin-prueba-termica
version: 2.0.0
---

# Ciclos Aeon: reinicio de estado y límites termodinámicos

Revisión científica: 2026-10-24. Estatus: **Modelo-discreto-sin-prueba-termica**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Diseño conservado

Dividir actividad en épocas, acotar estado caliente y archivar evidencias es una propuesta de ingeniería. «Aeon», «reseteo conforme» y la referencia a cosmología CCC son metáforas: no hay en este modelo un espacio-tiempo ni una transformación conforme que permita deducir propiedades físicas del procesador.

## 2. Qué dicen realmente las fuentes formales

Los cinco bloques históricos de esta página invocaban `ax_pl_*` sin suministrar definiciones. No reproducen el contenido actual de [Babylon.lean](../../proof/lean/Babylon.lean). La inspección actual muestra:

| Declaración | Alcance lógico observado |
| --- | --- |
| `lemma_monotonic_entropy_growth` | Recibe `h_growth`, que ya presupone que el orden de ticks implica el de entropy; aplica esa hipótesis. No deriva una ley de entropía. |
| `AeonState.h_bounded` y lema de memoria | Almacena la igualdad del campo `hot_memory_bytes` a 64; no mide tamaño real del objeto Lean, heap, caché ni memoria total del programa. |
| `conformal_reset` y estabilidad | Construye un registro con `entropy := 0` y ciertos campos fijados; prueba sus valores por reducción. No demuestra estabilidad dinámica física ni ausencia de fugas. |
| `theorem_landauer_cache_bypass` | Demuestra igualdades de campos del registro. No contiene calor, temperatura, borrado físico ni mediciones; su nombre no amplía la proposición. |

La antigua conclusión `∃ hot_heat : Nat, hot_heat = 0` ni siquiera vinculaba ese número a una operación física: el testigo cero existe sin ejecutar un sistema. Los resultados del modelo no son necesariamente falsos; se retira su interpretación como prueba termodinámica.

## 3. Correcciones físicas

Landauer trata el borrado lógicamente irreversible bajo condiciones físicas específicas. Para el bit equiprobable ideal a 300 K, $k_BT\ln2\approx2{,}87\times10^{-21}$ J. No se deduce un coste por token, por tick ni por escritura sin analizar qué información se borra. La [fuente original de Landauer](https://doi.org/10.1147/rd.53.0183) no establece un bypass mediante hashing.

Una raíz Merkle de 256 bits no es una compresión reversible de historiales arbitrarios; si se pretende conservarlos, su almacenamiento externo y acceso requieren recursos. Mover trabajo a un sink no demuestra calor local exactamente cero ni elimina coste global. Se retiran AX-PL-5 y el «teorema Penrose–Landauer» como garantías físicas, así como la latencia 2,13 ns sin registro de medición.

64 B de layout/alineación de una estructura concreta no prueban tamaño de línea de caché, ausencia de false sharing ni memoria de trabajo total. La monotonía de un campo llamado entropy es una hipótesis o regla de transición, no una consecuencia de la segunda ley.

## 4. Evidencia necesaria

Para una garantía de recursos: medir heap, colas, retención y crecimiento con carga y horizonte fijados. Para calor: balance físico con instrumentos y unidades. Para correspondencia: implementación identificada, modelo de memoria y refinamiento probado. Ninguna de esas propiedades se certifica aquí; se conserva solo el alcance aritmético de las fuentes compiladas descrito en el informe.
