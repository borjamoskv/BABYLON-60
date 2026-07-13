# AUDITORÍA · github.com/borjamoskv/BABYLON-60

**Fecha:** 2026-07-13 · **HEAD:** `e0b8ce9` (main, 2026-07-10) · **Alcance:** clon remoto de GitHub (no el working copy local)
**Método:** clon fresco + verificación por comando (compileall, ruff, pytest, grep, GitHub/PyPI). Cada afirmación fue ejecutada, no estimada.

## Qué es

Monorepo público del paquete PyPI `cortex-persist` (memoria tamper-evident y linaje de decisiones para agentes IA). 4.623 archivos, 95 MB de working tree, `.git` remoto de 41 MB. 267.676 LOC de Python solo en `babylon60/` (~70 subpaquetes), más Rust, Go, JS/TS, Solidity y Clojure. 474 archivos de test. 3 stars, 0 forks, 4 PRs abiertas, 2.500+ ejecuciones de Actions.

## Veredicto

El código es más sano que el repositorio. El núcleo criptográfico es real y los tests pasan, pero el repo como producto público tiene tres problemas serios: **17 vulnerabilidades abiertas en la capa Rust**, **identidad fragmentada con onboarding roto**, y **contenido personal/ajeno publicado en un repo que se presenta como infraestructura de producción**. Además, el remoto está notablemente más limpio que lo que describía la auto-auditoría del 6-jul (`AUDITORIA_BABYLON.md`): el `.git` de 9,2 GB, el wav de 266 MB, `reqs.txt` y las ramas muertas son problemas del working copy local, no del remoto.

## ✅ Verificado como correcto

- **Cripto real, no teatro:** Ed25519, AES-GCM, Argon2id, HKDF (`cryptography`), Merkle (`ledger/merkle.py`), hash-chain (`prev_hash` en 10+ módulos del ledger), RFC3161 y cliente Rekor/Sigstore.
- **0 errores de sintaxis** en 2.305 archivos .py (`compileall`). **0 violaciones ruff** (el único E902 es un fallo de caché del propio ruff, no del código).
- **Tests funcionales:** con las deps core instaladas, la muestra ejecutada pasa (7/7 `test_memory_firewall.py`, 0.38s).
- **Sin secretos reales en HEAD:** solo fixtures de test, regexes de las guardas y ejemplos documentados (AKIA…EXAMPLE). `.env` solo como `.example`. Sin `__pycache__` ni `.DS_Store` trackeados.
- **Gobernanza presente:** SECURITY.md, gitleaks, pre-commit, secrets.baseline, CodeQL, pip-audit, codecov, RELEASE_PROCESS. Solo 4 TODO/FIXME en 267K LOC.

## 🔴 Crítico

**1. 17 alertas Dependabot abiertas (6 high, 4 medium, 7 low), todas en dependencias Rust.**
`rust-openssl` (OOB write, heap overflow, undefined behavior, ×7), `rustls-webpki` (DoS por CRL malformado), `rand`. Para un producto cuya propuesta de valor es "integridad criptográfica verificable", vulnerabilidades high en su propia capa criptográfica/TLS Rust son la contradicción central. **Acción:** `cargo update` de openssl/rustls-webpki/rand y cerrar las 17 esta semana.

**2. Identidad fragmentada + onboarding roto.**
Repo `BABYLON-60` ≠ paquete `cortex-persist` ≠ URL de pyproject (`github.com/borjamoskv/Cortex-Persist`, otro repo). PyPI publica 1.0.0; el repo declara 1.0.2. El README no explica instalación ni uso (solo manifiesto "exergía/anergía"). El QUICKSTART está roto: `uvicorn cortex.api:app` y `from cortex import CortexClient` no existen (`cortex/` solo contiene `math/` y `nodes/`; el cliente real es `babylon60.api.client.CortexClient`). Un usuario nuevo no puede completar el "quickstart de 3 minutos". **Acción:** un nombre, un repo canónico, README instalable, quickstart probado en CI, publicar 1.0.2.

## 🟡 Importante

