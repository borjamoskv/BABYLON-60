# [C5-REAL] Exergy-Maximized
"""Version consistency tests.

Ensures the canonical ``babylon60.__version__`` is the single source of truth
and that all downstream consumers (pyproject.toml, CHANGELOG.md, FastAPI app)
stay in sync. Also validates the cortex backward-compat shim.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import tomllib

import babylon60
import cortex

ROOT = Path(__file__).resolve().parents[1]


# ─── Helpers ──────────────────────────────────────────────────────────


def _pyproject_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]["version"]


# ─── Tests ────────────────────────────────────────────────────────────


def test_module_version_matches_pyproject() -> None:
    """babylon60.__version__ must equal pyproject.toml [project].version."""
    assert babylon60.__version__ == _pyproject_version()


def test_cortex_shim_version_matches_babylon60() -> None:
    """cortex shim must proxy babylon60.__version__ correctly."""
    assert cortex.__version__ == babylon60.__version__


def test_changelog_has_entry_for_current_version() -> None:
    """CHANGELOG.md must contain a heading for the current release version."""
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    # Keep-a-Changelog format: ## [x.y.z] — date
    pattern = re.compile(rf"^## \[{re.escape(babylon60.__version__)}\]", re.MULTILINE)
    assert pattern.search(changelog), (
        f"CHANGELOG.md has no entry for version {babylon60.__version__}"
    )


def test_fastapi_app_uses_module_version() -> None:
    """babylon60/api/core.py must import __version__ and pass it to FastAPI()."""
    core_path = ROOT / "babylon60" / "api" / "core.py"
    source = core_path.read_text(encoding="utf-8")

    # 1. Verify the import is present (canonical babylon60 namespace)
    assert "from babylon60 import __version__" in source, (
        "babylon60/api/core.py must import __version__ from babylon60"
    )

    # 2. Verify FastAPI() is instantiated with version=__version__ (AST check)
    tree = ast.parse(source, filename=str(core_path))
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Match FastAPI(...)
        func = node.func
        if isinstance(func, ast.Name) and func.id == "FastAPI":
            for kw in node.keywords:
                if kw.arg == "version":
                    # Accept version=__version__ (ast.Name with id "__version__")
                    if isinstance(kw.value, ast.Name) and kw.value.id == "__version__":
                        found = True
    assert found, (
        "FastAPI() in babylon60/api/core.py must use version=__version__, not a hardcoded string"
    )
