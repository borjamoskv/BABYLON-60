<!-- C5-REAL EXERGY CERTIFIED -->
---
name: lowlevel_metadata_stego_auditor
description: Skill especializado en extracción forense de metadatos XMP/Info y detección de esteganografía tipográfica (caracteres invisibles Unicode, Zero-Width spaces y canales ocultos).
---

# Low-Level Metadata & Steganography Auditor Skill

Este Skill faculta al agente para auditar metadatos crudos, historia de revisiones y estructuras de texto para detectar exfiltración de información sensible o marcaje esteganográfico de datos.

## Vectores de Análisis

1. **Extracción Directa de Metadatos Crudos**:
   - Lectura de diccionarios `/Info` (Autor, Creador, ModDate, Producer, Keywords).
   - Extracción de paquetes XML de XMP Metadata (`<?xpacket begin="..."?>`).

2. **Detección de Esteganografía Tipográfica Unicode**:
   - Detección de caracteres invisibles o de ancho cero (*Zero-Width Spaces*):
     - `U+200B` (Zero Width Space)
     - `U+200C` (Zero Width Non-Joiner)
     - `U+200D` (Zero Width Joiner)
     - `U+FEFF` (Zero Width No-Break Space / BOM)
     - `U+202E` (Right-to-Left Override - RLO)
   - Decodificación de marcas de agua esteganográficas codificadas en secuencias binarias invisibles inter-palabras.

3. **Homóglifos y Sustitución de Glifos**:
   - Detección de caracteres cirílicos u omicrons griegos intercalados en texto latino para eludir filtros semánticos o firmas de texto.

## Herramientas Asociadas
- `src/cortex-engine/cortex-persist/cortex_python/doc_audit/metadata_stego_extractor.py`
