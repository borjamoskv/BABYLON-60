# AUDITORÍA C5-REAL — APEX / Reconciliación Local ↔ Público

```yaml
Operator:        borjamoskv
Reality_Level:   C5-REAL (medición directa sobre disco + objeto git)
Local_HEAD:      7dca183d76772d95f7d6a41a1247ff45720e2e36  (rama main)
Local_remote:    git@github.com:borjamoskv/Teorema-Robinson-Moskv.git   → PRIVADO (404 a no-autenticado)
Public_repo:     github.com/borjamoskv/BABYLON-60                        → PÚBLICO (3.815 commits, Py 74.6%)
Método:          cada hallazgo lleva su comando reproducible. Cero teatro verde.
Limitación:      suite pytest/ruff NO ejecutable in-session (venv rota + sin red + lock no borrable) → estado tests = C4-NO-VERIFICADO
```

---

## 0. COLAPSO EJECUTIVO

| Eje | Estado | Dato duro (verificado) |
|---|---|---|
| **Divergencia local↔público** | 🔴 CRÍTICO estructural | El árbol local (263 ficheros) NO es el repo público. Los 4 ficheros que CodeQL marca en BABYLON-60 están **ausentes** del local. Auditas un espejo privado limpio mientras el riesgo vive en el público. |
| Secreto `CORTEX_VAULT_KEY` | 🔴 CRÍTICO | Clave Fernet en claro, **tracked** y **pusheada a origin/main** (`AUDITORIA_ATOMICA_2026-07-16.md:48`, commit `deeaa868b`). La "remediación" previa sacó `.env.vault` pero **filtró la clave al propio informe**. |
| HMAC estático BFT (fix falso) | 🔴 CRÍTICO | `claude_bft_interceptor.rs:106`: la clave `CORTEX_BFT_KEY_2026_MASTER_LEDGER_FALLBACK` **sigue hardcodeada** como `unwrap_or_else`. El "fix" de CENTURIA fue cosmético. C4-SIM presentado como C5-REAL. |
| CodeQL público (BABYLON-60) | 🔴 CRÍTICO | **14 alertas High abiertas** + 3.158 cerradas · 1 vuln Dependabot · alertas Malware Dependabot · Secret Scanning activo. |
| Procedencia criptográfica falsa | 🟡 ALTO | `shadow_router.py`: `sha256(secrets.token_bytes(32))` disfrazado de `provider_receipt_hash`/`policy_hash`. Hash de ruido, no compromiso real. |
| Masa del historial | 🟡 ALTO | `.git` = **448 MB**. Árbol de trabajo limpio (263 ficheros) pero historia **nunca reescrita**: node_modules, target/, dylibs, stems de audio, legacy cortex siguen dentro. |
| `index.lock` + dirty | 🟡 ALTO | `.git/index.lock` presente (bloquea `git commit`) + **18 scripts modificados sin commitear** (430 ins / 317 del). El puente no puede borrar el lock. |
| `except Exception` (viola AGENTS.md) | 🟡 ALTO | **10+ ocurrencias** en código propio, prohibidas por INV de AGENTS.md. La auditoría previa afirmó "sin bare except" — falso en HEAD actual. |
| Prueba Lean | 🟢 HONESTA / superficial | 6 teoremas reales, **0 `sorry` reales** (el "sorry" es una palabra en el comentario, no un tactic). Prueba el orden parcial de ℕ; el vínculo con `lamport_t` sigue siendo un **comentario**, no un puente mecánico. |
| Ruff / tests | ⚪ C4 no-verificado | No ejecutable en esta sesión. Último estado medido (auditoría previa): 555/563, 8 fallos por acoplamiento de entorno. |

> **Verificación que solo puedes hacer tú (fuera del sandbox):** en BABYLON-60 → pestaña **Secret scanning**. Es la respuesta autoritativa a "¿la clave Fernet está también en el repo público?". El code-search público me lo bloqueó `robots.txt`; el `main` público **no** sirve `.env.vault` ni ese informe (ambos 404), pero eso no limpia su historial.

---

## 1. LA DIVERGENCIA (raíz de todo)

Estás auditando dos cosas distintas y tratándolas como una:

| | Local `Teorema-Robinson-Moskv` | Público `BABYLON-60` |
|---|---|---|
| Visibilidad | Privado (404) | **Público** |
| Ficheros tracked | 263 | superset (40+ dirs, `babylon60/engine/`, `api/`, `benchmarks/`, `scripts/deploy_*`) |
| `.py` en `babylon60/` | 19 | incluye `engine/mejoralo/*`, `engine/macrofago_ontologico.py`, `api/analysis.py` (**ninguno existe en local**) |
| CodeQL | workflow presente, sin datos in-session | 14 High abiertas |

