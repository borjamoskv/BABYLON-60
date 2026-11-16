# Lote 12: impacto en el registro

Análisis de lectura contra la instantánea anterior. No modifica dictámenes ni cierra hallazgos.

Las 29 fuentes previstas afectan a **53 registros**: 30 seleccionados y 23 colaterales (**20 OPEN, 2 FIXED y 1 NOT_APPLICABLE**). El descubrimiento usa `current.path` o, si falta, `original.path`, además de `source_checks`.

## Colaterales que requieren conservación y revisión de rangos

| ID | Estado conservado | Fuente principal |
| --- | --- | --- |
| SW100-C0032 | OPEN | `tests/test_moskv_native_host.py` |
| SW100-C0073 | FIXED | `01_KISH_ENGINE/babylon60/compliance_exporter/m0_evidence_pack.py` |
| SW100-C0176 | OPEN | `01_KISH_ENGINE/babylon60/verifier/standalone_verify.py` |
| SW100-C0177 | FIXED | `01_KISH_ENGINE/babylon60/verifier/standalone_verify.py` |
| SW100-C0272 | OPEN | `01_KISH_ENGINE/babylon60/attestation/conformal_tree.py` |
| SW100-C0277 | OPEN | `01_KISH_ENGINE/babylon60/attestation/merkle_anchor.py` |
| SW100-C0295 | OPEN | `01_KISH_ENGINE/babylon60/primitives/sandbox.py` |
| SW100-C0323 | OPEN | `scripts/c5_sharur/sharur_100_conversation_auditor.py` |
| SW100-C0334 | OPEN | `scripts/c5_sharur/sharur_100_conversations_sitrep.json` |
| SW100-C0353 | OPEN | `01_KISH_ENGINE/babylon60/bft/bounty_claim_attester.py` |
| SW100-C0356 | OPEN | `scripts/c5_destiladora/codegen_rust_b60.py` |
| SW100-C0361 | NOT_APPLICABLE | `scripts/babylon60/gen_oncology_primitives.py` |
| SW100-C0375 | OPEN | `01_KISH_ENGINE/babylon60/bft/bounty_ring_dispatcher.py` |
| SW100-C0376 | OPEN | `scripts/c5_destiladora/invariant_extractor_z3.py` |
| SW100-C0386 | OPEN | `scripts/c5_destiladora/test_destiladora_e2e.py` |
| SW100-C0405 | OPEN | `01_KISH_ENGINE/babylon60/bft/defi_bytecode_scraper.py` |
| SW100-C0406 | OPEN | `01_KISH_ENGINE/babylon60/bft/defi_bytecode_scraper.py` |
| SW100-C0426 | OPEN | `scripts/c5_git_utils/commit_polisher.py` |
| SW100-C0436 | OPEN | `scripts/c5_cli/moskv_native_host.py` |
| SW100-C0485 | OPEN | `02_EDIN_SWARMS/agents_archi/clients/openrouter.py` |
| SW100-C0491 | OPEN | `tools/install_shield.sh` |
| SW100-C0492 | OPEN | `tools/install_shield.sh` |
| SW100-C0534 | OPEN | `scripts/c5_l1_ledger/seal_bounty_aeon.py` |

## Aserción histórica que impide reconciliar

`reconcile_registry.py` comprueba incondicionalmente el hash histórico de la remediación de C0177 contra el verificador actual. C0175 cambia ese mismo archivo. El ajuste mínimo consiste en aplicar esa comprobación solo si el ID carece de override posterior, igual que las revisiones de los shards. Los overrides ya se validan contra la fuente actual. La evidencia y el hash anteriores permanecen en `history`.

C0177 necesita regresiones actuales V04 de integridad del contenido de eventos JSON y un override completo que conserve FIXED; no se presenta como cierre adicional.

## Criterio para rangos y hashes

Una coincidencia de bytes permite mover un rango sin alterar su observación histórica. Si el fragmento cambia o desaparece, el propietario y el revisor deben contrastar el defecto en la fuente nueva antes de actualizar su hash. Ningún ID colateral se cierra por compartir archivo. Si el parche pudo corregirlo incidentalmente, se conserva como pendiente de adjudicación explícita.

El detalle reproducible por ID y el plan de reconciliación están en [registry-impact.json](registry-impact.json).
