<!-- C5-REAL EXERGY CERTIFIED -->
---
name: lowlevel_byte_entropy_auditor
description: Skill especializado en escaneo de estructura de bytes a bajo nivel, mapas de entropía de Shannon, detección de magic bytes, offsets y overlay payloads.
---

# Low-Level Byte & Entropy Auditor Skill

Este Skill capacita al agente para inspeccionar el flujo de bytes crudo (*raw binary stream*) de cualquier documento o contenedor binario (PDF, DOCX, ZIP, PNG, ELF, Mach-O) sin depender de librerías de alto nivel.

## Objetivos Físicos y Criptográficos

1. **Histograma y Entropía de Shannon \(H(X)\)**:
   - Recorre el archivo con una ventana deslizante (*sliding window*) de tamaño configurable (ej. 256 / 512 bytes) y paso variable.
   - Calcula la entropía en cada segmento:
     \[
     H(X) = -\sum_{i=0}^{255} p(x_i) \log_2 p(x_i)
     \]
   - Identifica regiones de alta entropía (\(H(X) > 7.5\)) que denotan compresión, cifrado o payloads ocultos.

2. **Identificación de Magic Bytes y Offsets**:
   - Valida firmas de cabecera (`%PDF-`, `PK\x03\x04`, `\x7fELF`, `\x89PNG`, `\xfe\xed\xfa`).
   - Mapea las estructuras internas de offset (tablas `xref` en PDF, End of Central Directory en ZIP).

3. **Detección de Overlay Data (Payload Post-EOF)**:
   - Localiza los delimitadores legítimos de final de archivo (ej. `/%%EOF` o marca EOCD).
   - Detecta bytes huérfanos o cargas útiles adjuntas tras la marca de fin formal.

## Herramientas Asociadas
- `src/cortex-engine/cortex-persist/cortex_python/doc_audit/entropy_byte_scanner.py`
