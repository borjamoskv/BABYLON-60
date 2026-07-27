# Project: T-Cell Monitoring Daemon Upgrade

## Architecture
- `babylon60/extensions/daemon/t_cell_ihelp_purge.py`: Holds the `IHelpPurgeDaemon` which compiles a dynamic regex and registers with `MHCAntigenRouter`.
- `babylon60/routes/telemetry.py`: Holds `BASE_MAFIA_NODES` and provides the dynamic list of telemetry target nodes.
- `babylon60/engine/causal/taint_engine.py`: Holds `MHCAntigenRouter` which manages antigen routing and dynamic antigen learning.
- `babylon60/audit/ledger.py`: Master Ledger interface (`EnterpriseAuditLedger`) for recording security events.
- `tests/extensions/daemon/test_mafia_t_cell.py`: Unit tests for dynamic T-Cell regex validation and high-concurrency checks.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Fix Core Import Issue | Resolve `from .swarm` import issue in `babylon60/engine/__init__.py` | none | DONE |
| 2 | Dynamic Antigen Ingestion | Refactor `t_cell_ihelp_purge.py` to dynamically load and construct regex from telemetry nodes | M1 | DONE |
| 3 | High-Concurrency Swarm Monitoring | Implement async-based parallel checkout of all Mafia domains and log events to Master Ledger | M2 | DONE |
| 4 | Unit Tests and Verification | Write unit test suite `test_mafia_t_cell.py` and run full checks (ruff, pyright, pytest) | M3 | DONE |

## Interface Contracts
### `IHelpPurgeDaemon` ↔ `babylon60.routes.telemetry`
- Load targets dynamically from `BASE_MAFIA_NODES` or the telemetry endpoint.
- Returns list of nodes (str).

### `IHelpPurgeDaemon` ↔ `MHCAntigenRouter`
- `register_t_cell(agent_id, antigen_regex)` for dynamically constructed regex signature.

### `IHelpPurgeDaemon` ↔ `EnterpriseAuditLedger`
- Log actions via `log_action(timestamp, tenant_id, actor_role, actor_id, action, resource, status, metadata)` with SHA3-256 signatures and `BABYLON60-TAINT` metadata.

## Code Layout
- `babylon60/extensions/daemon/t_cell_ihelp_purge.py`
- `babylon60/engine/__init__.py`
- `tests/extensions/daemon/test_mafia_t_cell.py`
