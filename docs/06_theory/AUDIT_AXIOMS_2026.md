---
title: Revisión documental de la axiomatización C5-REAL
status: Historical review
version: 2.0.0
---

# Revisión documental de la axiomatización C5-REAL

El informe original, fechado el 18 de agosto de 2026, declaraba una retirada
completa de firmas vacías y publicaba estados de verificación. No vinculaba esas
declaraciones con una revisión de código y registros reproducibles de compilación.
Esta corrección documental del 30 de octubre de 2026 retira ese veredicto global.

## Fallo identificado

El propio informe terminaba con un axioma sin propiedad del sistema y un teorema
cuya conclusión era `True`. Ese bloque no restringía estados, transiciones,
concurrencia ni entradas y no constituía evidencia sobre ellos. Se ha eliminado,
sin sustituirlo por otra afirmación trivial.

Los ejemplos de este patrón se describen expresamente como antipatrones en
[Tautología vacía](AUDIT_TAUTOLOGIA_VACIA_2026.md). La existencia de un axioma o de
un campo que exige una prueba no demuestra que se haya construido una instancia
del modelo, ni que ese modelo represente una ejecución del producto.

## Ámbitos pendientes de verificación

Esta tabla conserva los temas del informe histórico. Enumera las comprobaciones
necesarias; no comunica ejecuciones nuevas ni una certificación del corpus.

| Documento | Comprobación necesaria | Estado de esta revisión |
| --- | --- | --- |
| [AXIOMATIZATION_C5_REAL.md](AXIOMATIZATION_C5_REAL.md) | Identificar axiomas, hipótesis y propiedad demostrada. | NO_VERIFICADO |
| [axiom_bayesian_disintegration.md](axiom_bayesian_disintegration.md) | Construir instancias y delimitar el dominio probabilístico. | NO_VERIFICADO |
| [axiom_sharur_swarm.md](axiom_sharur_swarm.md) | Conectar límites del modelo con la representación y el scheduler. | NO_VERIFICADO |
| [axiom_oncology_protocol.md](axiom_oncology_protocol.md) | Separar el modelo formal de las afirmaciones biológicas y clínicas. | NO_VERIFICADO |
| [axiom_tonnetz_oversight.md](axiom_tonnetz_oversight.md) | Precisar definiciones, hipótesis y correspondencia con datos. | NO_VERIFICADO |
| [c5_thermodynamic_invariants_compendium.md](c5_thermodynamic_invariants_compendium.md) | Distinguir fórmulas, unidades, objetivos y magnitudes medidas. | NO_VERIFICADO |

## Fuentes formales del kernel

[BabylonTrace.lean](../../proof/lean/BabylonTrace.lean) contiene, entre otros,
`no_torn_reads_universal`: bajo la hipótesis de que el validador acepta una traza,
la traza satisface la propiedad `TraceReadsEven` del modelo. Su alcance depende
de las definiciones e hipótesis de ese archivo; no demuestra por extensión las
afirmaciones científicas de todos los documentos anteriores.

El [informe de seguridad del kernel](../security/kernel-audit-2026-10-15.md)
identifica comprobaciones concretas y sus límites. Una evaluación nueva debe
registrar revisión, comando, entorno y resultado, y analizar los axiomas usados.
Esta edición documental no ha ejecutado Lean ni certifica el runtime.
