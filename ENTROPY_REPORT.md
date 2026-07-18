# PURGA DE ENTROPÍA — BABYLON-60 (v2 + v3)

> **Operación:** `purge/entropia-v2-2026-07-19` · **Fecha:** 2026-07-19
> **Base:** `main@462d9c25` · **Ejecutor:** Kimi K3 vía GitHub MCP
> **v2:** 23 archivos purgados · **v3:** guardián anti-reincidencia + incidente iconos

---

## 0. CONTEXTO: RESET DEL REPO ENTRE ITERACIONES

| Evento | Detalle |
| :--- | :--- |
| Iteración 1 (PR #553) | 19 archivos purgados sobre `main@5728210` |
| Reset total | Repo force-pusheado a otra línea temporal: 30+ ramas y PR #553 destruidos. Head oscilando: `bc224018` → `d22f24ef` → `462d9c25` (swarm mutando en vivo) |
| Iteración 2 (este PR) | Re-auditoría sobre el head vigente: entropía **reincidente** + nueva |
| Iteración 3 (este PR) | ENTROPY GUARD (hook pre-commit) + sellado de proceso |

## 1. PURGA v2 — 23 ARCHIVOS

### Reincidentes (purgados en v1, reaparecieron tras el reset)
- `main` — **vacío (0 bytes), 3ª línea temporal en la que reaparece**. Revisar el pipeline que lo genera (probable `git add -A` sobre redirect roto).
- `.agents/AGENTS.md` · `.snapshots/` (3) · `scratch/*.py` (2)
- `cortex/agents/ontology/centuria_bft_ledger.db` (331 KB, runtime)
- `src-tauri/gen/schemas/` (4, regenerados por tauri-build)
- `babylon60-ide/frontend/dist/` (9 — **3 bundles JS byte-idénticos**, mismo blob `48ee3ed`: builds sucesivos commiteados sin limpiar `dist/`)

### Nuevos
- `Dockerfile.bak` · `pyproject.toml.bak` (backups editoriales)

### Ya purgados por el propio swarm (verificado)
`C5_12_*.npz/.png/.json`, `shards.json`, `iteration_05_ledger.jsonl`, `AUDITORIA_*.md`, `visual-canvas.png`, `scratch_*.py` raíz.

## 2. SELLADO `.gitignore` v2
`*.bak` · `.snapshots/` · `babylon60-ide/frontend/dist/` · `src-tauri/gen/schemas/`
(las reglas de v1 murieron con el reset — **declarar `.gitignore` invariante en `AGENTS.md`**)

## 3. v3 — ENTROPY GUARD (anti-reincidencia)

La purga sin guardián es Sisifo (el `main` vacío lleva 3 reincidencias). Esta iteración instala el guardián:

- **`.githooks/pre-commit`** — bloquea: archivos 0 bytes (whitelist `__init__.py`, `.gitkeep`), `*.bak/tmp/swp`, `dist/*.{js,css,html}`, `src-tauri/gen/schemas/*`, `*.db*`, blobs >2MB. Override: `git commit --no-verify`.
- **`make install-hooks`** — activa `core.hooksPath .githooks` y da permiso de ejecución (la API no puede fijar el bit +x, por eso va en el Makefile).

## 4. INCIDENTE DECLARADO: `src-tauri/icons/32x32.png`

Los 6 iconos raíz eran **el mismo placeholder de 83 bytes** (PNG 32×32 vacío del template Tauri). En v3 intenté regenerarlos desde el logo real (`babylon60-ide/src-tauri/icons/icon.png`, 512×512) y descubrí que **la API MCP de esta sesión no puede escribir binarios** (guarda base64 como texto ASCII — verificado por round-trip en `create_or_update_file` y `push_files`).

Consecuencia: `32x32.png` quedó corrupto **solo en esta rama** (`main` intacto). Se ha eliminado de la rama para no arrastrar el archivo roto al merge.

**Restauración / fix real (local, 1 comando):**
```bash
git checkout main -- src-tauri/icons/32x32.png        # restaura el placeholder
cd src-tauri && cargo tauri icon ../babylon60-ide/src-tauri/icons/icon.png   # regenera TODO el set con el logo real
```

## 5. BRANCH PROTECTION (acción manual — la API de sesión no la expone)

La entropía de proceso (oscilación de heads, resets) solo muere con protección:
```bash
gh api -X PUT repos/borjamoskv/BABYLON-60/branches/main/protection \
  -f required_pull_request_reviews='{"required_approving_review_count":1}' \
  -f enforce_admins=false -F required_status_checks=null -F restrictions=null
```
Efecto: todo cambio entra por PR → adiós force-push anónimos, adiós oscilación.

## 6. NO PURGADO (criterio)
- `cortex/legal_dossier/` — custodia forense intencional con sellado hash
- `Anergy_Audit.yml`, docs raíz, `.py` raíz — invariantes `PROTECTED_FILES` del motor `cortex_purge_anergy.py`
- `index.html` raíz — landing protegida
- 5 iconos placeholder restantes — referenciados por `tauri.conf.json` (ver §4)

---
*Merge recomendado: **squash**. C5-REAL.*
