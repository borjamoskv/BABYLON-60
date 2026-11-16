---
name: c5_release_governance_invariant
description: Invariante de gobierno de releases públicas en GitHub alineadas con RELEASE_MANIFEST.json y Ley O9.
trigger: "model_decision"
---

# Invariante de Gobierno de Releases (INV_C5_RELEASE_GOVERNANCE)

Aplica al preparar o revisar una release concreta. Registrar manifiesto, revisión, checks y evidencia. Preparar una corrección local no autoriza publicar ni modificar GitHub; aplicar la autorización y el contrato de atestación del [manifiesto](../../.babylon60rules#autoridad-y-seguridad) cuando corresponda.

## 1. Alineación Estricta de Estado (Anti-Deriva de Releases)
El estado de una release pública en GitHub (Stable vs Pre-release) DEBE ser una proyección determinista y exacta del campo `state` del `RELEASE_MANIFEST.json` (o archivo canónico equivalente).
* Si el manifiesto dicta `candidate`, la release DEBE publicarse con el flag de pre-release (`--prerelease`).
* Jamás se forzará la etiqueta "Estable" si la CI/CD (Sanity) de la revisión que se publica no ha finalizado con éxito (Exit Code 0).

## 2. Separación de Integridad Criptográfica y Cumplimiento Evaluado (Ley O9 Aplicada)
* La verificación correcta de una firma Ed25519 contra la clave y el contenido esperados acredita la integridad de esos bytes dentro del esquema utilizado, pero NO certifica la veracidad jurídica, legal o técnica de los procesos del mundo real.
* Queda **estrictamente prohibido** utilizar palabras como "certificada", "homologada" o "cumplimiento absoluto" en textos públicos de releases (ej. EU AI Act) si no existe un rastro de evidencia determinista (`evidence.json`) en silicio que acote la afirmación (Claim).
* El marco legal evalúa el caso de uso y el nivel de riesgo del sistema en su conjunto, no clasifica a la arquitectura aisladamente. Todo texto comercial o de release no debe incurrir en "Falso Isomorfismo Legal".

## 3. Invariabilidad del Puntero de Atestación
El `commit hash` referido en el cuerpo del release en GitHub DEBE coincidir bit a bit con el `commit` sellado en el `RELEASE_MANIFEST.json`. Si hay discrepancia, preparar la corrección contra el manifiesto verificado y bloquear la publicación afectada. Aplicarla a la interfaz pública requiere autorización; conservar evidencia de la revisión y del cambio.
