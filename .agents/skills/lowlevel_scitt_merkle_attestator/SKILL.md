<!-- C5-REAL EXERGY CERTIFIED -->
---
name: lowlevel_scitt_merkle_attestator
description: Skill especializado en la construcción de árboles Merkle SHA3-256 sobre fragmentos de bytes de documentos y emisión de certificados de atestación SCITT C5-REAL.
---

# Low-Level SCITT & Merkle Attestator Skill

Este Skill formaliza el veredicto del análisis forense mediante la construcción de una prueba criptográfica determinista (*Merkle Proof*) y la emisión de un recibo SCITT (Supply Chain Integrity, Transparency, and Trust).

## Propiedades Garantizadas

1. **Particionado en Bloques y Árbol Merkle SHA3-256**:
   - División determinista del documento en bloques de tamaño fijo (ej. 4 KB).
   - Cálculo del digest SHA3-256 por bloque y construcción de la raíz Merkle (\(R_{Merkle}\)).

2. **Atadura Criptográfica del Veredicto (Commitment)**:
   - Firma inmutable que vincula:
     - Hash global del documento \(H(Doc)\).
     - Raíz Merkle \(R_{Merkle}\).
     - Entropía máxima registrada \(H_{max}\).
     - Recuento de obj/streams de riesgo detectados.
     - Presencia de esteganografía o caracteres invisibles.

3. **Veredicto Fail-Stop**:
   - Si la entropía en zonas críticas excede los umbrales o se detectan payloads ejecutables unverified, emite un estado `ABORT / ANOMALY_QUARANTINE`.
   - Si el documento satisface la integridad formal, emite `PASS / SCITT_CERTIFIED`.

## Herramientas Asociadas
- `src/cortex-engine/cortex-persist/cortex_python/doc_audit/scitt_merkle_prover.py`
