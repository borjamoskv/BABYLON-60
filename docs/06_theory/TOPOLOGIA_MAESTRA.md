---
title: Topología conceptual y fronteras propuestas
status: Mapa-conceptual-no-certificado
version: 2.0.0
---

# Topología conceptual y fronteras propuestas

Revisión científica: 2026-10-24. Estatus: **Mapa-conceptual-no-certificado**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Roles y capas

| Capa | Responsabilidad conceptual | Límite de la descripción |
| --- | --- | --- |
| CORTEX / agente conversacional | Proponer, recuperar contexto y elaborar candidatos | Identidad o memoria no confieren autoridad, continuidad garantizada ni presencia permanente en servicios. |
| Puentes de integración | Transportar mensajes y llamadas estructuradas | Mencionar WhatsApp, Baileys, Moonshot u Ollama no demuestra que estén conectados en esta sesión ni desplegados. |
| BABYLON / ejecución | Evaluar políticas y ejecutar operaciones autorizadas | «Ring-0» es un nombre de responsabilidad; C-ABI y Rust no prueban ejecución privilegiada en el kernel del SO. |
| Persistencia y evidencias | Registrar entradas, resultados y recibos | SQLite/WAL no es por sí mismo WORM; una firma no prueba verdad del contenido o éxito del efecto. |

El mapa es una propuesta de separación de responsabilidades, no delimitación física definitiva del host ni censo de procesos activos. «Persona» es una interfaz conceptual; bots también pueden tener memoria y sesiones persistentes. No hay un teorema que los distinga por esas etiquetas.

## 2. Rectificaciones de garantías

Se retiran como hechos medidos los 17 millones de operaciones/s, los 57 ns de la secuencia de ejemplo, «Zero Data Races» de todo el swarm y disponibilidad continua de mensajería. No se aportan aquí carga, medición o prueba de correspondencia. `SharedManifest` y `SpscRingBuffer` son estructuras distintas; no se atribuye a ambas toda la memoria del sistema ni un tamaño universal de 64 B.

Los objetos COSE_Sign1 se especifican en [RFC 9052, sección 4.2](https://www.rfc-editor.org/rfc/rfc9052.html#section-4.2); se corrige la referencia a RFC 9942. Una firma puede autenticar bytes bajo supuestos, no «atestiguar legalmente» por sí sola la licitud o corrección de un apagado. La conformidad normativa requiere evaluación propia.

## 3. Flujo de ejemplo, no traza observada

Mensaje → propuesta → evaluación de autoridad → operación autorizada → observación → verificación del resultado. Cada flecha requiere una integración y controles concretos. No se afirma que ese recorrido se haya ejecutado por WhatsApp ni que un agente especializado garantice cumplimiento jurídico.

Para el criterio de no-herencia véase [Continuidad sin obediencia](CONTINUIDAD_SIN_OBEDIENCIA_TEORIA_ARQUITECTONICA.md). La autoridad real se rige por el [manifiesto canónico](../../.babylon60rules), no por los nombres de este mapa.
