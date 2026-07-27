#!/usr/bin/env python3
"""Lightweight runtime smoke for the restored BABYLON60 surfaces.
This smoke intentionally checks a narrow but high-value slice:

- FastAPI app imports and exposes routes
- Babylon60Engine initializes against an isolated temp database
- CLI help renders without crashing
"""

from __future__ import annotations

import logging

import subprocess
import sys
import tempfile
from pathlib import Path


def _check_api_import() -> None:
    from babylon60.api import app

    route_count = len(getattr(app.router, "routes", []))
    if app.__class__.__name__ != "FastAPI":
        raise RuntimeError(f"unexpected app type: {app.__class__.__name__}")
    if route_count == 0:
        raise RuntimeError("FastAPI app loaded with no registered routes")
    logging.getLogger(__name__).info(f"[smoke-api] API import OK ({route_count} routes)")


def _check_engine_init(tmp_dir: Path) -> None:
    from babylon60.engine import Babylon60Engine

    db_path = tmp_dir / "smoke.db"
    engine = Babylon60Engine(db_path=str(db_path))
    if engine.__class__.__name__ != "Babylon60Engine":
        raise RuntimeError(f"unexpected engine type: {engine.__class__.__name__}")
    logging.getLogger(__name__).info(f"[smoke-api] Engine init OK ({db_path.name})")


def _check_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "babylon60", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "python -m babylon60 --help failed")

    stdout = result.stdout.lower()
    if "usage" not in stdout and "commands" not in stdout:
        raise RuntimeError("CLI help rendered without expected usage output")
    logging.getLogger(__name__).info("[smoke-api] CLI help OK")


def main() -> int:
    try:
        _check_api_import()
        with tempfile.TemporaryDirectory(prefix="babylon60-smoke-") as tmp:
            _check_engine_init(Path(tmp))
        _check_cli_help()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).info(f"[smoke-api] FAIL: {exc}", file=sys.stderr)
        return 1

    logging.getLogger(__name__).info("[smoke-api] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
