---
title: Fuente de Verdad Canónica del Repositorio
status: Causal-Determinist
version: 1.0.0
---

# Fuente de Verdad Canónica del Repositorio

<div align="center">

[![C5-REAL Compliant](https://img.shields.io/badge/C5--REAL-Verified-0052CC?style=for-the-badge&logo=shield)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/06_theory/AUDIT_VERDICT_C5_REAL.md)
[![Regime](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/06_theory/AXIOMATIZATION_C5_REAL.md)
[![License](https://img.shields.io/badge/Licencia-Soberana_INV__C5__17-008055?style=for-the-badge)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/STATUS.md)

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
