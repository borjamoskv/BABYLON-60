<!-- C5-REAL EXERGY CERTIFIED -->
---
name: lowlevel_metadata_stego_auditor
description: Skill especializado en extracción forense de metadatos XMP/Info y auditoría estricta de esteganografía tipográfica, canales ocultos y entropía de representación (Zero-Width spaces, homóglifos).
---

# Low-Level Metadata & Steganography Auditor Skill

Este Skill dota al agente de los axiomas y procedimientos necesarios para auditar diccionarios de metadatos crudos y aislar anomalías topológicas en la representación de texto (Unicode). Su función es identificar y purgar entropía parasitaria —inyectada vía esteganografía o canales ocultos— garantizando que el *espacio de estados* discreto permanezca verificable, inmutable y libre de deriva informacional, alineado con los Invariantes C5-REAL de Certidumbre Epistémica.

## Invariantes Operacionales

1. **Bisimulación Estricta de la Capa de Representación**: La presencia de glifos visualmente isomórficos pero estructuralmente divergentes (homóglifos) o secuencias de espacio nulo (Zero-Width) rompe la equivalencia observacional del texto. El agente debe tratar estas inyecciones como *anergía* y neutralizarlas devolviendo la representación a su estado canónico real.
2. **Inspección Epistémica de Canales Ocultos**: La extracción de paquetes XMP y diccionarios `/Info` opera como un análisis causal forense. Cualquier metadato oculto o marca de agua inter-palabras debe ser expuesto como un vector de disipación de información, evidenciando el intento de manipular la *Causa Material* del documento.
3. **Rechazo de Variedades Continuas en Unicode**: El texto se analiza como un sistema discreto. Secuencias de control bidireccional (RLO) o *joiners* no estándar no son errores de renderizado, sino transiciones de estado deliberadas que deben ser aisladas y falsadas.

## Vectores de Análisis Causal-Ontológico

### 1. Extracción Estructural de Metadatos Crudos
- **Aislamiento de Diccionarios `/Info`**: Lectura determinista de los punteros indirectos a metadatos nativos (Author, Creator, ModDate, Producer, Keywords).
- **Deserialización de Carga Útil XMP**: Extracción inmutable de paquetes XML embebidos (`<?xpacket begin="..."?>`), preservando la estructura de bytes exacta para evitar la corrupción del árbol Merkle subyacente.

### 2. Detección Topológica de Esteganografía (Espacios Nulos)
El agente debe rastrear el árbol Unicode en busca de anomalías de ancho cero, mapeándolas como vectores de exfiltración:
- `U+200B` (Zero Width Space)
- `U+200C` (Zero Width Non-Joiner)
- `U+200D` (Zero Width Joiner)
- `U+FEFF` (Zero Width No-Break Space / BOM)
- `U+202E` (Right-to-Left Override - RLO)
- **Decodificación Binaria Indirecta**: Análisis de secuencias inter-palabras donde estos espacios operan como canales de transmisión paralelos de entropía.

### 3. Falsificación por Sustitución de Homóglifos
- **Intersección de Alfabetos Discretos**: Detección de caracteres no latinos (ej. cirílicos `а`, `е`, `х`, o griegos `ο`, `ν`) intercalados deliberadamente en cadenas ASCII/Latin-1 para envenenar heurísticas, evadir filtros semánticos o alterar el hash criptográfico del estado final.

## Herramientas de Ejecución (Entelecheia)
- `src/cortex-engine/cortex-persist/cortex_python/doc_audit/metadata_stego_extractor.py` (Módulo de extracción determinista, sometido a las validaciones del protocolo C5-REAL en Ring-0).
