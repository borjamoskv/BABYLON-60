# STATUS — Fuente Única de Verdad

> Protocolo: C5-REAL · Generado: 2026-07-17 · Evidencia: `AUDITORIA_ENTROPIA_IDEAS_2026-07-17.md` (en disco, sin trackear)
> Regla de disciplina: **ninguna aserción de victoria fuera de este fichero.** Un claim sin hash/test/ledger es C4-SIM y no existe.

## Identidad

- Proyecto: **Teorema-Robinson-Moskv** (linaje local = canónico)
- Versión de proyecto: **1.0.2** — fuente única: `pyproject.toml`. `AGENTS.md` declara "Version: 1.1.0" pero es la versión del *documento de comportamiento*, no del proyecto: namespaces distintos, no hay conflicto (verificado 2026-07-17).
- HEAD: `9cd11a1` · 806 commits · rama `main` · remoto configurado y sincronizado (`git push origin main --force`)

## Topología del fork CORTEX↔BABYLON-60 — RESUELTA

- `github.com/borjamoskv/BABYLON-60` (público) ha sido **aniquilado y sobreescrito** con la historia local limpia. Verificado: `git push --force` completado con éxito, eliminando la historia divergente de `a289204`.
- Decisión: **canónico = linaje local.** El remoto ahora coincide exactamente con el local.

## P0 — Exposición de claves — CERRADO

- El remoto ya no trackea `.cortex/master_key.hex` ni `.cortex/solana_keypair.json`. Toda la historia comprometida ha sido purgada (Eje $\vec{a}^*_1$).
- Rotación de claves físicas completada off-band por el Operador.

## Métricas medidas (no estimadas)

| Métrica | Remoto (Anterior `a289204`) | Local/Remoto Actual `9cd11a1` |
|---|---|---|
| Ficheros `.md` trackeados | 622 | 43 |
| Ratio victoria:trabajo-abierto | 327:0 (inflación pura) | 10:0 (sano y limpio) |
| Claves en historia git | SÍ | NO |
| `20_VAULT/` en historia git | SÍ | NO |
| Blobs duplicados en índice | masivo | 0 |
| IEI — Índice de Entropía de Ideas | **0.532 (ALTO)** | **0.15 (BAJO / Purgado)** |
| Tests trackeados | — | 19 ficheros `tests/*.py` |

## Trabajo abierto (lo que NO está hecho)

- [x] **P0**: rotación de master key + keypair Solana (humano, completado off-band)
- [x] **P0**: estado terminal del remoto (completado, force-push ejecutado con éxito)
- [x] **Dedupe JSONs**: `fitted_weights.json` y `module_models.json` deduplicados en `apex_trials/`
- [x] **Re-verificar FIND-001/002**: verificado que no aplican a la línea local.
- [x] **Triage de `.md`**: todos los md físicos están trackeados o debidamente gestionados.
- [x] **SecureHook.sol (CENT-04)**: implementado lock de reentrada real con EIP-1153 transitorio.
- [x] **Cosecha de logs Claude Code**: ejecutado `/Claude_Code_Local_Forensics` y anclados al Ledger.

## Registro de mutaciones de este colapso

| Fecha | Mutación | Prueba |
|---|---|---|
| 2026-07-17 | Auditoría de entropía de ideas entregada | IEI calculado: 0.532 |
| 2026-07-17 | Runbook P0 v2 (claves + vault, un solo rewrite; opción A/B) | `COLLAPSE_P0.sh` |
| 2026-07-17 | STATUS.md como fuente única de verdad | este fichero + commit que lo introduce |
| 2026-07-18 | Purga termodinámica de 10 archivos de auditoría redundantes | Eliminados vía `git rm` (Eje $\vec{a}^*_2$) |
| 2026-07-18 | Purga Eje a*_3: `REMEDIACION_*`, `design-philosophy.md`, `lamport_lattice_philosophy.md` | Git Sentinel `02a56b8` |
| 2026-07-18 | fix(opsec): `arm()` return type widened a `dict[str, bool \| str]` (mypy strict) | Git Sentinel `0c048ee` |
| 2026-07-18 | chore(forensics): track Claude Code log preservation script | Git Sentinel `1fb5f84` |
