# AUDITORÍA ATÓMICA — Teorema-Robinson-Moskv

**Fecha:** 2026-07-16 · **Objetivo:** `~/10_PROJECTS/Teorema-Robinson-Moskv` · **Remoto:** `git@github.com:borjamoskv/Teorema-Robinson-Moskv.git`
**Método:** cada hallazgo lleva su comando reproducible. Cero teatro verde: lo que pasa, pasa; lo que falla, falla.

---

## 0. Colapso ejecutivo

| Eje | Estado | Dato duro |
|---|---|---|
| Seguridad app | **CRÍTICO** | Endpoint `/api/terminal` = RCE sin autenticación |
| Secreto en repo | **CRÍTICO** | `CORTEX_VAULT_KEY` en claro, tracked y en historial |
| Exposición legal/RGPD | **CRÍTICO** | `cortex/legal_dossier/` (32 ficheros): dossier fiscal + dato de salud + logs locales |
| Peso `.git` | **ALTO** | 1,5 GB por `.venv`/`target`/`mp4`/`safetensors` en historial |
| Higiene tracked | **ALTO** | 69.832 ficheros tracked; 57.099 son `batch_100k/iter_*.yaml` |
| Tests | **ALTO** | 555/563 pasan · **8 fallan** por acoplamiento al entorno del autor |
| Lint (ruff) | **BIEN** | 0 avisos |

**Verificación pendiente por ti (no resoluble desde sandbox):** ¿el repo es **público**? De ello depende que C1 y C2 sean "riesgo latente" o "brecha consumada". Compruébalo: GitHub → repo → badge Public/Private.

---

## 1. CRÍTICO

### C1. `/api/terminal` — ejecución remota de comandos SIN autenticación
`cortex/api/analysis.py:322`. El endpoint `POST /api/terminal` ejecuta la cadena recibida vía `subprocess.run(cmd, shell=True)` en **ambos** modos (agente GitHub y bash estándar, líneas 388 y 406).

Dos fallos que se componen:

1. **Sin auth.** La app define `verify_jwt` (HTTPBearer, línea 23) y lo aplica a `/facts` (`Depends(verify_jwt)`, línea 73) — pero **NO** a `run_terminal` (línea 323). La firma es `def run_terminal(payload: TerminalCmd)`, sin `Depends`/`Security`. Cualquiera que alcance el puerto ejecuta comandos.
2. **La única defensa es una denylist rota.** `validate_command_antipatterns` (línea 238) bloquea `sudo`, `| sh`, `2>/dev/null`, `cat >`, `./`… pero **no** bloquea `;`, `&&`, backticks ni `$()`. El modo bash exige además que `tokens[0]` no empiece por `/` y que no haya `..` — trivial de sortear.

**PoC (pasa todos los guards):** `git status; id`
```python
import shlex
c = "git status; id"; t = shlex.split(c)
# base='git' | starts '/': False | has '..': False | ';' no está en denylist → EJECUTA
```
Denylist es el enfoque equivocado: seguridad por lista negra siempre se elude. Un endpoint que corre shell arbitrario no debería existir; si debe existir, allowlist estricta de binarios + argumentos, `shell=False`, y auth obligatoria.

**Acción:** desactivar el endpoint o, mínimo, `Depends(verify_jwt)` + `shell=False` + allowlist. Denylist → papelera.
Repro: `sed -n '322,410p' cortex/api/analysis.py`

### C2. `CORTEX_VAULT_KEY` en claro, tracked y en historial
`.env.vault` está **tracked** y contiene la clave en texto plano:
```
CORTEX_VAULT_KEY="0hg-PwsyJHjNur5z7--PJmiIXLejkGTjB_wxJOxNe1g="
```
Es una clave Fernet/base64 usada por `bft/ledger_actor.py` y `scripts/bootstrap_cortex_memory.py`. Presente en el historial desde `3d2031cde`. Si el repo es público, está comprometida; aunque sea privado, vivir en git es incorrecto.
**Acción:** rotar la clave primero (reescribir historial sin rotar no sirve si ya se clonó) → sacar `.env.vault` de tracking → purgar del historial (`git filter-repo`) → cargar por variable de entorno.
Repro: `git show HEAD:.env.vault` · `git log --oneline -- .env.vault`

