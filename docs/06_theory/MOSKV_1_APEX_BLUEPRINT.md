---
title: MOSKV-1 APEX: propuesta de producto e hipótesis de uso
status: Blueprint-no-certificado
version: 2.0.0
---

# MOSKV-1 APEX: propuesta de producto e hipótesis de uso

Revisión científica: 2026-10-24. Estatus: **Blueprint-no-certificado**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Naturaleza y alcance

El documento conserva propuestas de IDE local, memoria de trabajo, edición asistida y visualización. No es un inventario de capacidades instaladas, una autorización de despliegue ni una prueba de beneficios cognitivos o fisiológicos. Se retiran el sello «Verified» y el axioma `document_epistemic_validity`.

| Área propuesta | Estatus y evidencia pendiente |
| --- | --- |
| Orquestador nativo, análisis AST y renderer de grafos | Diseño. Requiere integración identificada, pruebas funcionales y medición de latencia. «Cero latencia» no es una garantía física admisible. |
| Memoria SQLite/embeddings | Diseño. WAL no prueba WORM, inmutabilidad ni BFT. Hay que definir retención, integridad, recuperación y coste. |
| Inferencia local y gateway remoto | Alternativas de arquitectura. «Estado infinito» no describe un dispositivo de recursos finitos; marcas de modelos no acreditan conexión ni rendimiento. |
| Zoom, atajos, sonificación, MIDI y feedback háptico | Hipótesis de usabilidad; necesitan tareas, población, métricas, accesibilidad y contraste. |
| Hot-reload de bibliotecas | Diseño que requiere protocolo de sincronización y ciclo de vida; un intercambio de puntero no demuestra ausencia de interrupciones o uso de recursos liberados. |
| Optimización de activos y despliegue | Flujos propuestos, sometidos a controles de autorización, evidencia y errores del proyecto. |

## 2. Garantías retiradas

No se sostienen «0 UI impact», ausencia universal de fricción, eliminación de sesgos, prevención de model collapse por consenso, ni eficacia frente a TDAH/AACC por estilo visual. «Hipocampo», «gemelo biológico», «bucles dopaminérgicos» y «entrelazamiento háptico» son metáforas; no medidas clínicas ni efectos físicos demostrados.

Variar temperatura de inferencia con meteorología es una propuesta arbitraria sin mejora verificada. Una señal háptica no evita thermal throttling. Un clipper tanh limita una variable digital bajo condiciones; no certifica niveles acústicos seguros ni sustituye medición de la cadena completa.

## 3. Criterio de promoción de estatus

Para declarar una capacidad implementada: ruta de código, versión y prueba funcional. Para rendimiento: hardware, carga y método. Para beneficios humanos: evaluación apropiada. Para memoria o aislamiento: pruebas y modelo de fallos pertinentes. Ninguna se acredita mediante un nombre de producto, una firma textual o un sello documental.

Las obligaciones vigentes se consultan en el [manifiesto canónico](../../.babylon60rules), sin inferir permiso para publicar ni para ejecutar efectos protegidos de este blueprint.
