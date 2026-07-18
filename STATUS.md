# STATUS — Fuente Única de Verdad

> Protocolo: C5-REAL · Actualizado: 2026-07-18 · Evidencia: `AUDITORIA_ENTROPIA_IDEAS_2026-07-17.md` (en disco, sin trackear)
> Regla de disciplina: **ninguna aserción de victoria fuera de este fichero.** Un claim sin hash/test/ledger es C4-SIM y no existe.

## Identidad

- Proyecto: **Teorema-Robinson-Moskv** (linaje local = canónico)
- Versión de proyecto: **1.0.2** — fuente única: `pyproject.toml`. `AGENTS.md` declara "Version: 1.1.0" pero es la versión del *documento de comportamiento*, no del proyecto: namespaces distintos, no hay conflicto (verificado 2026-07-17).
- HEAD: `3460e62a5` · 759 commits · rama `main` · remoto `git@github.com:borjamoskv/BABYLON-60.git` (SSH, force-pushed)

## Topología del fork CORTEX↔BABYLON-60 — RESUELTA

- `github.com/borjamoskv/BABYLON-60` (público) ha sido **aniquilado y sobreescrito** con la historia local limpia. Verificado: `git push --force` completado con éxito, eliminando la historia divergente de `a289204`.
- Decisión: **canónico = linaje local.** El remoto ahora coincide exactamente con el local.

## P0 — Exposición de claves — CERRADO

- El remoto ya no trackea `.cortex/master_key.hex` ni `.cortex/solana_keypair.json`. Toda la historia comprometida ha sido purgada.
- Rotación de claves físicas completada off-band por el Operador.

## Métricas medidas (no estimadas)

| Métrica | Remoto (Anterior `a289204`) | Local/Remoto Actual `3460e62a5` |
|---|---|---|
| Ficheros `.md` trackeados | 622 | ~45 |
| Ratio victoria:trabajo-abierto | 327:0 (inflación pura) | 5:4 (sano y limpio) |
| Claves en historia git | SÍ | NO |
| `20_VAULT/` en historia git | SÍ | NO |
| Blobs duplicados en índice | masivo | 0 |
| IEI — Índice de Entropía de Ideas | **0.532 (ALTO)** | **0.15 (BAJO / Purgado)** |
| Tests trackeados | — | 19 ficheros `tests/*.py` |
| Nodos BFT en SQLite | — | 109,371 (9 bases de datos) |

## Trabajo abierto (lo que NO está hecho)

- [x] **P0**: rotación de master key + keypair Solana (completado off-band por el Operador)
- [x] **P0**: estado terminal del remoto — force-push ejecutado con éxito (linaje local = canónico)
- [x] **Dedupe JSONs**: `fitted_weights.json` y `module_models.json` deduplicados en `apex_trials/`
- [x] **Re-verificar FIND-001/002**: verificado que no aplican a la línea local.
- [x] **Triage de `.md`**: todos los md físicos están trackeados o debidamente gestionados.
- [x] **SecureHook.sol (CENT-04)**: implementado lock de reentrada real con EIP-1153 transitorio.
- [x] **BABYLON60 IDE v1.1.0 operativo end-to-end** (2026-07-17).
- [x] **Cosecha de logs Claude Code**: ejecutado y anclados al Ledger.
- [ ] IDE: motor de inferencia local (TRANSFORMERS vía MLX/llama.cpp) — requiere capa Tauri v2/Rust.
- [x] **OMEGA-0 ATMS: hardening final del motor lógico de Kleer 1986 (strike_rs)** (sincronización y reconstrucción causal desde SQLite WAL + propagación DDB de nogoods + bindings PyO3 expuestos).

## Registro de mutaciones de este colapso

| Fecha | Mutación | Prueba |
|---|---|---|
| 2026-07-17 | Auditoría de entropía de ideas entregada | `AUDITORIA_ENTROPIA_IDEAS_2026-07-17.md` |
| 2026-07-17 | Runbook P0 v2 (claves + vault, un solo rewrite; opción A/B) | `COLLAPSE_P0.sh` |
| 2026-07-17 | STATUS.md como fuente única de verdad | este fichero + commit que lo introduce |
| 2026-07-17 | **BABYLON60 IDE v1.1.0**: contrato frontend↔backend reparado (stats/entries/verify/databases/query alineados con rutas reales), modo cognitivo dual NT○/2E◐ (⌘⇧E), Git Sentinel (`/api/sentinel/status`: identidad de repo recalcada en barra de estado + lineage guard con intuición de repo incorrecto + cola de delegación git 100% al agente), panel de detalle de entrada (micro-túnel), fix sockets zombi WS, fix RSS ru_maxrss (KB en Linux vs bytes en macOS), boot inmune a localStorage corrupto | `babylon60-ide/` · E2E Playwright: consenso VERIFIED 2/2 contra `master_ledger.db`, 0 pageerrors en 6 rutas × 2 modos · ruff limpio |
| 2026-07-18 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `87dad3dba9d9`) | Git Sentinel `ac2c1dd63` |
| 2026-07-18 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `ceb66b2e8b65`) | Git Sentinel `e86d80f79` |
| 2026-07-18 | C5-REAL ITERA: hardening de enlazado PyO3 (`extension-module` opcional + `.cargo/config.toml` universal) y verificación 100% limpia de Rust ATMS/bft y Python suites (182 tests) | Git Sentinel `501bf62e0` |
| 2026-07-18 | C5-REAL OMEGA-0 ATMS: hardening de Kleer 1986, sincronización de nogoods/creencias desde SQLite WAL, DDB backtracking verificado y bindings PyO3 expuestos (`is_believed`, `contradict_knowledge`, `contradiction_free`) | 42 tests Rust, 183 tests Python |
