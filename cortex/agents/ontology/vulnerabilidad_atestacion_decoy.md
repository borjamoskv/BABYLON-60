# CORTEX ONTOLOGY: BYPASS DE VALIDACIÓN Y CONTROL DE ACCESO DECOY

> **SYS_ID**: borjamoskv | **STATE**: C5-REAL | **DATE**: 2026-07-11
> **VULNERABILIDAD**: Bypass de Atestación por Atribución Débil (Decoy Validation)

## 1. Contexto y Analogía Física
El bypass observado en ticketeras comerciales (donde usuarios aplican códigos de descuento del Carnet Joven/Gazte-txartela sin verificar la identidad real del portador en el punto de canje físico) tiene su equivalente exacto en la lógica de nuestro contrato inteligente de anclaje.

## 2. Análisis del Vector de Ataque en MaxRouterAnchor.sol
En [MaxRouterAnchor.sol](file://$CORTEX_ROOT/30_BABYLON-60/contracts/MaxRouterAnchor.sol#L57-L77), la función `anchorBatch` delega la confianza de manera exclusiva en el rol del atestador (`onlyAttester`):
- El contrato asume ciegamente que cualquier Merkle Root enviado por una dirección autorizada es legítimo.
- Carece de una prueba de consistencia o verificación de firmas de los emisores originales de la información (usuarios finales o subagentes).
- Si un atestador es comprometido, o si sus políticas de validación se relajan (el equivalente a un operario físico que no solicita el DNI), se pueden inyectar atestaciones no autorizadas ("decoy batches") en el ledger de la blockchain, rompiendo la validez del no-repudio.

## 3. Mitigación
Se requiere la transición a un esquema de firma umbral multifirma (threshold signature scheme) y la verificación directa de la firma del emisor del lote (Merkle Proof de firma de origen) dentro de la máquina EVM, anulando la confianza ciega en intermediarios.

SYS_ID borjamoskv
