# Guía de Contribución a BABYLON-60

Toda contribución (humana o mediante agentes autónomos) se rige por los contratos formales del proyecto.

## 1. Fuentes Canónicas
- **Reglas del workspace:** [.babylon60rules](.babylon60rules)
- **Protocolo de trabajo con agentes:** [AGENTS.md](AGENTS.md)
- **Contratos por anillo:** [docs/03_guides/agent_contracts.md](docs/03_guides/agent_contracts.md)

## 2. Contratos por Anillo de Seguridad

| Ámbito afectado | Anillo | Contrato Requerido |
| :--- | :--- | :--- |
| Memoria, IPC, biometría, persistencia, Rust o aislamiento | **Ring-0** | [Ring-0 en agent_contracts.md](docs/03_guides/agent_contracts.md#ring-0) |
| Lean 4, Z3, PoC, concurrencia o garantías formales | **Ring-1** | [Ring-1 en agent_contracts.md](docs/03_guides/agent_contracts.md#ring-1) |
| CI, Git, dependencias, ledger, datasets o licencias | **Ring-2** | [Ring-2 en agent_contracts.md](docs/03_guides/agent_contracts.md#ring-2) |
| UI, voz, documentación, rutas o salida | **Ring-3** | [Ring-3 en agent_contracts.md](docs/03_guides/agent_contracts.md#ring-3) |

## 3. Convención de Commits y PRs
- **Formato obligatorio de commit:** `[AX-<Num>] <DOMINIO>: <Descripción causal>` (ej. `[AX-0] CI: homogenizar fijación de acciones y permisos en workflows`).
- **Verificación previa a commit / PR:**
  ```bash
  # Contratos semánticos y enlaces
  python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only --public-projection

  # Presupuesto de tokens
  python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners

  # Topología activa
  python3 scripts/guards/verify_active_topology.py

  # Test dirigido del subsistema afectado
  cargo test --workspace --locked
  uv run --locked pytest <ruta_test> -q
  ```

## 4. Política de Dependencias y Lockfiles
- Prohibido modificar dependencias sobre un árbol de trabajo sucio (`INV_C5_CLEAN_WORKTREE_LOCK_GATE`).
- Toda adición o actualización de paquetes debe preservar los lockfiles (`Cargo.lock`, `uv.lock`) y pasar las suites con `--locked`.
