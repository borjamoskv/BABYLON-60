# Auditoría técnica — moskv-1-apex
**Fecha:** 2026-07-13 · **Auditadas:** `~/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/moskv-1-apex` (10P), `~/moskv-1-apex` (HOME), GitHub `borjamoskv/moskv-1-apex`

---

## 1. Estado de las copias — hay TRES versiones divergentes

| Copia | HEAD | Fecha | Estado |
|---|---|---|---|
| **GitHub master** | `72874b0` | — | La más avanzada. Ninguna copia local la tiene. |
| **10P** (10_PROJECTS) | `dd42b20` (130 commits) | 8 jul | Casi canónica: le falta ≥1 commit de GitHub. |
| **HOME** (~) | `eb69e63` (123+1 commits) | 13 jul | Obsoleta (base 18 jun) **+ 1 commit sin pushear** + 1.647 borrados sin commitear (naroa-vision/node_modules). |

- El commit huérfano del HOME es `eb69e63` — *fix(metacognition): strict integer parsing FREEZE_MS* (toca solo `kernel/metacognition.js`). **Rescatarlo con cherry-pick antes de descartar esa copia.**
- Copia canónica recomendada: **10P** tras `git fetch && git pull`. La HOME debería archivarse o eliminarse para dejar de trabajar en dos sitios.

## 2. Hallazgos CRÍTICOS

### C1. El repo es PÚBLICO y contiene tu dossier de defensa fiscal
Verificado: GitHub lo marca `public` (1 estrella, indexable). Tracked y visibles ahora mismo:

- `docs/INFORME_FISCAL_ABOGADO.md` — estrategia de defensa completa ante Hacienda Bizkaia: escenarios económicos (optimista/moderado/pesimista), estrategia IVA/IRPF y **dato de salud (diagnóstico TDAH como atenuante)** — categoría especial RGPD.
- `Dossier_Defensa_Fiscal/` (memo al abogado, checklist) y `Dossier_Abogado_BorjaMoskv.zip`.

Con una inspección activa (Bizkaia 2026), tu estrategia de defensa es legible por cualquiera, incluida la Administración. **Acción hoy: Settings → hacer el repo privado.** Después, purgar estos ficheros del historial. Su sitio es `20_VAULT/.../00_CONSOLIDACION_MOSKV_APEX`, no un repo de código.

### C2. Clave criptográfica recuperable del historial público
El commit `4a780ef` ("purge critical leaks") solo dejó de *trackear* `kernel/crypto/pq_seed.key` (128 B), `cortex.db` y `swarm_os.sqlite`: siguen íntegros en el historial (`git show 4a780ef^:kernel/crypto/pq_seed.key` la devuelve entera). En un repo público, la clave está comprometida.
**Acción: rotar la clave (regenerar) + reescribir historial con `git filter-repo` o BFG + force push.** Rotar primero: reescribir sin rotar no sirve si alguien ya la clonó.

## 3. Hallazgos ALTOS

- **A1. `.git` de 527 MB** (repo total 599 MB): ~300 MB de mp4 (`apps/brt-video/out/*.mp4`), `node_modules` y artefactos Rust purgados del working tree pero vivos en el historial. Se arregla con la misma pasada de filter-repo/BFG de C2.
- **A2. 72 MB de media aún tracked**: `remix_project/*.wav|mp4` (~64 MB) + el zip del dossier. Untrack + LFS o fuera del repo.
- **A3. Dependencias sin declarar**: `pyproject.toml` dice `dependencies = []` pero el código requiere `aiohttp` y `neo4j`. Quien clone no puede ejecutar ni testear sin adivinarlas.
- **A4. Tres submódulos rotos** (gitlinks mode 160000 sin `.gitmodules`): `MOSKV-1`, `borjamoskv_wiki`, `mac-maestro`. Cualquier clon los recibe como directorios vacíos/error; en 10P aparecen como "deleted" permanentes en `git status`.

## 4. Hallazgos MEDIOS/BAJOS

- 18 `.pyc` tracked; `.gitignore` sin `__pycache__/`, `node_modules/`, `.venv/`, `*.pyc`.
- Credenciales por defecto `neo4j/password` hardcodeadas en `docker-compose.yml` y como default en `src/moskv_1/memory.py` (solo localhost → riesgo bajo, pero en repo público es una pista regalada).
- `install.sh` promociona `curl | bash` (patrón desaconsejado, decisión tuya).
- `cortex_hijack.js`: revisado, benigno (skin de console.log).

