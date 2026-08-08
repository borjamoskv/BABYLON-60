<!-- C5-REAL EXERGY CERTIFIED -->
---
name: lowlevel_stream_object_auditor
description: Skill especializado en descompresión de streams crudos (zlib/FlateDecode) e inspección de árboles de objetos, scripts embebidos y referencias indirectas.
---

# Low-Level Stream & Object Auditor Skill

Este Skill permite al agente descomprimir en tiempo real flujos de datos sin invocar motores PDF de alto nivel, inspeccionando la topología de objetos binarios e identificando primitivas de código o ejecución.

## Objetivos de Inspección

1. **Descompresión en Tiempo Real de Streams**:
   - Soporte para decodificación de `FlateDecode` (`zlib`), `ASCIIHexDecode`, `ASCII85Decode`.
   - Extracción de buffers descomprimidos para inspección de texto y objetos incrustados.

2. **Detección de Patrones de Ejecución y Riesgo**:
   - Búsqueda de tokens críticos: `/JavaScript`, `/JS`, `/Launch`, `/EmbeddedFiles`, `/OpenAction`, `/AA` (Additional Actions), `/URI`.
   - Identificación de vectores de ataque o scripts que escapan a los visores estándar.

3. **Invarianza de Referencias Indirectas y Objetos Huérfanos**:
   - Auditoría de objetos `N M obj ... endobj`.
   - Detección de objetos desvinculados de la raíz (`/Root` / `/Catalog`) que residen silenciosamente en la memoria del documento.

## Herramientas Asociadas
- `src/cortex-engine/cortex-persist/cortex_python/doc_audit/stream_object_parser.py`