### C3. Dossier legal + datos de categoría especial RGPD versionados en un repo de código
`cortex/legal_dossier/` — 32 ficheros que no son código:
- Estrategia de defensa ante inspección fiscal (NFT 2021-2024): `ESCUDO_DEFENSA_INSPECCION_NFT_2021_2024.md`, `ESCRITO_ALEGACIONES_INSPECCION_HFB_NFT.md`.
- **Dato de salud (categoría especial, art. 9 RGPD):** `C5_RESUMEN_PERICIAL_HERMANA_LORENA.md`.
- Comunicaciones con abogado: `C5_MENSAJE_ACTUALIZADO_ABOGADO_RICARDO.md`, `EMAIL_RICARDO_AKORN_DOSSIER_TOTAL.md`.
- **Logs locales de Claude Code** con rutas `~/...`: 4 `.jsonl` bajo `claude_code_local_logs/`.
- OSINT/crónica de terceros: `DOSSIER_OSINT_ANTHROPIC_2026.md`, `LA_GUERRA_CON_ANTHROPIC_CRONICA_TOTAL.md`, `MEMORANDUM_INVESTIGACION_ARENA_Y_REVENG.md`.
- Capturas (`evidencias_capturas/`).

Su sitio es un vault cifrado fuera del repo, no `cortex/`. Con una inspección activa, tu estrategia de defensa sería legible por la contraparte si el repo es público.
**Acción:** mover a vault local, `git rm` + purga de historial.
Repro: `git ls-files cortex/legal_dossier | wc -l` → 32

---

## 2. ALTO

### A1. `.git` = 1,5 GB por artefactos que no deberían estar versionados
Blobs mayores del historial (`git rev-list --objects --all | git cat-file --batch-check`):

| Tamaño | Blob |
|---|---|
| 51,6 MB | `cortex/sota_arbitrage/.venv/.../chromadb_rust_bindings.abi3.so` |
| 46,2 MB | `adapters/0000100_adapters.safetensors` |
| 40,8 MB | `10_PROJECTS/cortex-nexus/public/assets/video.mp4` |
| 40,1 MB | `cortex/agents/ontology/autodidact_mega_batch.yaml` |
| 38,7 MB | `.../grpc/_cython/cygrpc.cpython-314-darwin.so` |
| 36,9 MB | `.../onnxruntime_pybind11_state.so` |
| 27,2 MB | `c5_remotion_video/out/video.mp4` |
| 15 MB ×N | `strike_rs/target/.../libzerocopy-*.rlib`, `rust_siege/target/...` |

**499 ficheros tracked** cuelgan de `node_modules/__pycache__/.venv/target/dist/build`. El `.gitignore` ya los excluye, pero se colaron antes de la regla.
**Acción:** una sola pasada de `git filter-repo` eliminando `*.venv*`, `*/target/*`, `*.so`, `*.dylib`, `*.mp4`, `*.safetensors`, `*/node_modules/*` → `.git` cae a decenas de MB. Force push + reclonar.
Repro: `du -sh .git` → 1,5G

### A2. 69.832 ficheros tracked; el 82 % es ontología generada
`git ls-files | wc -l` → **69.832**. Desglose de `cortex/ontology/` (295 MB): **57.099** ficheros en `batch_100k/iter_*.yaml` + 1.006 en `primitives/`. `cortex/agents/` añade 78 MB. El repo está dominado por output generado, no por código fuente; ralentiza clones, `git status`, e índices de IDE.
**Acción:** decidir si `batch_100k` es fuente o artefacto. Si es artefacto → fuera del repo (release/LFS/almacén aparte). Si es fuente → al menos empaquetar, no 57k ficheros sueltos.

### A3. Cuatro DBs SQLite tracked pese a `.gitignore`
`.gitignore` tiene `*.db`, pero estas se añadieron antes y siguen tracked:
`cortex/apex_centuria.db` (1,8 M), `nexus_go_insert_primitives.db`, `nexus_py_insert_primitives.db`, `nexus_rust_insert_primitives.db` (~356 K c/u).
**Acción:** `git rm --cached cortex/apex_centuria.db nexus_*_insert_primitives.db && git commit`.
Repro: `git ls-files | grep '\.db$'`