## 5. Lo que está BIEN

- **Tests: 22/22 pasan** (pytest, con deps instaladas a mano).
- **Ruff: solo 3 avisos menores** (E402, E701, F401) en todo el repo.
- Los commits de "apoptosis de antipatrones" cumplieron: cero `shell=True`, `eval/exec`, `bare except` o `mutable default` en `src/`.
- Stripe correcto: claves por env var con fallback mock explícito, verificación de firma del webhook.

## 6. Plan de acción priorizado

1. **HOY — repo a privado** (GitHub → Settings → Danger Zone). Coste: 1 min. Elimina la exposición C1/C2 de inmediato.
2. **HOY — rotar `pq_seed.key`.**
3. Rescatar `eb69e63` de HOME: `git cherry-pick` sobre 10P actualizada.
4. Consolidar: 10P `git fetch && git pull`, verificar tests, archivar la copia HOME.
5. Reescritura de historial (una sola pasada): eliminar `*.mp4`, `Dossier*`, `docs/INFORME_FISCAL_ABOGADO.md`, `pq_seed.key`, `*.db`, `*.sqlite`, `node_modules`, `target/` → `.git` pasará de 527 MB a ~decenas de MB. Force push + reclonar.
6. `.gitignore` completo + untrack `.pyc` y media de `remix_project`.
7. `pyproject.toml`: `dependencies = ["aiohttp>=3.9", "neo4j>=5"]`.
8. Eliminar los 3 gitlinks rotos (`git rm --cached MOSKV-1 borjamoskv_wiki mac-maestro`) o convertirlos en submódulos reales.

---
*Nota: al ejecutar los tests quedaron 12 ficheros de caché `*.cpython-310*.pyc` en `__pycache__/` de esta copia que no pude borrar por permisos. Son inofensivos; bórralos cuando quieras.*

---

## 7. VERIFICACIÓN DE ESTADO — 2026-07-13 (segunda pasada)

### 🔴 CRÍTICO SIN RESOLVER: GitHub sigue PÚBLICO con el dossier fiscal visible
Verificado hoy: `github.com/borjamoskv/moskv-1-apex` sigue marcado **public** y en master siguen visibles `Dossier_Defensa_Fiscal/`, `Dossier_Abogado_BorjaMoskv.zip` y `docs/` (131 commits, historial SIN purgar). La purga se hizo solo en local: el remote de GitHub fue eliminado de la copia 10P (solo queda `home_repo`), así que **nada de la limpieza llegó a GitHub**. C1 y C2 siguen expuestos públicamente.

**Acción inmediata:** GitHub → Settings → Danger Zone → *Change visibility* → Private (o borrar el repo y re-crearlo desde la copia local purgada, que es más limpio: el historial público antiguo con la clave vieja y el dossier desaparece de verdad).

### ✅ Resuelto (en local)
- Clave rotada: `f602671` "rotate post-quantum seed after history purge".
- Historial local purgado: 0 rastros de dossier/INFORME_FISCAL/mp4; `.git` 527 MB → 198 MB.
- Cherry-pick de la metacognition fix hecho (`04ffb0c`).
- `cortex.db` ya no está tracked.

### ⚠️ Pendiente (en local, copia 10P)
1. `kernel/crypto/pq_seed.key` **sigue tracked** — aunque rotada, una clave no debe vivir en git. Untrack + gitignore.
2. `.gitignore` **no existe**. Añadir: `__pycache__/`, `*.pyc`, `node_modules/`, `.venv/`, `*.db`, `*.sqlite`, `*.key`.
3. 18 `.pyc` siguen tracked (7 aparecen como modified en cada `git status`).
4. `pyproject.toml`: `dependencies = []` sin corregir (faltan aiohttp, neo4j).
5. 3 gitlinks rotos siguen: `MOSKV-1`, `borjamoskv_wiki`, `mac-maestro`.
6. `.git` aún 198 MB: quedan blobs grandes purgables (caches de Chromium headless `apps/vector_zeta/headless_profile/` ~5 MB+, binarios `moskv-core` ~6 MB, `moskv_dag_core.so` 2,4 MB, `cortex_index.json` 3,8 MB).
7. Sin remote de GitHub configurado: decidir destino (repo nuevo privado recomendado) y push.
