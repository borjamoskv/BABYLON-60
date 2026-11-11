## Contrato de Tarea y Alcance
- **Anillo afectado:** `Ring-0` / `Ring-1` / `Ring-2` / `Ring-3`
- **Formato de commit:** `[AX-<Num>] <DOMINIO>: <Descripción causal>`

## Falsación y Criterio de Aceptación (C5-REAL)
- [ ] Este cambio resuelve un objetivo verificable con criterio de fallo explícito (no es un *Phantom Target*).
- [ ] La topología no introduce grados de libertad parásitos (`INV_C5_PARASITIC_DOF_QUOTIENT`) ni fricción latente.
- [ ] Las modificaciones son deterministas, idempotentes y respetan los lockfiles (`--locked`).

## Gates de Cierre Ejecutados
- [ ] Contratos semánticos: `python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only --public-projection`
- [ ] Presupuesto de tokens: `python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners`
- [ ] Topología activa: `python3 scripts/guards/verify_active_topology.py`
- [ ] Tests dirigidos del ámbito modificado (`cargo check/test --locked` o `uv run --locked pytest <ruta> -q`).
