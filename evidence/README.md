# Política de Custodia Criptográfica y Retención OPSEC de Evidencias (`evidence/`)

**Autor:** Borja Fernández Angulo (*Investigador en Sistemas Complejos*)  
**Ámbito:** `BABYLON-60-VAULT` (`origin`) $\leftrightarrow$ Proyección Pública Acotada (`public`)  
**Estado:** Vigente · Gobernanza Determinista de Evidencias (AX-0 / O1)

---

## 1. Arquitectura de Retención Dual y Confinamiento OPSEC

Por diseño de seguridad operativa (**OPSEC**) e higiene del espejo público (`INV_C5_DUAL_REMOTE` y `Zero Historical Bloat`), los lotes crudos de auditoría adversarial, trazas forenses de hardware y bibliotecas internas se conservan íntegramente en la bóveda privada (**`BABYLON-60-VAULT`**) y se excluyen de forma determinista de la proyección pública (**`BABYLON-60`**) mediante [`scripts/c5_git_utils/c5_distill_public_mirror.sh`](../scripts/c5_git_utils/c5_distill_public_mirror.sh) y [`scripts/verify_release.sh`](../scripts/verify_release.sh).

Esta separación garantiza que:
1. Los informes técnicos en [`docs/security/`](../docs/security/) preserven sus referencias exactas y sus compromisos criptográficos (`SHA-256` / `BLAKE3`) sin alterar las actas originales.
2. El espejo público no exponga trazas locales de host, topologías internas de red, payloads de reproducción de vulnerabilidades ni artefactos binarios pesados, manteniendo un árbol público verificable y auditable en `< 20 MB`.

---

## 2. Inventario de Lotes Bajo Custodia en Bóveda (`docs/security/evidence/`)

Los enlaces relativos a `evidence/...` dentro de [`docs/security/`](../docs/security/) resuelven directamente sobre `docs/security/evidence/` en el árbol completo de `BABYLON-60-VAULT`:

| Categoría de Evidencia | Ruta en `BABYLON-60-VAULT` | Artefactos Custodiados | Política en Proyección Pública |
| :--- | :--- | :--- | :--- |
| **Campañas Swarm100 (Rondas 1–3 y Lotes 1–13)** | `docs/security/evidence/swarm100-*` | Registros reconciliados (`registry.json`), colas de remediación, reproducciones pre/post-parche, revisiones independientes y logs de regresión (`related-tests.log`). | Retenido en Vault (`is_excluded_from_public_tree`). Hashes publicados en actas `AUDIT_SWARM100_*.md` y `REMEDIATION_SWARM100_*.md`. |
| **Auditorías de Integración Local y Concurrencia** | `docs/security/evidence/local-core-20261030/`<br>`docs/security/evidence/pending-local-audit-20261030/`<br>`docs/security/evidence/concurrent-main-audit-20261030/` | Recibos de hardware (`hardware-receipt.json`), pruebas firmadas, consolidación concurrente y anclajes de solver SMT. | Retenido en Vault. Resumen verificable en `LOCAL_CORE_INTEGRATION_2026-10-30.md` y `AUDIT_PENDING_COMMITS_2026-10-30.md`. |
| **Auditorías de Arnés, Recuperación y Regulación** | `docs/security/evidence/harness-audit-2026-10-24/`<br>`docs/security/evidence/external-audit-remediation-2026-10-24/`<br>`docs/security/evidence/regulatory-native-20261030/`<br>`docs/security/evidence/recovery-audit-2026-10-26.rs` | Controles negativos, estado de migración de claves, desafío regulatorio EU AI Act y pruebas de recuperación. | Retenido en Vault. Referenciado desde `harness-audit-2026-10-24.md`, `EU_AI_ACT_NATIVE_2026-10-30.md` y `fl-rec01-recovery-provenance.md`. |
| **Paquetes de Validación de Plataforma (Fuera de Árbol Git)** | `~/.babylon60/validation/cognitive-pilot-20261023/`<br>`~/.babylon60/validation/integration-platforms-20261023/` | Tarballs locales (`cognitive-pilot-evidence-20261023.tar.gz`, `linux-arm64-evidence-20261023.tar.gz`) con logs completos y JUnit XML. | Custodia local fuera del árbol de fuentes; digests `SHA-256` publicados en sus respectivos informes. |
| **Biblioteca Portable de Skills** | `tools/skill_library/` | Distribución multi-entorno (`global/`, `workspace/`, `codex_overrides/`). | Excluida de la proyección pública ligera junto con sus pruebas (`tests/test_skill_library_convergence.py`, `tests/test_skill_intent_routing.py`, `tests/test_skill_maintenance.py`); auditada en CI solo donde el código fuente privado está presente. |

---

## 3. Verificación Independiente y Acceso a Sala de Datos Virtual (VDR)

1. **Verificación Pública sin Credenciales:** Los artefactos de cumplimiento público, manifiestos de versión ([`RELEASE_MANIFEST.json`](../RELEASE_MANIFEST.json)), inventario de afirmaciones ([`CLAIMS.toml`](../CLAIMS.toml)) y paquetes de verificación ([`proof/bundles/attestation_bundle_v1/`](../proof/bundles/attestation_bundle_v1/)) están incluidos en el repositorio público y pueden comprobarse mediante:
   ```bash
   python3 scripts/c5_quality_gates/verify_claims.py
   bash scripts/verify_release.sh
   ```
2. **Inspección de Evidencias Retenidas (Due Diligence / VDR bajo NDA):** Las entidades auditoras o contrapartes autorizadas pueden solicitar el paquete exportado del *Virtual Data Room* (`BABYLON60_DATA_ROOM`) o la verificación de hashes específicos contra la bóveda `BABYLON-60-VAULT` a través del canal institucional `access@babylon60.com`.
