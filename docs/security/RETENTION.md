# Política de Retención y Custodia de Evidencias de Seguridad (`docs/security/RETENTION.md`)

**Autor:** Borja Fernández Angulo (*Investigador en Sistemas Complejos*)  
**Ámbito:** `docs/security/` y `docs/security/evidence/`  
**Referencia Raíz:** [`../../evidence/README.md`](../../evidence/README.md)

---

## 1. Regla de Exclusión en Proyección Pública

Todos los artefactos bajo `docs/security/evidence/` (incluyendo los lotes `swarm100-*`, `local-core-*`, `pending-local-audit-*`, `harness-audit-*`, `external-audit-remediation-*`, `regulatory-native-*`, `concurrent-main-audit-*` y `recovery-audit-*`) forman parte del registro forense interno en **`BABYLON-60-VAULT`** (`origin/main`).

Durante la destilación de la proyección pública acotada ([`scripts/c5_git_utils/c5_distill_public_mirror.sh`](../../scripts/c5_git_utils/c5_distill_public_mirror.sh)), el directorio `docs/security/evidence/` se excluye deliberadamente y su ausencia en el árbol público es verificada como invariante de seguridad por [`scripts/verify_release.sh`](../../scripts/verify_release.sh) y [`tests/test_release_verification.py`](../../tests/test_release_verification.py).

## 2. Resolución de Enlaces y Verificación de Digests

- **En `BABYLON-60-VAULT`:** Todos los enlaces relativos `evidence/<lote>/<archivo>` dentro de `docs/security/*.md` resuelven localmente sobre `docs/security/evidence/<lote>/<archivo>`.
- **En la Proyección Pública (`BABYLON-60`):** La cláusula canónica de custodia y el inventario de categorías retenidas se encuentran en [`evidence/README.md`](../../evidence/README.md).
- **Evidencias de Validación en Host (`~/.babylon60/validation/`):** Los paquetes comprimidos generados por `cognitive_pilot` y `validate_linux_arm64.sh` se almacenan fuera del árbol Git con sus digests `SHA-256` sellados en [`cognitive-pilot-real-evaluation-2026-10-23.md`](cognitive-pilot-real-evaluation-2026-10-23.md) y [`linux-arm64-validation-2026-10-23.md`](linux-arm64-validation-2026-10-23.md).
- **Solicitud de Acceso VDR / NDA:** Contacto institucional exclusivamente vía `access@babylon60.com`.
