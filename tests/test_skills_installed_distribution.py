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


@pytest.mark.parametrize(
    ("query", "expected_code", "names"),
    [
        ("epistemic-simplifier", 0, ["wait-what"]),
        ("itera", 2, []),
        ("No uses /wait-what", 2, []),
        ("$wait-what; $grill-me-v2", 3, ["grill-me-v2", "wait-what"]),
    ],
)
def test_cli_matches_workspace_router(query: str, expected_code: int, names: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    import argparse
    from babylon60.cli.main_dispatcher import cmd_skills

    root = Path(__file__).resolve().parents[1] / ".agents" / "skills"
    routed = subprocess.run(
        [sys.executable, str(root / "_skill_router.py"), "--library-root", str(root), "--query", query],
        capture_output=True,
        text=True,
        check=False,
    )
    assert routed.returncode == expected_code, routed.stderr
    expected = json.loads(routed.stdout)
    assert sorted(item["name"] for item in expected) == sorted(names)
    code = cmd_skills(argparse.Namespace(skills_action="route", scope="workspace", role="all", query=query, json=True))
    actual = json.loads(capsys.readouterr().out)
    assert code == expected_code
    assert sorted([actual["name"]] if code == 0 else actual["candidates"]) == sorted(names)
    if code == 0:
        assert actual["procedure_path"] == str(Path(expected[0]["module"]).relative_to(root.parents[1]))
        assert actual["artifact_provenance"] == "workspace_disk"


def test_cli_does_not_route_catalog_only_or_wrong_role(capsys: pytest.CaptureFixture[str]) -> None:
    import argparse
    from babylon60.cli.main_dispatcher import cmd_skills

    for scope, role, query in [
        ("global", "all", "handoff"),
        ("workspace", "ejecutor", "epistemic-simplifier"),
    ]:
        assert cmd_skills(
            argparse.Namespace(skills_action="route", scope=scope, role=role, query=query, json=True)
        ) == 2
        assert json.loads(capsys.readouterr().out)["candidates"] == []


def test_cli_explicit_continuation(capsys: pytest.CaptureFixture[str]) -> None:
    import argparse
    from babylon60.cli.main_dispatcher import cmd_skills

    assert cmd_skills(
        argparse.Namespace(skills_action="route", scope="workspace", role="all", query="sigue",
                           context="epistemic-simplifier", json=True)
    ) == 0
    assert json.loads(capsys.readouterr().out)["name"] == "wait-what"


def test_workspace_metadata_matches_distribution() -> None:
    root = Path(__file__).resolve().parents[1] / ".agents" / "skills"
    registry = json.loads((root / "skills.json").read_text(encoding="utf-8"))
    entries = registry["entries"]
    assert {entry["name"] for entry in entries} == {path.parent.name for path in root.glob("*/SKILL.md")}
    assert registry["total_skills"] == len(entries)
    assert registry["average_exergy_density"] == round(sum(entry["tier"] for entry in entries) / len(entries), 2)


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
import json
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from babylon60.cli.main_dispatcher import cmd_skills
from babylon60.mcp.cortex_mcp_server import CortexMCPServer
expected_total = len(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["entries"])
server = CortexMCPServer(ledger_path=Path('ledger.db'), causal_gate_path=Path('gate.db'))
assert server._skills_snapshot.total_skills == expected_total
assert cmd_skills(argparse.Namespace(skills_action="list", scope="workspace", role="all", query=None, json=True)) == 0
assert cmd_skills(argparse.Namespace(skills_action="route", scope="workspace", role="all", query="epistemic-simplifier", json=True)) == 0
assert cmd_skills(argparse.Namespace(skills_action="status", scope="all", role="all", query=None, json=True)) == 0
import contextlib
import io
for query, code in [("itera", 2), ("No uses /wait-what", 2), ("$wait-what; $grill-me-v2", 3)]:
    with contextlib.redirect_stdout(io.StringIO()) as output:
        assert cmd_skills(argparse.Namespace(skills_action="route", scope="workspace", role="all",
                                            query=query, json=True)) == code
    assert json.loads(output.getvalue())["elected"] is None
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(installed), str(root / "docs/skills.json")],
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
    assert route["artifact_provenance"] == "installed_distribution"
    assert status["procedure_entries"] == expected
    assert status["catalog_only_entries"] == status["total_skills"] - expected
    assert status["workspace_canonical_alias_coverage"] == f"{expected}/{expected}"
    catalog = json.loads((root / "docs/skills.json").read_text(encoding="utf-8"))
    assert status["functorial_dag_edges"] == len(catalog["adjacency"]) > 0
