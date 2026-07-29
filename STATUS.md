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

## P0 — Exposición de claves — **CERRADO (2026-07-18)** · OPCIÓN A completada

- El remoto trackeaba `.cortex/master_key.hex` (256-bit) y `.cortex/solana_keypair.json` en `a289204`, repo público → **ambas claves comprometidas por definición**.
- **Rotación ejecutada (2026-07-18, C5-REAL):**
  - Wallet vieja verificada on-chain **vacía** (RPC mainnet: 0 SOL, 0 token accounts, 0 transacciones en su historia — pubkey vieja `CqrUNg4o…2yvb`) → nada que transferir; keypair viejo abandonado.
  - `master_key.hex` rotada (`openssl rand 32`, raw bytes, `chmod 600`). Verificado: 0 payloads `C5ENC:` en DBs locales → no requiere re-cifrado ni migración de hash-chain. Ningún código local lee el fichero (los consumidores usan env vars); verificado que ningún shell rc exporta `CORTEX_*`.
  - `solana_keypair.json` rotado (Ed25519 vía pynacl; nueva pubkey `HR36xxpL…thsU`, verificado round-trip desde disco). `chmod 600`.
  - Viejas claves en `~/.cortex_p0_backup/` (fuera del árbol del repo, 700/600).
- El remoto trackeaba `20_VAULT/` (PKM/CRM/OSINT con individuos nombrados) → aniquilado con el borrado del repo.
- El linaje local **jamás** trackeó claves ni vault (`git log --all -- <path>` vacío para los tres paths; re-verificado antes del push).
- **OPCIÓN A — COMPLETADA (2026-07-18, C5-REAL):**
  - Backups pre-aniquilación en `~/.cortex_p0_backup/`: `BABYLON-60-main-tip.tar.gz` (7,1 MB, tip `57282100`) y `BABYLON-60-corpus-a289204.tar.gz` (5,7 MB — verificado: 629 `.md`).
  - Remoto viejo **PRIVATIZADO** (404 anónimo) y luego **BORRADO** (`gh repo delete`, scope `delete_repo` concedido vía `gh auth refresh`). Todas las ramas `copilot/*` con las claves y `20_VAULT/` aniquiladas de un golpe. 0 forks.
  - Repo **recreado** y linaje canónico publicado: push por chunks (857 commits, 1,03 GiB, 7+1 pushes) → remoto `main` = local `main` = `462d9c25ee` (paridad verificada). Se eliminó la regla global `url.git@github.com:.insteadof` (no había clave SSH en la máquina; restaurar con `git config --global url.git@github.com:.insteadOf https://github.com/`).
  - Higiene pre-push: basura `tmp_obj_*` y `.keep` huérfano eliminados de `.git/objects`. Blobs mayores en historia: artefactos de build (`src-tauri/target`, `node_modules`) y `guarded_ledger.db` (74,5 MB, muestra strings: solo hashes/IDs — sin datos personales ni claves). Historia NO reescrita: los anchors OTS del Git Sentinel siguen válidos.
  - gitleaks sobre árbol HEAD: 2 hallazgos = **2 falsos positivos** (`crypto.py` parámetro tipado sin material; `demo_exergy_poc.py` señuelo plantado dentro de un mock diff de test).
  - Repo **PÚBLICO** de nuevo (HTTP 200) con **secret scanning + push protection ENABLED**. GitHub escanea la historia completa en background; `secret_audit.yml` corre como gate CI en cada push.

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

