"""macOS Seatbelt backend, exercised with the real ``sandbox-exec``.

These tests only run on macOS (the macos-native CI job). Set
BABYLON60_REQUIRE_SEATBELT=1 there so a missing backend fails instead of skipping.
Until a macOS run passes, the Seatbelt backend stays NO_VERIFICADO.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from babylon60.confine import demo, launcher
from babylon60.confine.policy import build_policy, default_homes

REQUIRED = os.environ.get("BABYLON60_REQUIRE_SEATBELT") == "1"
pytestmark = pytest.mark.skipif(
    sys.platform != "darwin" and not REQUIRED, reason="Seatbelt is macOS-only; BABYLON60_REQUIRE_SEATBELT=1 fails instead"
)


@pytest.fixture
def box(tmp_path: Path) -> dict[str, object]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    key = home / ".ssh" / "id_rsa"
    key.write_text("B60-CANARY-seatbelt\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    policy = build_policy(ws, homes=[str(home), *default_homes()], runtime=[launcher.interpreter_prefix()])
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "LC_ALL": "C"}
    return {"home": home, "key": key, "ws": ws, "policy": policy, "env": env}


def test_backend_is_seatbelt() -> None:
    assert launcher.backend() == "seatbelt"


def test_profile_is_accepted_by_sandbox_exec(box: dict[str, object]) -> None:
    from babylon60.confine.seatbelt import SANDBOX_EXEC, render_profile

    profile = render_profile(box["policy"])  # type: ignore[arg-type]
    done = subprocess.run([SANDBOX_EXEC, "-p", profile, "/usr/bin/true"], capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr


def test_home_is_denied_and_workspace_is_writable(box: dict[str, object]) -> None:
    denied = launcher.run(
        launcher.Launch(["/bin/cat", str(box["key"])], box["policy"]),  # type: ignore[arg-type]
        env=box["env"],  # type: ignore[arg-type]
        cwd=str(box["ws"]),
    )
    assert denied.returncode != 0 and b"B60-CANARY" not in denied.stdout
    assert b"Operation not permitted" in denied.stderr
    written = launcher.run(
        launcher.Launch(["/bin/sh", "-c", "echo ok > out.txt && cat out.txt"], box["policy"]),  # type: ignore[arg-type]
        env=box["env"],  # type: ignore[arg-type]
        cwd=str(box["ws"]),
    )
    assert written.returncode == 0 and written.stdout == b"ok\n", written.stderr


def test_real_home_stays_denied(box: dict[str, object]) -> None:
    home = default_homes()[0]
    probe = launcher.run(
        launcher.Launch(["/bin/ls", home], box["policy"]),  # type: ignore[arg-type]
        env=box["env"],  # type: ignore[arg-type]
        cwd=str(box["ws"]),
    )
    assert probe.returncode != 0 and b"Operation not permitted" in probe.stderr


def test_demo_blocks_every_applicable_vector(tmp_path: Path) -> None:
    report = demo.run_demo(journal_path=tmp_path / "journal.db", workers=4)
    totals = report.document["totals"]
    assert report.exit_code == 0, "\n".join(report.transcript)
    assert totals["passed"] == 0 and totals["inconclusive"] == 0
    assert report.document["platform"]["backend"] == "seatbelt"
