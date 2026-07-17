# STATUS — Fuente Única de Verdad

> Protocolo: C5-REAL · Generado: 2026-07-17 · Evidencia: `AUDITORIA_ENTROPIA_IDEAS_2026-07-17.md` (en disco, sin trackear)
> Regla de disciplina: **ninguna aserción de victoria fuera de este fichero.** Un claim sin hash/test/ledger es C4-SIM y no existe.

## Identidad

- Proyecto: **Teorema-Robinson-Moskv** (linaje local = canónico)
- Versión de proyecto: **1.0.2** — fuente única: `pyproject.toml`. `AGENTS.md` declara "Version: 1.1.0" pero es la versión del *documento de comportamiento*, no del proyecto: namespaces distintos, no hay conflicto (verificado 2026-07-17).
- HEAD: `0c048ee` · 805 commits · rama `main` · sin remoto configurado (deliberado hasta resolver P0)

## Topología del fork CORTEX↔BABYLON-60 — RESUELTA

- `github.com/borjamoskv/BABYLON-60` (HEAD `a289204`, público) es un **fork de publicación muerto**: historia NO relacionada con el linaje local. Verificado: `git cat-file -t a289204` → objeto inexistente en local; `merge-base --is-ancestor` → NOT-ANCESTOR.
- Decisión: **canónico = linaje local.** El remoto queda pendiente de estado terminal — OPCIÓN A (borrar/reemplazar: aniquilación total de su entropía) u OPCIÓN B (purga quirúrgica y sigue vivo como corpus doc). Runbook: `COLLAPSE_P0.sh` (v2).

## P0 — Exposición de claves — ABIERTO (bloqueado en acción humana)

- El remoto trackea `.cortex/master_key.hex` (256-bit) y `.cortex/solana_keypair.json` en `a289204`, repo público → **ambas claves comprometidas por definición**. Rotación manual pendiente.
- El remoto trackea `20_VAULT/` (PKM/CRM/OSINT con individuos nombrados) → exposición de privacidad; purga incluida en el mismo rewrite.
- El linaje local **jamás** trackeó claves ni vault (`git log --all -- <path>` vacío para los tres paths).
- Secuencia: rotar claves → elegir estado terminal (A/B) → ejecutar `COLLAPSE_P0.sh --confirm-history-rewrite` si B.

## Métricas medidas (no estimadas)

| Métrica | Remoto `a289204` | Local `f62135b` |
|---|---|---|
| Ficheros `.md` trackeados | 622 | 49 |
| Ratio victoria:trabajo-abierto | 327:0 (inflación pura) | 10:55 (sano) † |
| Claves en historia git | SÍ | NO |
| `20_VAULT/` en historia git | SÍ | NO |
| Blobs duplicados en índice | masivo (fork de renombrado) | 0 (deduplicados a `apex_trials/`) |
| IEI — Índice de Entropía de Ideas | **0.532 (ALTO)** | no medido (corpus 12,7× menor) |
| Tests trackeados | — | 19 ficheros `tests/*.py` |

† Instrumentos de regex ligeramente distintos entre corpus (el remoto se midió con el set DONE/VICTORY ampliado); el orden de magnitud y el signo de la inversión son válidos.

## Trabajo abierto (lo que NO está hecho)

- [ ] **P0**: rotación de master key + keypair Solana (humano, irreversible, primero)
- [ ] **P0**: estado terminal del remoto — OPCIÓN A o B + force-push/borrado
- [x] **Dedupe JSONs**: `fitted_weights.json` y `module_models.json` deduplicados en el path canónico `apex_trials/` (completado 2026-07-17).
- [x] **Re-verificar FIND-001/002**: verificado que no aplican a la línea local; los ficheros vulnerables del remoto (`swarm/state_store.py`, Stripe webhooks) no existen en este linaje.
- [x] **Triage de `.md`**: todos los md físicos están trackeados, ignorados en `.gitignore` (`.agents/`, `.pytest_cache/`, etc.) o pertenecen al submódulo Git `docs/aie-book`.
- [x] **SecureHook.sol (CENT-04)**: implementado lock de reentrada real con EIP-1153 transitorio (tstore/tload) y control de errores en `contracts/test/SecureHook.sol`.
- [ ] Si OPCIÓN B: colapso documental del remoto (§6 pasos 2–7 de la auditoría — ontologías, `.agents/` vacíos, MANIFESTO divergente)

## Registro de mutaciones de este colapso

| Fecha | Mutación | Prueba |
|---|---|---|
| 2026-07-17 | Auditoría de entropía de ideas entregada | IEI calculado: 0.532 |
| 2026-07-17 | Runbook P0 v2 (claves + vault, un solo rewrite; opción A/B) | `COLLAPSE_P0.sh` |
| 2026-07-17 | STATUS.md como fuente única de verdad | este fichero + commit que lo introduce |
| 2026-07-18 | Purga termodinámica de 10 archivos de auditoría redundantes | Eliminados vía `git rm` (Eje $\vec{a}^*_2$) |
| 2026-07-18 | Purga Eje a*_3: `REMEDIACION_*`, `design-philosophy.md`, `lamport_lattice_philosophy.md` | Git Sentinel `02a56b8` |
| 2026-07-18 | fix(opsec): `arm()` return type widened a `dict[str, bool \| str]` (mypy strict) | Git Sentinel `0c048ee` |
