---
title: Tautologías, supuestos y evidencia: rectificación del informe
status: Auditoria-documental-con-alcance-limitado
version: 2.0.0
---

# Tautologías, supuestos y evidencia: rectificación del informe

Revisión científica: 2026-10-24. Estatus: **Auditoria-documental-con-alcance-limitado**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Antipatrón documentado

Una prueba de A → A o True puede ser correcta. El error es presentarla como prueba de una propiedad distinta —concurrencia, seguridad o energía— que su proposición no expresa. Declarar `axiom document_epistemic_validity` presupone validez; no la comprueba. Este informe no necesita un axioma de validez propio.

Una estructura que exige una prueba como campo tampoco la fabrica: es una especificación condicional, salvo que se construya una instancia y se examine su alcance. `omega`, `decide`, AOT o ausencia de `sorry` no sustituyen inspeccionar qué se afirma y qué se asume.

## 2. Métricas históricas sin evidencia suficiente

| Afirmación original | Estatus corregido |
| --- | --- |
| TRNG Secure Enclave: 7,9975 bits/byte y 99,969%, PASS | NO_VERIFICADO: faltan muestra, procedencia, estimador e incertidumbre. Una estimación cercana al máximo no prueba origen físico, independencia ni seguridad de la fuente. |
| 1001 archivos, cero clones Jaccard ≥ 0,75, PASS | NO_VERIFICADO como medición actual: faltan lista de archivos, normalización, algoritmo y resultados reproducibles ligados a versión. |
| Densidad KISH 99,85% y slop 0,0, PASS | Métrica no operacionalizada aquí; no es porcentaje de exergía física ni prueba de calidad lingüística universal. |
| Fisher g_ij = 0, calor ΔQ = 0 por tautología | No se definen modelo estadístico ni balance físico; se retiran como inferencias cuantitativas. |

## 3. Criterio de revisión

Separar enunciado, hipótesis, prueba y vínculo con implementación. Guardar comandos y resultados reales para mediciones, con versión, entorno y cobertura. Un test que siempre responde ALLOW no prueba seguridad; un test positivo aislado no prueba una frontera completa. El rechazo de una operación debe obedecer el contrato del componente, no una instrucción genérica de este ensayo.

El enlace absoluto heredado al [dictamen histórico](AUDIT_VERDICT_C5_REAL.md) se corrige a relativo. Ese dictamen también distingue ahora sus acusaciones históricas de lo efectivamente comprobado. No se infiere falsedad de una ejecución remota antigua por no encontrar sus archivos en el árbol actual.
