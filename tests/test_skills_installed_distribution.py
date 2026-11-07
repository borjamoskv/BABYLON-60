"""Exercise actual wheel resources with an isolated import outside the checkout."""

import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest


def test_skills_without_resources_abc(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Python 3.10 has resources.files, but no resources.abc submodule."""
    import argparse
    import importlib.resources
    import yaml
    from babylon60.cli.main_dispatcher import cmd_skills

    assert callable(importlib.resources.files)
    assert callable(yaml.safe_load)
    monkeypatch.setitem(sys.modules, "importlib.resources.abc", None)
    assert (
        cmd_skills(
            argparse.Namespace(
                skills_action="route", scope="workspace", role="all", query="epistemic-simplifier", json=True
            )
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["name"] == "wait-what"


def test_skills_catalog_from_installed_wheel(tmp_path: Path) -> None:
    root = Path(__file__).absolute().parents[1]
    wheel_dir = tmp_path / "wheels"
    subprocess.run(
        ["uv", "build", "--offline", "--wheel", "--out-dir", str(wheel_dir), str(root)],
        check=True,
        capture_output=True,
        text=True,
    )
    installed = tmp_path / "site-packages"
    with zipfile.ZipFile(next(wheel_dir.glob("*.whl"))) as wheel:
        wheel.extractall(installed)
    # -I ignores PYTHONPATH and the checkout; existing dependencies remain available.
    script = """
import argparse
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from babylon60.cli.main_dispatcher import cmd_skills
from babylon60.mcp.cortex_mcp_server import CortexMCPServer
server = CortexMCPServer(ledger_path=Path('ledger.db'), causal_gate_path=Path('gate.db'))
assert server._skills_snapshot.total_skills == 131
assert cmd_skills(argparse.Namespace(skills_action="list", scope="workspace", role="all", query=None, json=True)) == 0
assert cmd_skills(argparse.Namespace(skills_action="route", scope="workspace", role="all", query="epistemic-simplifier", json=True)) == 0
assert cmd_skills(argparse.Namespace(skills_action="status", scope="all", role="all", query=None, json=True)) == 0
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(installed)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    decoder = json.JSONDecoder()
    listing, end = decoder.raw_decode(result.stdout)
    route, end_route = decoder.raw_decode(result.stdout[end:].lstrip())
    remaining = result.stdout[end:].lstrip()[end_route:].lstrip()
    status = json.loads(remaining)
    expected = sum(1 for path in (root / ".agents/skills").iterdir() if (path / "SKILL.md").is_file())
    assert listing["total"] == expected > 0
    assert route["name"] == "wait-what"
    assert route["path"] == "babylon60/mcp/resources/skills/wait-what/SKILL.md"
    assert status["workspace_canonical_alias_coverage"] == f"{expected}/{expected}"
    catalog = json.loads((root / "docs/skills.json").read_text(encoding="utf-8"))
    assert status["functorial_dag_edges"] == len(catalog["adjacency"]) > 0