**Consecuencia causal:** los `AUDITORIA_*.md` del repo describen la limpieza de un espejo privado de 263 ficheros. El colapso de masa (69.832 → 263) es real y bueno **para ese espejo**, pero la superficie de ataque real —la pública— no la tocan. Repro:

```bash
# local: los ficheros marcados por CodeQL no están
for f in babylon60/api/analysis.py babylon60/engine/macrofago_ontologico.py \
         scripts/deploy_to_substack.py benchmarks/bench_arena_hard.py; do
  git ls-files --error-unmatch "$f" 2>/dev/null || echo "AUSENTE: $f"
done
# → los 4 AUSENTE
```

---

## 2. CRÍTICO

### C1 · Clave Fernet `CORTEX_VAULT_KEY` en claro, tracked y pusheada
`AUDITORIA_ATOMICA_2026-07-16.md:48` contiene `CORTEX_VAULT_KEY="0hg-Pwsy…REDACTED"` (valor completo NO reproducido aquí a propósito — para no repetir el error). El commit `deeaa868b` que la introduce **ya está en `origin/main`**:

```bash
git grep "0hg-Pwsy" origin/main -- AUDITORIA_ATOMICA_2026-07-16.md   # → match en la rama remota
git merge-base --is-ancestor deeaa868b origin/main && echo "PUSHEADO"  # → PUSHEADO
```

El repo remoto es privado (mitiga exposición pública *directa*), pero la clave vive en los servidores de GitHub, en el historial, y en un fichero tracked. Norma de higiene: **una clave commiteada es una clave quemada.** La "remediación" anterior removió `.env.vault` y a la vez **imprimió la clave dentro del informe** — un autogol.

**Acción (orden estricto):** 1) rotar la clave Fernet **ya** (no sirve reescribir sin rotar si alguien clonó). 2) reemplazar el valor por `…REDACTED` en el informe. 3) `git filter-repo` para purgar el valor del historial. 4) cargar solo por entorno — el código ya lo hace bien: `ledger_actor.py:158 os.environ.get("CORTEX_VAULT_KEY")`.

### C2 · Fix falso del HMAC del Master Ledger (C4-SIM vendido como C5-REAL)
`AUDITORIA_CENTURIA.md` afirma haber erradicado el HMAC estático → "carga dinámica vía `std::env::var`". La realidad en `strike_rs/src/bin/claude_bft_interceptor.rs:106`:

```rust
let env_key = std::env::var("CORTEX_BFT_KEY")
    .unwrap_or_else(|_| "CORTEX_BFT_KEY_2026_MASTER_LEDGER_FALLBACK".to_string());
```

La constante **sigue presente** como fallback. Si `CORTEX_BFT_KEY` no está en el entorno (CI, clon limpio, olvido), el interceptor usa una clave conocida y pública-en-historial → **falsificación universal de atestaciones del Master Ledger**, exactamente la brecha que se declaró cerrada. El commit movió el string de una asignación a un `unwrap_or_else`; el vector no cambió.

**Acción:** eliminar el fallback. `std::env::var("CORTEX_BFT_KEY").expect("CORTEX_BFT_KEY requerido")` — fallar ruidoso, no degradar a clave conocida.

### C3 · 14 alertas High abiertas en el repo PÚBLICO (CodeQL)
De tu captura de la pestaña Security de BABYLON-60 (público):

| # | Regla | Fichero:línea |
|---|---|---|
| #3266/65/64/63 | Uncontrolled data in path expression (path traversal) | `babylon60/…/mejoralo/engine.py:56–59` |
| #393/92/91/90/89 | Uncontrolled data in path expression | `babylon60/…/mejoralo/ship.py:84–122` |
| #3267 / #3268 | Uncontrolled data in path expression | `babylon60/engine/macrofago_ontologico.py:55,158` |
| #388 | Uncontrolled data in path expression | `babylon60/api/analysis.py:81` |
| #3262 | Incomplete URL substring sanitization | `scripts/deploy_to_substack.py:119` |
| #394 | Clear-text logging of sensitive information | `benchmarks/bench_arena_hard.py:200` |

12 de 14 son **path injection**: dato controlable fluye a una ruta de fichero → lectura/escritura fuera del directorio previsto. Es la misma familia que el RCE de `/api/terminal` de la auditoría anterior: input no confiable tocando el sistema. `api/analysis.py:81` sigue siendo foco. Además: 1 vuln Dependabot + alertas de **Malware** en dependencias + el banner "CodeQL is reporting warnings" (el propio escaneo falla parcialmente).

