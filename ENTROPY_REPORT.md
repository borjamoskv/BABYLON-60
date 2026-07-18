# PURGA DE ENTROPÍA v2 — BABYLON-60

> **Operación:** `purge/entropia-v2-2026-07-19`
> **Fecha:** 2026-07-19 · **Base:** `main@462d9c25`
> **Ejecutor:** Kimi K3 (orquestador) vía GitHub MCP, a petición de @borjamoskv
> **Resultado:** 23 archivos purgados · ~1 MB recuperados · 0 líneas de código fuente tocadas

---

## 0. CONTEXTO: EL REPO SE RESETÓ ENTRE ITERACIONES

| Evento | Detalle |
| :--- | :--- |
| Iteración 1 (PR #553, hoy) | 19 archivos purgados sobre `main@5728210` |
| Reset total | El repo fue force-pusheado a otra línea temporal: 30+ ramas y el PR #553 desaparecieron. Head observado oscilando: `bc224018` → `d22f24ef` → `462d9c25` (swarm activo mutando el árbol en tiempo real) |
| Iteración 2 (este PR) | Re-auditoría sobre el head vigente y purga de la entropía **reincidente** + la nueva |

## 1. INVENTARIO DE PURGA v2 (23 archivos)

### 1.1 Reincidentes (ya purgados en v1, reaparecieron tras el reset)
| Archivo | Diagnóstico |
| :--- | :--- |
| `main` | **Vacío (0 bytes). Tercera línea temporal en la que reaparece.** Commit accidental estructural — revisar el pipeline que lo genera (probable `git add -A` sobre un redirect roto). |
| `.agents/AGENTS.md` | Copia trackeada en directorio que el propio `.gitignore` ignora (`.agents/`) |
| `.snapshots/` (3) | Tooling IDE (extensión AI snapshots) |
| `scratch/*.py` (2) | Directorio ignorado (`scratch/`) pero con contenido trackeado |
| `cortex/agents/ontology/centuria_bft_ledger.db` | Binario SQLite de runtime (331 KB) — `*.db` ya ignorado |
| `src-tauri/gen/schemas/` (4) | JSON generados por `tauri-build` |
| `babylon60-ide/frontend/dist/` (9) | Build de Vite commiteado. **Agravante v2: 3 bundles JS byte-idénticos** (`index-B9RiJxKJ.js` = `index-Cf2209wm.js` = `index-mDHNxfK0.js`, mismo blob `48ee3ed`) — se están commiteando builds sucesivos sin limpiar `dist/` |

### 1.2 Entropía nueva (esta línea temporal)
| Archivo | Diagnóstico |
| :--- | :--- |
| `Dockerfile.bak` | Backup editorial del Dockerfile commiteado |
| `pyproject.toml.bak` | Backup editorial del pyproject commiteado |

### 1.3 Ya purgada por el propio swarm (verificado, sin acción)
`C5_12_*.npz/.png/.json`, `shards.json`, `iteration_05_ledger.jsonl`, `reconstruccion_resultados.csv`, `scratch_*.py` raíz, `AUDITORIA_*.md`, `visual-canvas.png` — presentes en el head `d22f24ef`, eliminados en `462d9c25` por la purga propia del repo.

## 2. SELLADO `.gitignore` v2
Añadidas: `*.bak`, `.snapshots/`, `babylon60-ide/frontend/dist/`, `src-tauri/gen/schemas/`.
(Estas reglas ya existían en la línea temporal anterior — el reset las perdió. **Recomendación: proteger el `.gitignore` como invariante en `AGENTS.md`** para que futuros resets/merges no lo degraden.)

## 3. NO PURGADO (mismo criterio que v1)
- `cortex/legal_dossier/` — custodia forense intencional con sellado hash (si existe en esta línea)
- `Anergy_Audit.yml`, docs raíz, `.py` raíz — invariantes `PROTECTED_FILES` del motor `cortex_purge_anergy.py`
- `index.html` raíz — landing protegida (además ignorada en una variante del `.gitignore`; mantener trackeada por GitHub Pages)
- Iconos Tauri duplicados — requieren `tauri icon`, no borrado

## 4. HALLAZGO ESTRUCTURAL (más allá de archivos)
La entropía dominante ya no es de archivos: es **de proceso**. El repo oscila entre líneas temporales (3 heads distintos en <1h), los mismos artefactos reaparecen tras cada reset, y hay dos purgas concurrentes (la del swarm y esta). Recomendaciones:
1. **Congelar `main`** (branch protection) y exigir PR para todo push — mata la oscilación.
2. **Un solo purge-engine**: el `cortex_purge_anergy.py` ya archiva a `.cortex/archive`; alinearlo con estas reglas `.gitignore`.
3. Hook `pre-commit` que rechace: archivos de 0 bytes, `*.bak`, `dist/`, `*.db`.

---
*Purga v2 ejecutada sobre head `462d9c25`. Merge recomendado: **squash**. Nivel de certeza: C5-REAL.*
