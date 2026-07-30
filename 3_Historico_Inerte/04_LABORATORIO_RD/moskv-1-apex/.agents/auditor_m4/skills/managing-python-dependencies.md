---
name: managing-python-dependencies
description: |
  Ensures proper Python dependency management.
  C5-REAL Execution protocol for Python environments.
  Triggers:
    - Attempting `pip install {package_name}`
    - Adding/modifying Python packages
    - Initiating Python project
    - Python environment execution
license: Apache-2.0
metadata:
  version: v1
  publisher: google
script: scripts/managing_python_dependencies.py
---

# Python Environment Matrix (C5-REAL)

Execution Level: C5-REAL (System State Mutation).

**Constraints:**
- NEVER use global `pip install`.
- Tooling overrides PROHIBITED.

## Detection & Execution Hierarchy

| Signal | Manager | C5-REAL Install | C5-REAL Setup |
| :--- | :--- | :--- | :--- |
| `uv.lock` or `[tool.uv]` | uv | `uv add <pkg>` | `uv sync` |
| `[tool.poetry]` | poetry | `poetry add <pkg>` | `poetry install` |
| `Pipfile` | pipenv | `pipenv install <pkg>` | `pipenv install` |
| `environment.yml` | conda | `conda install <pkg>` | `conda env create -f environment.yml` |
| `requirements.txt` | venv+pip | `.venv/bin/pip install <pkg>` | `.venv/bin/pip install -r requirements.txt` |
| (None) | venv+pip | (See Fallback) | (See Fallback) |

## Fallback Protocol (venv + pip)

If no signal detected, enforce isolated C5-REAL state:

```bash
python3 -m venv .venv
.venv/bin/pip install <package>
.venv/bin/pip freeze > requirements.txt
```

*Note: Explicit paths ONLY (`.venv/bin/pip`). State preservation required.*
