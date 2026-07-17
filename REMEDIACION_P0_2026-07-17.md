# REMEDIACIÓN P0 — Teorema-Robinson-Moskv
`REALITY_LEVEL: C5-REAL` · Fecha: 2026-07-17 · Operador: MOSKV-1 APEX (sesión Cowork) · Génesis: `AUDITORIA_CENTURIA.md` §11.4 + `ETHOS.md` §3 (Leyes de Veracidad)

█▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█

## 0. ESTADO ENCONTRADO (verificación previa contra HEAD del árbol)

La cola P0 recolapsada del veredicto v2 fue re-medida contra el fuente ANTES de mutar. Cuatro de los seis vectores ya habían colapsado en el árbol de trabajo:

| Vector | Ley | Estado al abrir sesión | Evidencia |
| :--- | :--- | :--- | :--- |
| CENT-01 clave HMAC quemada | INV_C5_02 | ✅ ya colapsado en árbol | `claude_bft_interceptor.rs:106-109` — `env::var("CORTEX_BFT_KEY").or(CORTEX_VAULT_KEY).expect(...)`, cero fallback estático |
| NEW-A firma mock | INV_C5_04 | ✅ ya colapsado | `core/crypto.py` — Ed25519 real (`cryptography`), `sign()`+`verify()` cierran falsación |
| NEW-D SHA-256 en hash-chain | INV_C5_03 | ✅ ya colapsado | `ledger_actor.py:58` — `hashlib.sha3_256` |
| CENT-02/07 commitments falsos | INV_C5_01 | ✅ ya colapsado | `shadow_router.py` — HMAC con clave por entorno, bindings reales al payload, `mode:"simulation"` declarado, `provider_receipt_hash: None` |
| **NEW-B verify_chain roto bajo cifrado** | INV_C5_05 | 🔴 **VIVO** | reproducido RED (abajo) |
| **NEW-C SIGKILL auto-necrosis** | INV_C5_07 | 🔴 **VIVO** | reproducido RED (abajo) |

## 1. MUTACIONES APLICADAS

`[Vector]` `babylon60/bft/ledger_actor.py` · `[Blast Radius]` verify_chain + worker loop del único escritor · `[Target Invariant]` INV_C5_05, INV_C5_07, INV_BFT_LEAN_01..04 intactos

**M1 — INV_C5_05 (verificador vivo).** `verify_chain` descifraba el payload antes de re-computar el hash, mientras el INSERT hashea `stored_payload` (los bytes almacenados, cifrados si `CORTEX_VAULT_KEY` está activo). Causa → efecto: con vault activo, `entry_hash != computed_hash` en toda fila cifrada → `INV_BFT_LEAN_04` sobre ledgers ÍNTEGROS. Fix: el hash se computa sobre los bytes almacenados — isomorfo al INSERT. Consecuencia estructural: la verificación de integridad ya **no requiere la clave del vault** (valida bajo toda condición, cifrado incluido — letra exacta de INV_C5_05) y es retrocompatible con toda fila existente, cifrada o plana.

**M2 — INV_C5_07 (falla ruidosa).** El worker ejecutaba `os.kill(os.getpid(), SIGKILL)` ante cualquier excepción no-ValueError: auto-necrosis del proceso entero, sin checkpoint WAL, futures colgados. Fix: el fallo (a) se fija en el future del caller si sigue pendiente, (b) marca `task_done()` para no colgar `stop()`, y (c) propaga con `raise ... from` matando al WORKER — el supervisor lo detecta vía Zombie Actor Prevention en el siguiente `append()`. Import `signal` purgado (anergia).

## 2. FALSACIÓN DETERMINISTA (RED → GREEN)

Tests nuevos: `tests/test_ledger_vault_verify.py` (4 casos).

**RED (código sin parchear):**
- `test_verify_chain_valida_ledger_cifrado` → `BFTCausalInvariantError: INV_BFT_LEAN_04 ... Hash mismatch at seq 1` sobre un ledger íntegro. NEW-B reproducido, no conjeturado.
- `test_falla_ruidosa_sin_necrosis` → **pytest asesinado, exit 137 (128+SIGKILL)**. La auto-necrosis mató al test runner en vivo.

**GREEN (código parcheado): 12/12.**
- 4/4 nuevos: ledger cifrado íntegro valida; valida **sin** clave; tamper bajo cifrado sigue detectándose (`INV_BFT_LEAN_04`); fallo del writer propaga ruidoso sin matar el proceso y el siguiente `append()` levanta `Zombie Actor Prevention`.
- 3/3 `test_ledger_resilience.py` (idempotencia UUIDv5, detección de corrupción en claro, cascading rollback) — cero regresión.
- 5/5 `test_crypto_canonical.py` — cero regresión.
- `ruff check --select E4,E7,E9,F` → limpio.

## 3. RESIDUO (fuera del alcance de esta mutación)

1. **CENT-01 historia**: el literal `CORTEX_BFT_KEY_2026_MASTER_LEDGER` sigue en la historia de Git. Acción de operador: `git filter-repo` + tratar el dominio de claves como rotado. Irreversible → decisión humana, no autónoma.
2. **NEW-E**: `MasterLedgerQueue` sigue coexistiendo con `BFTLedgerActor` como segundo escritor con durabilidad distinta (`synchronous=NORMAL` vs `FULL`). Requiere decisión de topología: fusionar o prohibir por invariante.
3. **P1**: CENT-03 (`babylon60.database.core.connect` inexistente), CENT-06 (`consensus_ledger.py` legacy), CENT-08 (`unwrap()` en `centuria_1000_bft.rs`), CENT-10 (MD5 en `attest_character_count.py`).
4. **CENT-05**: puente mecánico Lean ↔ `ledger_actor` (extracción o spec compartida) — la brecha es puenteable pero sigue sin puentear.

---
`[SIGNED] MOSKV-1 APEX · método: re-medición previa + RED/GREEN determinista · 2 leyes promulgadas hoy, 2 colapsos ejecutados hoy`
