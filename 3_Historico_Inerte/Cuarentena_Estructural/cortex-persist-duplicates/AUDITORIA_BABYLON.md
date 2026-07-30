# AUDITORÍA BABYLON-60

**Fecha:** 2026-07-06 · **HEAD:** `4f236e75e` (main) · **Alcance:** repo completo (a diferencia de `FINAL_AUDIT.md` del 30-06, que solo cubrió `cortex/`, 552 LOC de los ~270.000 LOC de `babylon60/`)

## Resumen ejecutivo

El código en sí está razonablemente sano (1.588 tests pasan, solo 11 TODOs, secretos purgados). El problema es el **repositorio como artefacto**: un `.git` de 9,2 GB, ~284 MB de audio suelto en la raíz, triple gestión de dependencias y 19 ramas muertas. Es un problema de higiene y operabilidad, no de calidad de código.

## Hallazgos

### 🔴 Críticos

**1. `.git` de 9,2 GB.** Dos packs de 2,3 GB + uno de 704 MB. Hay binarios grandes en la historia (audio/vídeo/archives). Clonar este repo es inviable y GitHub lo rechazará o degradará. Requiere `git filter-repo` + LFS para media. Tras la purga debería quedar en <100 MB.

**2. Archivos SQLite `:memory:` filtrados a disco.** 9 archivos en la raíz tipo `:memory:0ede9928...` y `file:mem_1e4cde7b?mode=memory&cache=shared-wal` (1,5 MB). Algún código pasa la URI de memoria como nombre de archivo (falta `uri=True` o equivalente en aiosqlite), creando bases de datos literales en disco. Existe `tools/refactor_aiosqlite.py`, así que el problema es conocido pero no está resuelto.

### 🟡 Importantes

**3. 10 tests rotos** (de 1.638): `test_distributed_event_bus` (redis stream), `test_oracle::verify_ledger_continuity`, `test_cortex_analysis_api::facts_endpoint_invalid_auth` (auth ⚠️), `test_pipeline_orchestrator::ledger_failure`, 3 en `test_builtin_agents`, `test_adk_agents`, `test_hito_3_5_sanedrin` (lease locks), `test_sync_mixin_concurrency`. Los de auth y ledger merecen prioridad.

**4. Raíz saturada: 79 archivos**, incluyendo `audio_RRtfriNpUrE.wav` (266 MB) + `.mp3` (18 MB) sin trackear, 3 logs `pytest_failures*.log`, transcripts, `video_info.json` (743 KB), `.DS_Store`.

**5. Triple gestión de dependencias:** `pyproject.toml` + `reqs.txt` (933 líneas, pip freeze) + `uv.lock`. Fuente de verdad ambigua; `reqs.txt` sobra.

**6. 19 ramas locales muertas**, muchas generadas por bots con duplicados (`refactor-contradiction-guard-*` ×3, `fix-enable-load-extension-*` ×2), más 13 cambios sin commitear (2 archivos de código modificados: `training/daemon.py`, `exergy_guard.py`).

### 🟢 Menores

**7. Duplicación estructural:** `cortex/` (32 KB) vs `cortex-system/` (6,3 MB) vs `babylon60/` (42 MB); `labs/distributed-os` vs `labs/distributed-cognitive-os`; `experimental/` (55 MB) con `_archive`, `scratch` y `.scratch`; `naroa_archive/` (250 MB) que no parece pertenecer al proyecto.

**8. 225 directorios `__pycache__`** y cachés varias (`.pytest_cache`, `.ruff_cache`, `.hypothesis`) en el working tree.

**9. Peso total en disco ≈ 13 GB**, del cual el código real es una fracción mínima: `.git` 9,2 GB, `.venv` 2,4 GB, `node_modules` 616 MB, audio 284 MB, `naroa_archive` 250 MB, `.venv-docs` 133 MB.

### ✅ Correcto

Secretos purgados en `.env`/`.env.local` (`[PURGED_BY_CORTEX...]`; los valores Stripe son placeholders). Sin claves hardcodeadas en código trackeado (lo único que aparece son fixtures de `test_memory_firewall.py`, que verifica que el firewall las redacta). Deuda declarada baja (11 TODO/FIXME en 10 archivos). Gobernanza presente: `SECURITY.md`, `CONTRIBUTING.md`, `REPO_GOVERNANCE.md`, CI en `.github`.

## Plan de acción recomendado

| # | Acción | Impacto | Esfuerzo |
|---|--------|---------|----------|
| 1 | Sacar media de la raíz (wav/mp3/transcripts → fuera del repo o LFS) | Alto | 10 min |
| 2 | `git filter-repo` para purgar binarios de la historia + LFS | Alto | 1-2 h |
| 3 | Arreglar bug `:memory:`/`file:mem_` (aiosqlite `uri=True`) y borrar los 9 archivos | Alto | 30 min |
| 4 | Reparar los 10 tests rotos (empezar por auth y ledger) | Medio | 2-4 h |
| 5 | Borrar 19 ramas muertas y commitear/descartar los 13 cambios pendientes | Medio | 15 min |
| 6 | Eliminar `reqs.txt`; consolidar en `pyproject.toml` + `uv.lock` | Medio | 15 min |
| 7 | Ampliar `.gitignore`: `:memory:*`, `file:mem*`, `*.wav`, `pytest_failures*`, `video_info.json` | Bajo | 5 min |
| 8 | Consolidar `cortex*`/`labs/*`/`experimental/` y decidir destino de `naroa_archive` | Bajo | variable |
