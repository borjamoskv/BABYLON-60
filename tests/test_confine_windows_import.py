"""Regression checks for Windows host compatibility of CLI subparser registration."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import os
from pathlib import Path
import subprocess
import sys

import pytest

from babylon60.cli import main_dispatcher

ROOT = Path(__file__).absolute().parents[1]


def test_cli_help_and_confine_arguments_do_not_require_posix_modules() -> None:
    """Simulate a Windows host where POSIX-only stdlib modules are absent."""
    code = (
        "import sys\n"
        "for mod in ('pwd', 'grp', 'fcntl', 'termios', 'pty', 'resource'):\n"
        "    sys.modules[mod] = None\n"
        "from babylon60.confine.arguments import register_confine_subparsers\n"
        "from babylon60.cli import main_dispatcher\n"
        "sys.argv = ['babylon60', '--help']\n"
        "try:\n"
        "    main_dispatcher.main()\n"
        "except SystemExit as exc:\n"
        "    assert exc.code == 0, exc.code\n"
    )
    existing_pp = os.environ.get("PYTHONPATH", "")
    kish_path = str(ROOT / "01_KISH_ENGINE")
    pythonpath = f"{kish_path}{os.pathsep}{existing_pp}" if existing_pp else kish_path
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "PYTHONPATH": pythonpath},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "run" in proc.stdout and "demo" in proc.stdout and "log" in proc.stdout


@pytest.mark.parametrize("handler", [main_dispatcher.cmd_run, main_dispatcher.cmd_demo, main_dispatcher.cmd_log])
def test_confine_commands_fail_closed_on_windows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    handler: Callable[[argparse.Namespace], int],
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    rc = handler(argparse.Namespace())
    assert rc == 1
    assert "Confinement requires Linux or macOS." in capsys.readouterr().err


def test_landlock_monitor_reaches_waitpid_loop() -> None:
    """Guard against accidental early os._exit before waitpid in _landlock_exec._monitor."""
    import ast

    source = (ROOT / "01_KISH_ENGINE/babylon60/confine/_landlock_exec.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    monitor = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_monitor")
    loop_indices = [idx for idx, stmt in enumerate(monitor.body) if isinstance(stmt, ast.For)]
    assert loop_indices, "_monitor must contain its signal/waitpid loops"
    first_loop = loop_indices[0]
    for stmt in monitor.body[:first_loop]:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            fn = stmt.value.func
            if isinstance(fn, ast.Attribute) and fn.attr == "_exit":
                pytest.fail("_monitor calls os._exit unconditionally before its waitpid loop")
