# REMEDIACIÓN ITERA-2 — Teorema-Robinson-Moskv
`REALITY_LEVEL: C5-REAL` · Fecha: 2026-07-17 · Operador: MOSKV-1 APEX (sesión Cowork) · Génesis: `AUDITORIA_CENTURIA.md` P1 + `ETHOS.md` §3 · Predecesor: `REMEDIACION_P0_2026-07-17.md` (commit `574e3a944`)

█▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█

## 0. VECTORES DE ESTA ITERACIÓN

`[Vector]` capa de conexión + consenso + queue auxiliar + arco de atestación · `[Blast Radius]` BFT_Ledger API (aditiva), MasterLedgerQueue, recibos CLI · `[Target Invariant]` INV_BFT_02, INV_C5_03, INV_C5_04, INV_C5_07; suites previas intactas

| Vector | Ley | Mutación |
| :--- | :--- | :--- |
| CENT-03 doctrina inejecutable | INV_BFT_02 | **`babylon60/database/core.py` materializado**: `connect()` (async) y `connect_sync()` — WAL + `busy_timeout=5000` + `foreign_keys=ON` + durabilidad explícita validada (`FULL`/`NORMAL`, resto rechazado). El módulo fantasma sobre el que mandaba AGENTS.md ahora es físico. |
| CENT-06 conexión directa | INV_BFT_02 | `consensus_ledger.py` enruta por `database.core.connect_sync(FULL)`; fuera `check_same_thread=False` (invitaba escritura multi-hilo contra escritor-único). |
| **Verificador mock** (no auditado antes: hallado en lectura) | INV_C5_04 | `BFT_Ledger._verify_signature` devolvía `True` incondicional — **el contador de votos BFT era teatro**: 4 firmas basura alcanzaban quórum (RED-1 reproducido: `True`). Ahora: Ed25519 real contra registro `node_keys` (node_id→pubkey hex); nodo no registrado = voto nulo; sin registro = fail-closed. Nueva función `crypto.verify_ed25519()` (aditiva; `Ed25519Signer.verify` delega en ella). |
| CENT-14 replace no-op | — | `.replace("sha256:","")` sobre hash SHA3 purgado. |
| SIGKILL en audit | INV_C5_07 | `audit_integrity` mataba el proceso (o crasheaba sin capturar, RED-2: `CBOREncodeError` exit 1) ante payload indecodificable. Ahora: indecodificable/no-canonicalizable **ES veredicto de corrupción** — se cuenta, se reporta, el proceso vive. Réplica del escenario de `scripts/conformance_test.py` verificada: íntegro→True, corrupto→False, vivo. |
| NEW-E escritor rival + SIGKILL en callback | INV_C5_07 | `MasterLedgerQueue`: durabilidad `NORMAL`→`FULL` vía `database.core`; SIGKILL del done-callback (RED-3: exit 137) → **Zombie Writer Prevention** (el crash se registra y aflora en el siguiente `submit_transaction` con `raise from`); atomicidad de lote explícita (`BEGIN IMMEDIATE`/`COMMIT`); proscripción documentada: jamás apuntar al master ledger (BFTLedgerActor es el único escritor). Topología definitiva (fusión vs. eliminación) sigue siendo decisión de operador. |
| CENT-10 babel de hashes | INV_C5_03 | MD5 ya estaba muerto en árbol (verificado). Arco attest convergido: `attest_character_count` emite `sha3-256:`; `llm-attest` despacha por primitivo declarado — `sha3-256:` canónico, `sha256:` aceptado SOLO como legacy y **marcado** en el reporte (`hash_primitive: sha256-legacy`), hex desnudo 64 = SHA3-256 bare (compatibilidad shadow_router), prefijo desconocido = fail-closed. Cero downgrade silencioso. |

## 1. FALSACIÓN (RED → GREEN)

**RED (código previo, reproducido en vivo):**
- RED-1: `invoke_subagent` con 4 firmas `"FIRMA_BASURA_NO_ED25519"` y f=1 → `True` (quórum forjado).
- RED-2: `audit_integrity` con payload basura → crash `CBOREncodeError` sin capturar (exit 1); patrón alternativo → `os.kill(SIGKILL)`. Crash en vez de veredicto.
- RED-3: crash del writer del queue → done-callback ejecuta SIGKILL → proceso asesinado (exit 137).

**GREEN: 29/29.** 10 nuevos (`test_itera2_invariants.py`: pragmas async/sync, durabilidad ilegal rechazada, quórum con firmas reales, voto forjado→`PermissionError`, fail-closed sin registro, indecodificable=corrupción con proceso vivo, Zombie Writer Prevention, durabilidad FULL, roundtrip sha3 del par attest, legacy sha256 marcado) + 19 previos (vault_verify, resilience, crypto, master_ledger_queue, shadow_router_c5) — cero regresión. `ruff --select E4,E7,E9,F` limpio.

## 2. RESIDUO

1. `scripts/conformance_test.py:75` construye `StateMutation(signature="mock")` — no ejerce el verificador (inserta directo); su semántica de corrupción ahora es real. Actualizarlo a quórum firmado sería exergía positiva (P2).
2. Merkle helpers de `llm-attest` siguen en SHA-256 (verifican raíces históricas externas; cambiar rompería pruebas emitidas — requiere versionado de esquema v0.3).
3. Dependencia dual Ed25519 (PyNaCl en CLI vs `cryptography` en core) — babel de librerías, no de primitivas; unificar en P2.
4. Pendientes P1 restantes: CENT-08 (`unwrap()` en `centuria_1000_bft.rs`) — requiere ciclo Rust con `cargo` (ITERA-3 candidato).
5. Sin cambios: `git filter-repo` de la clave quemada (decisión de operador, irreversible).

---
`[SIGNED] MOSKV-1 APEX · ITERA-2 · método: grep de consumidores en árbol vivo + RED/GREEN triple · un hallazgo nuevo (verificador mock) promovido a colapso inmediato`