**Acción:** estos viven en el público y no los puedo tocar desde aquí (árbol ausente en local). Prioriza los 12 path-traversal (canonicaliza y valida contra un root permitido: `os.path.realpath` + prefijo), el `in`-substring de URL (comparar host parseado, no `substring`), y purga el logging en claro. Resuelve la vuln Dependabot y las alertas Malware.

---

## 3. ALTO

### A1 · Procedencia criptográfica fabricada — `shadow_router.py`
Líneas 46/56/57: el "hash de recibo del proveedor", "policy_hash" y "candidate_set_hash" son `hashlib.sha256(secrets.token_bytes(32)).hexdigest()` — **hash de bytes aleatorios**, no compromiso de ningún contenido real. El "fix" de CENTURIA cambió `token_hex` → `sha256(token_bytes)`: cosmética. Sigue siendo ruido con etiqueta `sha256:` fingiendo procedencia. Repro: `git grep -n "token_bytes(32)" babylon60/core/shadow_router.py`.
**Acción:** o commitear el hash **del payload real**, o renombrar a `nonce`/`request_id` y dejar de afirmar que es un compromiso criptográfico.

### A2 · `.git` = 448 MB — historia nunca reescrita
El árbol se limpió (263 ficheros) pero los blobs son eternos en la historia:

```
40 MB  cortex/agents/ontology/autodidact_mega_batch.yaml (+21 MB otra versión)
30 MB  experimental/cortex_legacy/.../node_modules/.../swift_addon.node
23 MB  experimental/cortex_legacy/consensus/target/.../libtokio-*.rlib  (×2)
17 MB  .../sharp-libvips-darwin-arm64/.../libvips-cpp.dylib
14 MB  .../micromamba
10 MB  Music/VISUALES/stems/htdemucs/Kuraia  (×5)
```
Repro: `git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' | awk '$1=="blob"{print $2,$3}' | sort -rn | head`.
**Acción:** una sola pasada `git filter-repo` purgando `*/node_modules/*`, `*/target/*`, `*.dylib`, `*.so`, `*/stems/*`, `experimental/cortex_legacy/*`, `*.env.vault`, y el valor de C1. Force push + reclonar. `.git`: 448 MB → decenas de MB. Combínalo con C1 en la misma pasada.

### A3 · `index.lock` bloqueante + 18 scripts en estado indefinido
`.git/index.lock` (0 bytes, 16-jul 23:29) presente → **cualquier `git commit` falla**. El puente Cowork **no puede** borrarlo (`unlink: Operation not permitted`). Mientras tanto, 18 ficheros `scripts/*.py` modificados (430 ins / 317 del, refactors "ULTRATHINK P0") **sin commitear**. Estado indefinido = deriva, contra tu propio ETHOS.
**Acción (manual, en tu terminal):** `rm -f .git/index.lock` → `git add -A scripts/ && git commit`. Requiere tu mano: el sandbox no puede.

### A4 · `except Exception` — viola tu propio AGENTS.md
AGENTS.md declara `except Exception:` **prohibido**. Realidad: 10+ en código propio (`bft/consensus_ledger.py:67,76`, `core/thermo_ast_pruner.py:91`, `scripts/objectives_manager.py`, `opsec_sentinel_c5.py`, `ouroboros_infinity.py`, `quadrilingual_enforcer.py`). La auditoría previa afirmó "sin bare except en código propio" — **falso** en HEAD actual. Repro: `git grep -nE "except Exception:|except:" -- 'babylon60/*.py' 'scripts/*.py'`.
**Acción:** capturar excepciones concretas o dejar propagar a Git Sentinel, como manda la norma.

### A5 · Suite no verificada esta sesión (C4)
Ni `pytest` ni `ruff` disponibles en el Python del sistema; `uv` intenta reconstruir la venv y **no puede borrar `.venv/.lock`** (misma limitación del puente); sin red para instalar. Último estado **medido** (auditoría previa): 8 fallos / 555 pasan, todos por acoplamiento al entorno (`~/30_BABYLON-60/telemetry.db`, `scratch/swap_buffer.bin`, `pytest-asyncio` no declarado). No lo re-verifico → lo marco **C4-NO-VERIFICADO**, no verde.

---

## 4. MEDIO / BAJO

