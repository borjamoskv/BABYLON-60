# Source of Truth

BABYLON-60 is the repository and protocol project.
`cortex-persist` is the Python distribution name.
`babylon60` is the implementation namespace.
`cortex` is the user-facing CLI.

## Canonical Namespaces

- **Active package:** `babylon60`
- **Legacy package:** `cortex` (moved to `experimental/cortex_legacy`)
- **Canonical ledger implementation:** `babylon60/core/master_ledger.py`
- **Canonical tests:** `tests/`
- **Release artifact:** `cortex-persist` PyPI wheel

## Canonical Commands

The single official command suite for Continuous Integration:

```bash
uv run pytest tests/
uv run ruff check babylon60 tests scripts
uv run ruff format --check babylon60 tests scripts
uv run pyright babylon60
uv run python -m build
```
