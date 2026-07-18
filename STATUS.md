# STATUS — Fuente Única de Verdad

> Protocolo: C5-REAL · Generado: 2026-07-17 · Evidencia: `AUDITORIA_ENTROPIA_IDEAS_2026-07-17.md` (en disco, sin trackear)
> Regla de disciplina: **ninguna aserción de victoria fuera de este fichero.** Un claim sin hash/test/ledger es C4-SIM y no existe.

## Identidad

- Proyecto: **Teorema-Robinson-Moskv** (linaje local = canónico)
- Versión de proyecto: **1.0.2** — fuente única: `pyproject.toml`. `AGENTS.md` declara "Version: 1.1.0" pero es la versión del *documento de comportamiento*, no del proyecto: namespaces distintos, no hay conflicto (verificado 2026-07-17).
- HEAD: `f62135b` · 803 commits · rama `main` · sin remoto configurado (deliberado hasta resolver P0)

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
- [x] **BABYLON60 IDE v1.1.0 operativo end-to-end** (2026-07-17): contrato frontend↔backend reparado y verificado con Playwright contra `master_ledger.db` real (consenso 2/2 VERIFIED, 0 errores JS en ambos modos cognitivos).
- [x] **BABYLON60 IDE v1.2.0 — delegación REAL + CortexLedger propio** (2026-07-17): la delegación dejó de ser Teatro Verde (`localStorage`). Ahora `commit` ejecuta git de verdad (probado: commit real `53122e2` sellado por el motor) y `push/merge/ship/deploy` hacen **crash causal HTTP 423** mientras P0 esté abierto. El IDE lleva su propio CortexLedger append-only hash-chain SHA-256 (`babylon60_ide.db`, sidecar) y lo autoverifica. Nuevo eje DETERMINAR: analítica agregada + búsqueda Okapi BM25 léxica sobre payloads. E2E Playwright: 0 pageerrors en 7 rutas × 2 modos, search→detail OK, boot inmune a localStorage corrupto.
- [x] IDE sidecar: añadir `babylon60_ide.db*` al `.gitignore` del repo real (es el ledger local del IDE, no debe subir) (completado 2026-07-18).
- [ ] Si OPCIÓN B: colapso documental del remoto (§6 pasos 2–7 de la auditoría — ontologías, `.agents/` vacíos, MANIFESTO divergente)
- [ ] IDE: motor de inferencia local (TRANSFORMERS vía MLX/llama.cpp) + recuperación semántica por embeddings (`sqlite-vec`) — requiere capa Tauri v2/Rust (MOSKV-1-apex); fuera del runtime FastAPI actual. La búsqueda BM25 es el puente léxico determinista hasta entonces.

## Registro de mutaciones de este colapso

| Fecha | Mutación | Prueba |
|---|---|---|
| 2026-07-17 | Auditoría de entropía de ideas entregada | `AUDITORIA_ENTROPIA_IDEAS_2026-07-17.md` |
| 2026-07-17 | Runbook P0 v2 (claves + vault, un solo rewrite; opción A/B) | `COLLAPSE_P0.sh` |
| 2026-07-17 | STATUS.md como fuente única de verdad | este fichero + commit que lo introduce |
| 2026-07-17 | **BABYLON60 IDE v1.1.0**: contrato frontend↔backend reparado (stats/entries/verify/databases/query alineados con rutas reales), modo cognitivo dual NT○/2E◐ (⌘⇧E), Git Sentinel (`/api/sentinel/status`: identidad de repo recalcada en barra de estado + lineage guard con intuición de repo incorrecto + cola de delegación git 100% al agente), panel de detalle de entrada (micro-túnel), fix sockets zombi WS, fix RSS ru_maxrss (KB en Linux vs bytes en macOS), boot inmune a localStorage corrupto | `babylon60-ide/` · E2E Playwright: consenso VERIFIED 2/2 contra `master_ledger.db`, 0 pageerrors en 6 rutas × 2 modos · ruff limpio |
| 2026-07-17 | **BABYLON60 IDE v1.2.0**: CortexLedger real del IDE (`services/cortex_ledger.py`, append-only hash-chain SHA-256, UUIDv5, WAL); motor de delegación real (`routes/delegation.py`: git commit ejecutado de verdad + crash causal HTTP 423 en push/merge/ship/deploy por P0); analítica DETERMINAR (`routes/analytics.py`: agregación por stream/tipo/agente/continuidad-Lamport + búsqueda Okapi BM25 léxica); ruta Analytics (⌘7) + búsqueda→detalle; delegación cableada a API real (fin del Teatro Verde de localStorage) | commit real `53122e2` sellado por el motor · E2E Playwright: 0 pageerrors en 7 rutas × 2 modos · IDE CortexLedger autoverificado · ruff limpio · enjambre adversarial 3×2-votos |
| 2026-07-17 | **BABYLON60 IDE v1.2.1 — paleta + hardening del enjambre**: paleta recolapsada al brief neuro-inclusivo (carbón cálido `#0E0E16`, verde salvia, ámbar, terracota apagada, YInMn suavizado; `#000` y neón eliminados por halación/fatiga); paleta por modo (base calma para 2E, NT más nítido). Fixes del enjambre adversarial: append del CortexLedger **atómico** (`BEGIN IMMEDIATE` — evita fork de cadena bajo concurrencia, verificado 3× paralelo → 4/4 válido), guard de estado en `cancel()` (no pisa terminales), scan BM25 **acotado** (cap 5000 + reporta `truncated`), `_git` captura `ValueError` (NUL byte → error manejado, no 500) | E2E: 0 pageerrors en 7 rutas × 2 modos · ruff limpio |
| 2026-07-17 | **BABYLON60 Alcove — extensión de navegador MV3** (`babylon60-ide/extension/`): companion local-first del IDE. `popup` (sentinel/consenso/delegación real/BM25), `content` (tachómetro ambiental "notch" en el borde superior de cada pestaña), service worker (badge con nº de entradas + color por salud de linaje). Solo `localhost:8060`, paleta calma + modo dual | node --check limpio · popup renderizado contra backend (shapes reales) · lineage guard operativo en la extensión |
| 2026-07-18 | **BFT Consensus & Git Invariants**: Quórum de tolerancia a fallos corregido a $2f+1$. Se actualizaron las firmas del test harness a 2 votos corruptos para verificar fallas de quórum. Remediación del import de `os` en el agente de exergía. | `tests/test_itera2_invariants.py` · `scripts/exergy_optimizer_agent.py` · suite pytest 100% verde (217 passed) |
| 2026-07-18 | **Hardening de Gitignore**: Exclusión de archivos `babylon60_ide.db*` para asegurar que las bases de datos de sesión del IDE local nunca sean seguidas por Git. | `.gitignore` · commit `55348cc` |
