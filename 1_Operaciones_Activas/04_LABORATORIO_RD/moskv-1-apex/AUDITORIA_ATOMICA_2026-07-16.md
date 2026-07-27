# AUDITORIA ATÓMICA — moskv-1-apex
**Fecha:** 2026-07-16 · **Tipo:** verificación de ejecución del plan 2026-07-13 + delta · **Fuentes:** copia 10P (rama `home-final`, HEAD `f602671`) + GitHub `borjamoskv/moskv-1-apex` (fetch en vivo, hoy)

---

## VEREDICTO

**1/7 completo · 3/7 parciales · 3/7 sin tocar.** La purga se ejecutó en el universo equivocado: se reescribió el historial LOCAL pero GitHub —el único lugar donde la exposición es real— conserva el historial completo sin purgar y **sigue siendo PÚBLICO**. El ítem de coste 1 minuto (repo → privado) lleva 3 días sin ejecutarse.

## CRASH CAUSAL #1 — C1 SIGUE VIVO (verificado hoy, en vivo)

GitHub responde `repository_public: true`. Visible ahora mismo en `master` (131 commits, historial antiguo íntegro):

- `Dossier_Defensa_Fiscal/` — completo
- `Dossier_Abogado_BorjaMoskv.zip` — en raíz
- `docs/` — con `INFORME_FISCAL_ABOGADO.md` (estrategia ante Hacienda Bizkaia + dato de salud, categoría especial RGPD)
- `kernel/crypto/pq_seed.key` ANTIGUA — recuperable del historial público (la reescritura local no llegó nunca a GitHub)

Causa raíz: en vez de force-push del historial purgado, se **eliminó el remote** `origin` de la copia local. Resultado: la purga local es termodinámicamente nula — cero efecto sobre la superficie expuesta. GitHub y local ya no comparten línea causal (GitHub master 131c · local master 130c `a9ed26e` · `home-final` divergente).

## CRASH CAUSAL #2 — LA CLAVE ROTADA SE VOLVIÓ A COMMITEAR

`f602671 chore(crypto): rotate post-quantum seed after history purge [mode 0600]` — la clave NUEVA (129 B) está **tracked** en `kernel/crypto/pq_seed.key`. `mode 0600` solo existe en disco: git no preserva permisos más allá del bit de ejecución. Es el mismo anti-patrón que originó C2. Cualquier push futuro de `home-final` la quema.

## ESTADO DEL PLAN 2026-07-13

| # | Ítem | Estado | Evidencia |
|---|---|---|---|
| 1 | Repo → privado | ❌ **NO** | `repository_public: true` hoy; dossier fiscal visible |
| 2 | Rotar `pq_seed.key` | ⚠️ Defectuoso | Rotada, pero re-commiteada (Crash #2); la antigua sigue pública (Crash #1) |
| 3 | Rescatar `eb69e63` (FREEZE_MS) | ✅ | Cherry-pick presente: `04ffb0c` en `home-final` |
| 4 | Consolidar 10P, archivar HOME | ⚠️ Parcial | Consolidado en `home-final` + snapshot `72b2aab`; pero HOME sigue viva como remote `home_repo` y el commit exclusivo de GitHub (`72874b0`, `com.moskv.nexus.plist`) NO se rescató |
| 5 | Reescritura de historial | ⚠️ Solo local | Local: fiscal/dossier/media/clave-antigua = 0 objetos alcanzables, `4a780ef` inexistente. Pero (a) no publicada (Crash #1); (b) `.git` = **198 MB** de pack con blobs muertos inalcanzables (18.8 + 15.3×4 + 12.3 MB…) → falta `git gc --prune=now` o reclone |
| 6 | `.gitignore` + untrack | ❌ **NO** | `.gitignore` vacío/ausente; **19 `.pyc` siguen tracked** (7 aparecen modificados ahora = ruido permanente); `node_modules/`, `cortex.db` sin ignorar |
| 7 | Declarar dependencias | ❌ **NO** | `pyproject.toml`: `dependencies = []` intacto |

**Persisten del informe anterior:** A4 (3 gitlinks rotos `MOSKV-1`, `borjamoskv_wiki`, `mac-maestro`, sin `.gitmodules`) · `NEO4J_AUTH=neo4j/password` ×2 en `docker-compose.yml`.

## DELTA 13→16 JUL

Cero commits desde `f602671` (13-jul 18:33). Working tree sucio: 26 entradas (7 `.pyc` modificados, `cortex.db`, `node_modules/`, `purge_history.sh`, `LICENSE.md`, informe anterior — todos sin trackear/ignorar).

## LO QUE ESTÁ BIEN (verificado hoy)

- **Tests 22/22 pasan** (pytest, deps `aiohttp`+`neo4j` instaladas a mano — el ítem 7 sigue siendo el motivo de "a mano").
- La reescritura local fue quirúrgicamente correcta en contenido: 0 objetos fiscal/dossier/media alcanzables desde cualquier ref local.
- Rescate FREEZE_MS ejecutado limpio.

## PLAN — ORDEN CAUSAL ESTRICTO

1. **AHORA (1 min):** GitHub → Settings → Danger Zone → **make private**. Todo lo demás es teatro mientras esto siga público. (0 forks, 1 star: ventana de clonación ajena baja, no nula.)
2. **Rotar la clave OTRA VEZ** y sacarla del repo definitivamente: `git rm --cached kernel/crypto/pq_seed.key` + `.gitignore` + carga por env/Keychain. La actual está commiteada → ya no vale como secreto de largo plazo.
3. **Rescatar `72874b0` de GitHub** (único commit que ninguna copia local tiene) antes del paso 4: `git remote add origin … && git fetch && git cherry-pick 72874b0`.
4. **Matar el historial público:** o force-push de `home-final` sobre master, o borrar el repo y recrearlo privado desde `home-final` (más limpio). Nota: GitHub puede retener vistas cacheadas de commits huérfanos un tiempo; si se quiere purga total de caché, ticket a soporte GitHub.
5. `git gc --prune=now --aggressive` (o reclone): 198 MB → decenas.
6. `.gitignore` real (`__pycache__/`, `*.pyc`, `node_modules/`, `*.db`, `*.sqlite`, `.venv/`) + `git rm --cached` de los 19 `.pyc`.
7. `pyproject.toml`: `dependencies = ["aiohttp>=3.9", "neo4j>=5"]`.
8. Submódulos: `git rm --cached MOSKV-1 borjamoskv_wiki mac-maestro` (o `.gitmodules` real).
9. `NEO4J_AUTH` por variable de entorno.
10. Archivar/eliminar `~/moskv-1-apex` (HOME) y el remote `home_repo`: una sola línea causal.

---
*Auditoría ejecutada en frío sobre la copia 10P montada + fetch HTTP en vivo del repo público. Sin mutaciones sobre el repo.*