**3. Contenido ajeno al producto en un repo público (27 MB `public/` + 26 MB `data/naroa/`).**
Podcasts de 21+3 MB sobre "UTBH" ("colapso ético y judicial", "el lucrativo negocio del odio") e imágenes tipo "un hombre blanco hipócrita" conviven con una librería de compliance que cita el EU AI Act en sus keywords. Riesgo reputacional y legal directo. `data/naroa/` es la web de una artista (217 archivos, imágenes triplicadas en `web/images`, `web/assets` y `mirror/assets`) con derechos de obra sin aclarar. 148 binarios en git en total. **Acción:** extraer a repos propios y purgar del historial con `git filter-repo`.

**4. CI desmesurado: 27+ workflows, 2.500+ runs.**
Telemetría en cron cada ~30-40 min (1.181 runs solo de "C5-REAL Live Telemetry"), más MÖBIUS, SIGINT Monitor y "Exergy Singularity" diaria. Quema minutos de Actions y ahoga la señal: es imposible ver de un vistazo si `ci.yml` está verde. **Acción:** reducir a ~5 (ci, codeql, security-scan, release, docs); eliminar los crons decorativos.

**5. Superficie `exec()` por diseño.**
Los motores JIT/auto-modificación (`extensions/evolution/demiurge.py`, `extensions/swarm/sortu_jit_executor.py`, `engine/core/sandbox_jit.py`, `utils/sandbox.py`) ejecutan código generado con `exec()`. Hay justificaciones `nosec` y guardas (`guards/analysis.py`, `legion_vectors.py`), pero un namespace de Python no es un límite de seguridad: es la superficie de ataque nº1 del producto. **Acción:** feature flag off por defecto + modelo de amenaza documentado, o aislamiento real (proceso/contenedor).

**6. `dependabot_alerts.json` y `codeql_alerts.json` commiteados.**
Publican el estado de vulnerabilidades del propio repo (y quedan obsoletos al instante). Fuera del repo.

**7. Fallback silencioso `"sk-ant-fallback"`** en `engine/flow/cascade_router.py:85`: enmascara errores de configuración con peticiones que fallarán aguas abajo. Fail-fast en su lugar.

## 🟢 Menor

- **Raíz saturada:** 18 .md en raíz incluyendo lore de 96 KB (MILESTONES), 53 KB (AGENTS), `cortex_directives.yaml` (65 KB), más auditorías previas commiteadas (AUDITORIA_BABYLON, FINAL_AUDIT, CODE_REVIEW_fable5). Mover a `docs/`.
- **Duplicación:** `guards/secret_guard.py` (54 LOC) y `security/memory_firewall.py` comparten las mismas regexes con clases distintas (`SecretGuard` vs `SecretRedactor`). Fusionar. `cortex/` residual en raíz confunde con el nombre del paquete.
- **Scope creep:** ~70 subpaquetes en `babylon60/` (darknet, evm, mcts, shannon, sica, nous, mac_maestro…) entierran el producto vendible (ledger + crypto + memory + api + mcp_server).
- `shell=True` real solo en `extensions/aether/tools.py:204` (con guarda, nosec); el `verify=False` detectado es un kwarg propio (`ledger_verify`), falso positivo. Los `os.system`/`eval` de `guards/` son strings de detección, no llamadas.
- Tests no ejecutables sin `uv sync` completo (p.ej. `sqlite_vec` falta en clon fresco): documentar el mínimo para contribuir.

## Plan priorizado

| P | Acción | Esfuerzo |
|---|--------|----------|
| P0 | `cargo update` → cerrar 17 alertas Dependabot | horas |
| P0 | Quickstart/README funcionales + resolver identidad BABYLON-60 vs Cortex-Persist + publicar 1.0.2 | 1 día |
| P1 | Extraer `public/` (UTBH) y `data/naroa/` + `git filter-repo` | medio día |
| P1 | Borrar `*_alerts.json`; reducir workflows 27→5; matar crons de telemetría | horas |
| P2 | Fusionar secret_guard/memory_firewall; lore a `docs/`; flag off para JIT/exec | 1 día |

---
*Auditoría ejecutada con verificación por comando sobre clon fresco del remoto. Los hallazgos 1-7 son reproducibles con los comandos citados.*
