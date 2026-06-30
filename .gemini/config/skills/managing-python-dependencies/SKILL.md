---
name: managing-python-dependencies
description: |
  C5-REAL Sovereign Protocol for Python dependency management.
  Enforces deterministic, isolated package installation.
  Triggers:
    - Attempting `pip install {package_name}`
    - Adding/modifying Python packages
    - Initiating Python project
    - Python environment execution
    - Encountering ModuleNotFoundError or ImportError
  Guards:
    - P0: Global pip install is FORBIDDEN.
    - P0: Tooling override bypass is FORBIDDEN.
    - P1: Lock file coherence must be verified post-mutation.
license: Apache-2.0
metadata:
  version: v3.0.0
  publisher: borjamoskv
  reality_level: C5-REAL
  exergy_tier: P1
script: scripts/managing_python_dependencies.py
---

# Python Dependency Governance (C5-REAL)

Execution Level: **C5-REAL** (System State Mutation). Every dependency injection alters the physical execution environment. Treat it as a Saga write-path.

## §1 — Detection Hierarchy (Priority Order)

The agent MUST scan the project root **top-down** using TOML parsing (not substring matching) and lock onto the **first** signal detected. Ambiguity = abort.

| Priority | Signal | Manager | Install Command | Setup Command | Lock File |
|:---:|:---|:---|:---|:---|:---|
| 1 | `uv.lock` or `[tool.uv]` in `pyproject.toml` | **uv** | `uv add <pkg>` | `uv sync` | `uv.lock` |
| 2 | `[tool.poetry]` in `pyproject.toml` | **poetry** | `poetry add <pkg>` | `poetry install` | `poetry.lock` |
| 3 | `[tool.pdm]` in `pyproject.toml` or `pdm.lock` | **pdm** | `pdm add <pkg>` | `pdm install` | `pdm.lock` |
| 4 | `Pipfile` | **pipenv** | `pipenv install <pkg>` | `pipenv install` | `Pipfile.lock` |
| 5 | `environment.yml` | **conda** | `conda install <pkg>` | `conda env create -f environment.yml` | `conda-lock.yml` (if present) |
| 6 | `pyproject.toml` (no uv/poetry/pdm) | **pip** | `.venv/bin/pip install <pkg>` | `pip install -e ".[all]"` | `requirements.txt` (generated) |
| 7 | `requirements.txt` | **venv+pip** | `.venv/bin/pip install <pkg>` | `.venv/bin/pip install -r requirements.txt` | `requirements.txt` |
| 8 | (None) | **venv+pip** | (See Fallback §3) | (See Fallback §3) | — |

## §2 — Invariants (Non-Negotiable)

1. **Global pip is dead.** Never execute bare `pip install`. Always use the resolved manager or explicit venv path (`.venv/bin/pip`).
2. **Lock file coherence.** After any dependency mutation, verify the lock file exists and has been updated. If the manager produces a lock file, it MUST be committed.
3. **Editable installs for monorepos.** Projects with `pyproject.toml` and `[project.optional-dependencies]` MUST use `pip install -e ".[extra1,extra2]"` inside the venv.
4. **Version pinning.** New dependencies MUST specify minimum version constraints (`>=x.y.z`), never unconstrained.
5. **No implicit upgrades.** `--upgrade` flag requires explicit operator intent. Default behavior preserves current pins.
6. **Python version gate.** Verify `requires-python` constraint in `pyproject.toml` matches the active interpreter before any install. The script enforces this automatically.
7. **Conflict resolution.** If dependency check reports conflicts post-install, ABORT and report. Do not silently proceed.
8. **Exit codes.** The script MUST return non-zero on verification failures for CI integration.

## §3 — Fallback Protocol (No Manager Detected)

When no dependency manager signal is found, the script automatically creates an isolated C5-REAL environment:

```bash
# 1. Create venv (automated by script --install)
python3 -m venv .venv

# 2. Install
.venv/bin/pip install <package>

# 3. Freeze state (deterministic snapshot)
.venv/bin/pip freeze > requirements.txt

# 4. Verify
.venv/bin/pip check
```

## §4 — CORTEX-Persist Specific Protocol

This repository uses `uv` as its canonical dependency manager (`uv.lock` present).

```bash
# Add a new dependency
uv add <package>

# Sync environment from lock file
uv sync

# Verify coherence
uv pip check
```

The `pyproject.toml` also defines optional dependency groups (`compute`, `secure`, `api`, `mcp`, `distributed`, `daemon`) installable via `uv sync --extra api --extra mcp` or equivalent pip editable install.

## §5 — Anti-Patterns (Failure Signatures)

| Signal | Severity | Remediation |
|:---|:---:|:---|
| Bare `pip install` without venv prefix | **P0** | Prepend `.venv/bin/` or use resolved manager |
| `--break-system-packages` flag | **P0** | NEVER. Create venv instead |
| Missing lock file after install | **HIGH** | Run freeze/lock command for the detected manager |
| `pip install` inside `sudo` | **P0** | Abort immediately. Escalate to operator |
| Unconstrained version (`pkg` without `>=`) | **MEDIUM** | Add minimum version pin |
| Dependency check reports broken deps | **HIGH** | Resolve conflicts before proceeding |
| Mixing managers (poetry + pip + uv) in same project | **HIGH** | Pick one. Consolidate |
| `requires-python` mismatch with active interpreter | **HIGH** | Switch interpreter or update constraint |
