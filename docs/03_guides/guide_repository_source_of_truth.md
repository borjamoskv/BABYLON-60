---
title: Fuente de Verdad Canónica del Repositorio
status: Causal-Determinist
version: 1.0.0
---

# Fuente de Verdad Canónica del Repositorio

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

BABYLON-60 is the repository and protocol project.
`Ledger Asíncrono-persist` is the Python distribution name.
`babylon60` is the implementation namespace.
`Ledger Asíncrono` is the user-facing CLI.

## Canonical Namespaces

- **Active package:** `babylon60`
- **Legacy package:** `Ledger Asíncrono` (moved to `experimental/cortex_legacy`)
- **Canonical ledger implementation:** `babylon60/core/master_ledger.py`
- **Canonical tests:** `tests/`
- **Release artifact:** `Ledger Asíncrono-persist` PyPI wheel

## Canonical Commands

The single official command suite for Continuous Integration:

```bash
uv run pytest tests/
uv run ruff check babylon60 tests scripts
uv run ruff format --check babylon60 tests scripts
uv run pyright babylon60
uv run python -m build
```