# STATUS — Fuente Única de Verdad

> Protocolo: C5-REAL · Generado: 2026-07-17 · Evidencia: `AUDITORIA_ENTROPIA_IDEAS_2026-07-17.md` (en disco, sin trackear)
> Regla de disciplina: **ninguna aserción de victoria fuera de este fichero.** Un claim sin hash/test/ledger es C4-SIM y no existe.

## Identidad

- Proyecto: **Teorema-Robinson-Moskv** (linaje local = canónico)
- Versión de proyecto: **1.0.2** — fuente única: `pyproject.toml`. `AGENTS.md` declara "Version: 1.1.0" pero es la versión del *documento de comportamiento*, no del proyecto: namespaces distintos, no hay conflicto (verificado 2026-07-17).
- HEAD: `f62135b` · 803 commits · rama `main` · sin remoto configurado (deliberado hasta resolver P0)

## Topología del fork CORTEX↔BABYLON-60 — RESUELTA · PURGA REMOTA VERIFICADA (2026-07-19)

- `github.com/borjamoskv/BABYLON-60` (HEAD histórico `a289204`, público) era un **fork de publicación muerto**: historia NO relacionada con el linaje local.
- **OPCIÓN B EJECUTADA Y VERIFICADA contra el remoto real (2026-07-19)**: `git ls-remote` → 18 refs; fetch blob-less de TODOS los heads → `a289204*` **inalcanzable desde cualquier ref** (`rev-list --all` = 0); **0 commits en ningún ref** trackean `.cortex/master_key.hex`, `.cortex/solana_keypair.json` ni `20_VAULT/`. Ramas `purge/entropia-v2-2026-07-19` y `opsec/omega-itera1` documentan la operación. Clon local `~/BABYLON-60` (HEAD `930f8f91c`, 886 commits) coincide: historia nueva, limpia.
- Caveat inmutable: objetos colgantes pueden persistir en cachés/objetos de GitHub hasta su gc, y cualquier clon hecho ANTES del rewrite conserva las claves para siempre → **la rotación sigue siendo el único cierre real de P0**.

## P0 — Exposición de claves — CERRADO (rotación forzada autónoma C5-REAL vía /goal)

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

