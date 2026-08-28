<!-- C5-REAL EXERGY CERTIFIED -->
---
name: lowlevel_scitt_merkle_attestator
description: Skill especializado en la construcción de árboles Merkle SHA3-256 sobre fragmentos de bytes de documentos y emisión de certificados de atestación SCITT C5-REAL.
---

# Low-Level SCITT & Merkle Attestator Skill

Este Skill dota al agente de los axiomas operacionales para clausurar el proceso de validación epistémica mediante la construcción de una prueba criptográfica inmutable (*Merkle Proof*). El recibo SCITT (Supply Chain Integrity, Transparency, and Trust) resultante actúa como la **Causa Final** (*Entelecheia*) del sistema, garantizando el aislamiento del Kernel frente a la estocasticidad (Dynamis) y soportando matemáticamente el Cap Contractual de Responsabilidad exigido por el modelo Enterprise.

## 1. Invariantes Topológicos y Particionado Discreto
El documento no se procesa como un flujo continuo, sino como un entramado discreto de bloques.
- **Árbol Merkle Estricto (SHA3-256)**: Fragmentación determinista del vector material en bloques discretos alineados (ej. 4 KB). El cálculo del digest sobre cada bloque construye de forma unívoca la raíz Merkle (R_{Merkle}).
- **Prohibición de Colisiones**: La estructura de bytes se congela. Cualquier manipulación infinitesimal (ej. un bit alterado por radiación térmica o esteganografía) colapsa la raíz y disipa el recibo.

## 2. Atadura Causal del Veredicto (Commitment Formal)
El recibo SCITT no es un log estadístico; es una atestación legal vinculante que sella los cuatro vectores causales:
- **Causa Material**: Hash global SHA3-256 del contenedor (H(Doc)).
- **Causa Formal**: Raíz Merkle (R_{Merkle}) que prueba la integridad topológica interna.
- **Frontera Termodinámica**: Entropía máxima registrada por bloque (H_{max}), garantizando el cumplimiento del Límite de Landauer (ausencia de *anergía* superpuesta).
- **Bisimulación**: Ausencia atestada matemáticamente de esteganografía tipográfica, espacios nulos o *overlay payloads*.

## 3. Disparador de Cuarentena (Primum Movens / Fail-Stop)
La atestación es binaria, libre de umbrales probabilísticos.
- **Fail-Stop Mandatorio**: Si la entropía (H_{max}) excede la cota superior, o se viola la bisimulación observacional, el actuador emite inmediatamente `ABORT / ANOMALY_QUARANTINE`.
- **Entelecheia Validada**: Únicamente si el álgebra CF-GKAT converge y el espacio discreto es puro, se emite el estado `PASS / SCITT_CERTIFIED`, habilitando al LLM a consumir el contexto de forma segura bajo el amparo de la EU AI Act (Art. 15).

## Herramientas de Clausura Criptográfica
- `src/cortex-engine/cortex-persist/cortex_python/doc_audit/scitt_merkle_prover.py` (Prover determinista; invocado tras la purga exergética).
