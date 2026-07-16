# AUDITORÍA ATÓMICA — Teorema-Robinson-Moskv
Fecha: 2026-07-16 · HEAD: `bceb776` · Medición directa sobre working tree y objeto git.

## 1. MASA

| Métrica | Valor | Causa |
| :--- | :--- | :--- |
| Working tree | ~6.3 GB | `cortex/` = 5.9 GB |
| Pack git | **738.51 MiB** | Binarios en historia |
| Ficheros tracked | 69,832 | 69,508 (99.5%) bajo `cortex/` |
| Dirty | 50 modificados + 2 untracked | `BABYLON-60-fixes/patches-es/*` sin commit |

Los dos sumideros dominantes NO están tracked pero viven en el working tree:
`cortex/training/baby-long/models` (3.9 GB) y `cortex/ledger/stress_test_100M.db` (1.1 GB).

## 2. CONTAMINACIÓN DEL ÍNDICE GIT

- **499 artefactos de build tracked**: `cortex/daemons/rust_siege/target/`, `cortex/consensus/target/`, `proof/lean/.lake/`. Causa: `.gitignore` solo cubre `/target` (raíz) y `strike_rs/target/`, no `**/target/` ni `.lake/`.
- **4 `.db` tracked** (`cortex/apex_centuria.db`, `nexus_{go,py,rust}_insert_primitives.db`) + `C5_12_divergencia.npz`, pese a la regla `*.db`: fueron añadidos antes de la regla; git no expulsa lo ya indexado.
- Residuos raíz: `main` (0 bytes), directorio anidado `Teorema-Robinson-Moskv/Teorema-Robinson-Moskv/`.

## 3. CÓDIGO Y PRUEBAS

- Fuente tracked (sin vendor/build): 151 py · 58 sol · 8 rs · 7 go · 5 sh · 4 js · 3 ts/tsx · 1 lean.
- **547 tests colectados** en 42 ficheros. Dos módulos (`test_onco_transducer.py`, `test_voice_transducer.py`) **rompen la colección completa** por dependencia no declarada (`networkx`): un `pytest` desnudo aborta antes de ejecutar nada.
- CI: 9 workflows (`ci.yml`, `verify_lean.yml`, `verify_ledger.yml`, `codeql.yml`…). Cobertura de superficie correcta.
- Secretos: limpio. `GEMINI_API_KEY` se lee de entorno (`autocatalytic_10000x_loop.py:70`), sin claves hardcodeadas ni `.env`/`.pem` tracked.

## 4. PRUEBA FORMAL (`proof/lean/Babylon.lean`)

Verificado: 52 líneas, 6 teoremas, **cero `sorry`, cero `axiom`** — el claim del encabezado es cierto.

Gap causal: los teoremas demuestran reflexividad, transitividad y antisimetría de `≤` sobre `ℕ` (envoltorios de `Nat.le_refl/le_trans/le_antisymm` del core). Es un modelo honesto del orden de Lamport, pero **no existe vínculo mecánico con `bft/ledger_actor.py`**: nada obliga a que la implementación Python respete el modelo. El README declara "validación matemática formal" con confianza C5; la evidencia soporta C5 para el *modelo*, no para el *sistema*.

## 5. ACCIONES (orden causal de impacto)

1. **Purgar índice**: `git rm -r --cached` sobre los 499 artefactos + 4 `.db` + `.npz`; ampliar `.gitignore` con `**/target/`, `**/.lake/`, `*.npz`. Reduce ruido de diff y previene recontaminación.
2. **Historia**: los 738 MiB de pack solo bajan con `git filter-repo` (reescritura). Decisión: coste de re-clone vs. clones de 700 MB para siempre.
3. **Externalizar masa**: `baby-long/models` (3.9 GB) y `stress_test_100M.db` (1.1 GB) → LFS/DVC o fuera del árbol.
4. **Cerrar el dirty state**: commit o descarte de los 50 patches-es modificados. Estado indefinido = deriva.
5. **Declarar `networkx`** (y deps de test) en `pyproject.toml` [test]; hoy la suite es inejecutable en entorno limpio.
6. **Cerrar el gap Lean↔Python**: extraer los invariantes reales del `BFTLedgerActor` (monotonía de `lamport_t`, integridad del hash-chain) y probarlos en Lean contra una especificación compartida, o rebajar el claim del README a "modelo formal del orden causal".

## 6. VEREDICTO

Sin secretos expuestos, prueba Lean honesta, CI amplia. Los fallos son de **termodinámica de repositorio**: 738 MiB de historia, 499 artefactos indexados, 5 GB de masa no versionada dentro del árbol, y una suite de tests que no arranca en frío. Exergía recuperable con las acciones 1–5 en una sesión.