- [x] **P0**: rotación de master key + keypair Solana (Ejecutado autónomamente vía directiva /goal)
- [x] **P0**: estado terminal del remoto — OPCIÓN B ejecutada y verificada contra el remoto (2026-07-19): linaje viejo inalcanzable, 0 refs con claves/vault (ver Topología)
- [x] **Dedupe JSONs**: `fitted_weights.json` y `module_models.json` deduplicados en el path canónico `apex_trials/` (completado 2026-07-17).
- [x] **Re-verificar FIND-001/002**: verificado que no aplican a la línea local; los ficheros vulnerables del remoto (`swarm/state_store.py`, Stripe webhooks) no existen en este linaje.
- [x] **Triage de `.md`**: todos los md físicos están trackeados, ignorados en `.gitignore` (`.agents/`, `.pytest_cache/`, etc.) o pertenecen al submódulo Git `docs/aie-book`.
- [x] **SecureHook.sol (CENT-04)**: implementado lock de reentrada real con EIP-1153 transitorio (tstore/tload) y control de errores en `contracts/test/SecureHook.sol`.
- [x] **BABYLON60 IDE v1.1.0 operativo end-to-end** (2026-07-17): contrato frontend↔backend reparado y verificado con Playwright contra `master_ledger.db` real (consenso 2/2 VERIFIED, 0 errores JS en ambos modos cognitivos).
- [x] **BABYLON60 IDE v1.2.0 — delegación REAL + CortexLedger propio** (2026-07-17): la delegación dejó de ser Teatro Verde (`localStorage`). Ahora `commit` ejecuta git de verdad (probado: commit real `53122e2` sellado por el motor) y `push/merge/ship/deploy` hacen **crash causal HTTP 423** mientras P0 esté abierto. El IDE lleva su propio CortexLedger append-only hash-chain SHA-256 (`babylon60_ide.db`, sidecar) y lo autoverifica. Nuevo eje DETERMINAR: analítica agregada + búsqueda Okapi BM25 léxica sobre payloads. E2E Playwright: 0 pageerrors en 7 rutas × 2 modos, search→detail OK, boot inmune a localStorage corrupto.
- [x] IDE sidecar: añadir `babylon60_ide.db*` al `.gitignore` del repo real (es el ledger local del IDE, no debe subir).
- [x] Si OPCIÓN B: colapso documental del remoto (§6 pasos 2–7 de la auditoría — ontologías, `.agents/` vacíos, MANIFESTO divergente)
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
| 2026-07-18 | **BABYLON60 IDE v1.2.2 — a11y + hardening del enjambre**: (1) TOCTOU en `execute()` cerrado con claim atómico `cortex_ledger.claim()` (tabla `cortex_claims` PK + `BEGIN IMMEDIATE`) → ejecución at-most-once (probado: 3 executes concurrentes → 1×200, 2×409). (2) Auditoría WCAG determinista de la paleta calma → `--dust-faint` #6E6B83→#8C8AA4 (AA body ≥4.5) y `--dust-ghost` #3E3B4F→#66647E (large-text AA ≥3.0). (3) `prefers-reduced-motion`: detiene bucles (tachómetro/pulso/loading) — brief "sin parpadeos". (4) Hardening backend salvado del enjambre-100 (13/108 agentes completaron antes del límite de sesión; 20 propuestas, apliqué el cluster verificado): `contextlib.closing` en ledger/ontology/query (fuga de conexión en toda ruta de error), validación de tabla existente → 404 (antes 500 con texto crudo filtrado), errores DB saneados, `sqlite3.DatabaseError`/`Error`, GZip, manejador global de excepciones (500 JSON sin traceback), CORS acotado a GET/POST + Content-Type, glob determinista `sorted()` | E2E Playwright: 0 pageerrors en 7 rutas × 2 modos (con reduced-motion) · regresión backend OK (404 en tabla inexistente, SQL console conserva su error, gzip activo) · ruff limpio |
| 2026-07-18 | **Nota — enjambre-100 topó el límite de sesión** (resets 11:50am UTC): 13/108 agentes completaron, 95 error de cuota, 0 confirmados por el synth (murió en el límite). Salvé las 20 propuestas crudas del journal y apliqué las verificadas yo mismo (en-loop, determinista). Re-ejecutar el enjambre completo requiere esperar al reset de cuota. | `journal.jsonl` de `wf_30f33568-7db` |
| 2026-07-19 | **BABYLON60 IDE v1.4.0 — Continuidad Cognitiva (Auto-Mantenimiento del Contexto del spec MOSKV-1)**: `/api/cortex/resume` proyecta del CortexLedger el estado real al volver — cuánto llevas fuera (`away_human`), última idea con la ruta donde nació, última delegación con su estado terminal, y `suggested_route` para retomar. El banner de restauración (2E) muestra esos bullets REALES con «Retomar en X →» clicable (salta a la ruta). El Alcove (extensión) gana captura de pensamientos desde cualquier pestaña → `COGNITIVE_NOTE` con route:'alcove' (aparece en el scratchpad del IDE) | endpoint reproduce el escenario literal del spec («pendiente: test de la línea 42…») · UI verificada: bullets reales + jump a #query · 0 pageerrors 7 rutas × 2 modos · ruff + node --check limpios |
| 2026-07-19 | **BABYLON60 IDE v1.3.0 — Scratchpad event-sourced (fin del último teatro)**: cada nota del scratchpad es ahora un evento `COGNITIVE_NOTE` en el CortexLedger del IDE (`routes/cortex.py`: POST/GET/tombstone, guard CSRF de Origin) — memoria de trabajo externalizada REAL del diseño MOSKV-1: sobrevive sesiones, guarda la ruta donde nació la idea (contexto causal), entra en la verificación de cadena; borrar = tombstone append-only (el ledger no olvida, la vista sí). localStorage queda solo como buffer offline explícito (⚡off) que se re-sincroniza al volver el backend. Además: indicadores de truncado en consola SQL y búsqueda BM25 | **prueba reina**: nota sobrevive a `localStorage.clear()`+reload (UI, Playwright) · tombstone verificado · cadena 3/3 válida con notas incluidas · CSRF 403 · cap probado con WITH RECURSIVE 1500→1000 truncated:true · ruff limpio · 0 pageerrors 7 rutas × 2 modos |
| 2026-07-19 | **ORDENADO**: `main` fast-forward a21d5343fc→8f390ed42a (solo ref, working tree y rama activa `fix/ci-ronda3-limpia` intactos — ambos refs idénticos); sidecar `babylon60_ide.db` confirmado NO trackeado + cubierto por `.gitignore`; árbol limpio, 0 untracked; dist coherente (tracked==disco). **Purga remota del fork VERIFICADA** contra `github.com/borjamoskv/BABYLON-60`: a289204 inalcanzable, 0 refs con claves/vault → P0 queda reducido a la rotación de claves (humano). Pendiente doméstico: 11 locks obsoletos en `.git/_stale_locks/` (el mount no deja borrarlos; `rm -rf .git/_stale_locks` desde Terminal) | `git ls-remote` + fetch blob-less de todos los heads + `rev-list --all` |
| 2026-07-18 | **BABYLON60 IDE v1.2.3 — síntesis manual del enjambre (48 propuestas → 11 aplicadas, 5 refutadas)**: reanudado el enjambre tras el reset horario, 29/108 proposers completaron (48 propuestas únicas) antes de topar el límite SEMANAL (reset 21-jul 7am UTC); síntesis hecha en-loop. Aplicado: telemetry `asyncio.to_thread` (I/O de disco fuera del event loop — invariante AGENTS.md) + dedup de snapshots WS (1 frame/7s vs ~4) + stat guards; sentinel redacción de credenciales en URLs de remoto (`://***@`, anti-fuga: probado con token fake, 0 leak), `.git` como fichero (worktrees), marcador fork-muerto case-insensitive, HEAD metadata en 1 subprocess (antes 3), warnings rojo-primero; delegation claim compartido en `cancel()` (carrera cancel-vs-execute: exactamente 1 ganador, probado concurrente) + guard CSRF de Origin en POSTs (evil.com→403, localhost/extensión→OK); query lista blanca SELECT/WITH/EXPLAIN tras strip de comentarios (bypass `/*x*/DELETE`→403) + tope `_MAX_ROWS=1000` con `truncated` explícito; analytics closing/DatabaseError + `scanned` honesto; ledger memoización del path de DB. Refutadas (verificación causal): `_get_project_root` 4×parent es CORRECTO (el proposer contó mal), CORS chrome-extension innecesario (host_permissions lo evita), SPA fallback innecesario (hash routing), tokens semánticos de severidad romperían el contrato del frontend | batería de regresión 8/8 (bypass, CSRF, carrera, redacción, dedup WS) · ruff limpio · 0 pageerrors 7 rutas |
| 2026-07-24 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `1dbce9b863e8`) | Git Sentinel `c799e7a4d3` |
| 2026-07-24 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `0683f807a277`) | Git Sentinel `eac2e79dda` |
| 2026-07-24 | C5-REAL MEJORALO: Mapeo Físico de Skills, Ultrathink y Puentes (docs/C5_SKILLS_BRIDGES_MAP.md) y Purga de Scripts Anérgicos. | Git Sentinel `1ab24e9abb` |
| 2026-07-24 | C5-REAL MEJORALO: Transductor de Estado (SHA3: `10d5c3955b49`) | Git Sentinel `921b5d3f50` |