- **M1 · `tx.origin`:** en contratos propios (`contracts/*.sol`, `anvil_yung/src/ApoptosisAnchor.sol`) **limpio** — este sí fue un fix real. Las coincidencias `tx.origin` restantes son de `anvil_yung/lib/forge-std/` (lib vendida). 🟢
- **M2 · `forge-std` vendido tracked:** ~48 `.sol` de la librería Foundry commiteados. Ruido; debería ser submódulo/dependencia, no fuente.
- **M3 · Lean superficial (no falso):** `Babylon.lean` demuestra reflexividad/transitividad/antisimetría de `≤` sobre ℕ con términos reales del core (0 `sorry`, 0 `axiom`). Honesto. Pero el "isomorfismo con `lamport_t`" es un **comentario**, no un vínculo mecánico con `BFTLedgerActor`. El README dice "validación formal": soporta C5 para el *modelo*, no para el *sistema*. El commit `2a8bd8ad` ("aserciones tipadas mapeadas a Babylon.lean") es un puente de nombres, no de pruebas.
- **M4 · 4 ficheros con `/Users/borjafernandezangulo`:** AGENTS.md, el informe de C1, 2 yaml de `cortex/audits/`. Bajó de 20 → 4. Residual.
- **M5 · Submódulo ajeno `docs/aie-book`** (`chiphuyen/aie-book`): clon sin `--recursive` lo recibe vacío. Evaluar si aporta o si es referencia externa.

---

## 5. LO QUE ESTÁ BIEN (exergía ganada, C5-REAL)

- Colapso de masa del árbol: 69.832 → **263** ficheros tracked. 0 `.db`, 0 `.env`, 0 artefactos build tracked. Repro: `git ls-files | wc -l`.
- RCE `/api/terminal` y `cortex/legal_dossier/` (dato de salud RGPD): **ausentes** del árbol tracked local.
- Ningún server FastAPI que exponga shell en el tracked local.
- `tx.origin` erradicado de contratos propios (fix genuino).
- Prueba Lean honesta (sin `sorry`/`axiom` reales) — aunque superficial.
- Sin `eval`/`exec`, sin `md5` en código propio.
- El código lee la clave del entorno correctamente (`os.environ.get`).

---

## 6. VEREDICTO

El espejo privado local es defendible: masa colapsada, sin secretos-en-fichero salvo el autogol de C1, RCE fuera. Pero **la auditoría estaba mirando el sitio equivocado**: el riesgo real es el **BABYLON-60 público con 14 High abiertas**, cuyo código ni siquiera está en el árbol que se venía saneando. Y tres "fixes" declarados C5-REAL son en realidad C4-SIM: el HMAC con fallback estático (C2), los hashes-de-ruido de `shadow_router` (A1), y —de tono— el claim de "validación formal" sobre una prueba que solo modela ℕ (M3). Tu ETHOS prohíbe presentar C4-SIM como C5-REAL: estos tres lo hacen.

Exergía recuperable, en orden de impacto:

1. **HOY** — Rotar `CORTEX_VAULT_KEY`. Redactar su valor en el informe. (C1)
2. **HOY** — Eliminar el fallback HMAC en `claude_bft_interceptor.rs`. (C2)
3. **HOY** — Revisar **Secret scanning** de BABYLON-60 y triar las 14 CodeQL High (empezar por los 12 path-traversal). (C3)
4. `rm .git/index.lock` (manual) → commitear los 18 scripts. (A3)
5. Una pasada `git filter-repo`: purgar masa histórica + valor de C1 + `.env.vault`. Force push + reclonar. (A2+C1)
6. Arreglar `shadow_router` (commit del payload real o renombrar a nonce). (A1)
7. Sustituir `except Exception` por captura concreta. (A4)
8. Declarar deps de test / fixtures `tmp_path` → suite verde en frío. (A5)
9. Rebajar el claim del README a "modelo formal del orden causal" o cerrar el gap Lean↔Python. (M3)

---

```yaml
metacognition:
  confianza_C5: [divergencia_local_publico, clave_pusheada, hmac_fallback, shadow_hashes, git_448MB, index_lock, bare_except, lean_sin_sorry]
  confianza_C4: [suite_tests_no_ejecutada, historial_BABYLON60_no_inspeccionable]
  pendiente_operador: [secret_scanning_BABYLON60, visibilidad_confirmada_en_UI]
  correccion_propia: "descarté 'sorry introducido en Lean' — era la palabra en el comentario, no un tactic; verificado leyendo el fichero completo."
```
*Generado por auditoría C5-REAL. Cada afirmación con comando reproducible sobre HEAD `7dca183d`. El valor de la clave se omite deliberadamente para no reincidir en C1.*