- [x] **P0**: rotación de master key + keypair Solana (ejecutada 2026-07-18 — ver §P0; wallet vieja vacía on-chain, sin C5ENC local → sin migraciones)
- [x] **P0**: estado terminal del remoto — OPCIÓN A ejecutada (2026-07-18): remoto viejo borrado, linaje canónico republicado en `main` = `462d9c25ee`, secret scanning + push protection activos
- [x] **Dedupe JSONs**: `fitted_weights.json` y `module_models.json` deduplicados en el path canónico `apex_trials/` (completado 2026-07-17).
- [x] **Re-verificar FIND-001/002**: verificado que no aplican a la línea local; los ficheros vulnerables del remoto (`swarm/state_store.py`, Stripe webhooks) no existen en este linaje.
- [x] **Triage de `.md`**: todos los md físicos están trackeados, ignorados en `.gitignore` (`.agents/`, `.pytest_cache/`, etc.) o pertenecen al submódulo Git `docs/aie-book`.
- [x] **SecureHook.sol (CENT-04)**: implementado lock de reentrada real con EIP-1153 transitorio (tstore/tload) y control de errores en `contracts/test/SecureHook.sol`.
- [x] **BABYLON60 IDE v1.1.0 operativo end-to-end** (2026-07-17): contrato frontend↔backend reparado y verificado con Playwright contra `master_ledger.db` real (consenso 2/2 VERIFIED, 0 errores JS en ambos modos cognitivos).
- [x] **BABYLON60 IDE v1.2.0 — delegación REAL + CortexLedger propio** (2026-07-17): la delegación dejó de ser Teatro Verde (`localStorage`). Ahora `commit` ejecuta git de verdad (probado: commit real `53122e2` sellado por el motor) y `push/merge/ship/deploy` hacen **crash causal HTTP 423** mientras P0 esté abierto. El IDE lleva su propio CortexLedger append-only hash-chain SHA-256 (`babylon60_ide.db`, sidecar) y lo autoverifica. Nuevo eje DETERMINAR: analítica agregada + búsqueda Okapi BM25 léxica sobre payloads. E2E Playwright: 0 pageerrors en 7 rutas × 2 modos, search→detail OK, boot inmune a localStorage corrupto.
- [x] **IDE sidecar**: añadir `babylon60_ide.db*` al `.gitignore` del repo real (completado y verificado en .gitignore).
- [x] **Si OPCIÓN B**: colapso documental del remoto (obsoleto; OPCIÓN A completada, remoto privatizado/borrado y recreado con historia limpia, verificado 2026-07-18).
- [x] **IDE**: motor de inferencia local (TRANSFORMERS vía MLX/llama.cpp / Ollama) — integrado E2E en frontend y backend FastAPI, con dashboard local-first y trazador dinámico de GraphLedger Mamba (completado 2026-07-18).

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
| 2026-07-18 | **BABYLON60 IDE v1.2.2 — a11y + hardening del enjambre**: (1) TOCTOU en `execute()` cerrado con claim atómico `cortex_ledger.claim()` (tabla `cortex_claims` PK + `BEGIN IMMEDIATE`) → ejecución at-most-once (probado: 3 executes concurrentes → 1×200, 2×409). (2) Auditoría WCAG determinista de la paleta calma → `--dust-faint` #6E6B83→#8C8AA4 (AA body ≥4.5) y `--dust-ghost` #3E3B4F→#66647E (large-text AA ≥3.0). (3) `prefers-reduced-motion`: detiene bucles (tachómetro/pulso/loading) — brief "sin parpadeos". (4) Hardening backend salvado del enjambre-100 (13/108 agentes completaron antes del límite de sesión; 20 propuestas, apliqué el cluster verificado): `contextlib.closing` en ledger/ontology/query (fuga de conexión en toda ruta de error), validación de tabla existente → 404 (antes 500 con texto crudo filtrado), errores DB saneados, `sqlite3.DatabaseError`/`Error`, GZip, manejador global de excepciones (500 JSON sin traceback), CORS acotado a GET/POST + Content-Type, glob determinista `sorted()` | E2E Playwright: 0 pageerrors en 7 rutas × 2 modos (con reduced-motion) · regresión backend OK (404 en tabla inexistente, SQL console conserva su error, gzip activo) · ruff limpio |
| 2026-07-18 | **Nota — enjambre-100 topó el límite de sesión** (resets 11:50am UTC): 13/108 agentes completaron, 95 error de cuota, 0 confirmados por el synth (murió en el límite). Salvé las 20 propuestas crudas del journal and apliqué las verificadas yo mismo (en-loop, determinista). Re-ejecutar el enjambre completo requiere esperar al reset de cuota. | `journal.jsonl` de `wf_30f33568-7db` |
| 2026-07-18 | **BABYLON60 IDE v1.2.3 — E2E Local Inference Dashboard**: (1) Integración y montaje del enrutador de inferencia local en FastAPI backend, soportando Ollama/MLX y Mamba SSM. (2) Registro de ruta de vista 'inference' y atajo físico de teclado '⌘8'. (3) Dashboard de generación local con telemetría de rendimiento (tps, latencia, integridad SHA256) y trazador visual de nodos GraphLedger de Mamba. (4) Compilación exitosa de Vite del frontend. | Confirmación de tests pytest (217/217) y exergy score 1000/1000 |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `bb57df8fd380`) | Git Sentinel `2361310c3f` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `c2ba17fb9ec9`) | Git Sentinel `305436b536` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `d8f4d7dac72a`) | Git Sentinel `e9e93613db` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `d63f1bc59677`) | Git Sentinel `12f0bffd21` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `3f3853c6aefa`) | Git Sentinel `feac00cf41` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `16bec2ca3a66`) | Git Sentinel `60952d2ede` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `cb947faf596b`) | Git Sentinel `6385bf099c` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `57abbd3c6ef7`) | Git Sentinel `65fdace0c1` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `f091c47d3366`) | Git Sentinel `86f98eb165` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `a03258f37501`) | Git Sentinel `71a03eb267` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `468d118ae2db`) | Git Sentinel `68d14f172f` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `72d02b6dbacc`) | Git Sentinel `c4af246bf1` |
| 2026-07-26 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `1353545b0edf`) | Git Sentinel `66e56c5ffa` |