### A4. 8 tests fallan por acoplamiento al entorno del autor (555/563 pasan)
`pytest tests/` → **8 failed, 555 passed**. No es lógica rota; es dependencia de la máquina de Borja:

- `test_autonomic_daemon.py` (×3): `sqlite3.OperationalError: unable to open database file`. `cortex/agents/autonomic_daemon.py:23` conecta a `DB_PATH = ~/30_BABYLON-60/telemetry.db` (vía `BABYLON_ROOT`), ruta inexistente en cualquier clon. Sin fixture ni `skipif`.
- `test_layer_swap_simulator.py` (×2): `PermissionError: 'scratch/swap_buffer.bin'`. Escribe a ruta relativa no sandbox-safe.
- `test_hotstuff_consensus.py` (×3): usan `@pytest.mark.asyncio` pero **`pytest-asyncio` no está declarado** en `[project.optional-dependencies].dev`. Warning `PytestUnknownMarkWarning` → las corrutinas ni se ejecutan de verdad y el propose falla.

**Acción:** inyectar `DB_PATH`/`scratch` por fixture con `tmp_path`; añadir `pytest-asyncio>=0.23` a `dev`; marcar `skipif` lo que requiera entorno físico.
Repro: `python3 -m pytest tests/ -q --override-ini addopts=''`

---

## 3. MEDIO / BAJO

- **M1. 20 ficheros con `/Users/borjafernandezangulo` hardcodeado** (`.py`, `.yaml`). Rompe portabilidad. Repro: `git grep -l '/Users/borjafernandezangulo'`.
- **M2. Auto-anidamiento de rutas.** `Teorema-Robinson-Moskv/cortex/...` (2 ficheros tracked) y `borjamoskv/Teorema-Robinson-Moskv/...` en historial: copias del repo dentro del repo. Confunde imports y `filter-repo`.
- **M3. Submódulo ajeno `docs/aie-book`** (`github.com/chiphuyen/aie-book`). Un clon sin `--recursive` lo recibe vacío. Evaluar si aporta o si debe ser referencia externa.
- **B1. `validate_command_antipatterns` da falsa seguridad** (ver C1): documentar que NO es una barrera de seguridad, o eliminarla para no inducir confianza.

---

## 4. LO QUE ESTÁ BIEN

- **Ruff: 0 avisos** en todo el repo (excluyendo `.venv`). `python3 -m ruff check . --exclude .venv`.
- **555/563 tests pasan**; los 8 fallos son de entorno, no de lógica.
- **Sin `eval`/`exec` ni `bare except`** en código propio (`git grep` limpio fuera de dependencias).
- `verify_jwt` (HTTPBearer) existe y está bien construido — solo mal aplicado (C1).
- `.gitignore` es razonable; el problema es histórico (ficheros añadidos antes de las reglas).
- `pyproject.toml` declara dependencias reales (`networkx`, `numpy`, `pyyaml`, `aiosqlite`, `psutil`) y extras coherentes.

---

## 5. Plan priorizado (orden de ejecución)

1. **HOY — confirmar visibilidad del repo.** Si es público: privado inmediato. Neutraliza C2/C3 al instante.
2. **HOY — C1:** desactivar `/api/terminal` o blindarlo (auth + `shell=False` + allowlist).
3. **HOY — C2:** rotar `CORTEX_VAULT_KEY`, sacarla de `.env.vault`, moverla a entorno.
4. **C3:** mover `cortex/legal_dossier/` a vault fuera del repo.
5. **Una sola pasada `git filter-repo`** (A1 + C2 + C3 + M2): purgar `*.venv*`, `*/target/*`, `*.so/.dylib`, `*.mp4`, `*.safetensors`, `node_modules`, `.env.vault`, `cortex/legal_dossier/`, self-nesting. Force push + reclonar. `.git`: 1,5 GB → decenas de MB.
6. **A3:** `git rm --cached` de las 4 DBs.
7. **A4:** fixtures `tmp_path` + `pytest-asyncio` en `dev` → suite verde en clon limpio.
8. **A2:** decidir estatus de `batch_100k` (57k ficheros): fuente empaquetada o artefacto fuera del repo.

---
*Generado por auditoría atómica C5-REAL — cada afirmación verificada con comando reproducible sobre HEAD `bceb77654`.*
