"""Generated distributions preserve specializations and resolve without host paths."""

from pathlib import Path
import json
import subprocess
import sys

import pytest
from scripts.c5_skills_ontology.build_skill_library import build
from scripts.c5_quality_gates.audit_skill_links import inspect
from tools.skill_library.router import RouteRecord, select


def test_contextual_routing() -> None:
    records: list[RouteRecord] = [
        {"name": "special", "aliases": ["itera", "audit", "auditoría", "formalizar en lean"], "module": "special.md"}
    ]
    assert select("itera", records) == []
    assert select("audit", records) == []
    assert select("por favor itera", records) == []
    assert select("/special", records) == records
    assert select("quiero formalizar en lean", records) == records


def test_intent_routing_requires_action_and_respects_negation_and_context() -> None:
    records: list[RouteRecord] = [
        {
            "name": "formal",
            "aliases": ["formalizar en lean"],
            "module": "formal.md",
            "intent": {"actions": ["revisa"], "topics": ["lean"], "exclude": ["tutorial"]},
        }
    ]
    assert select("leer sobre lean", records) == []
    assert select("no revisa lean", records) == []
    assert select("revisa tutorial lean", records) == []
    assert select("revisa lean", records) == records
    assert select("$formal", records) == records
    assert select("sigue", records, context="revisa lean") == records
    assert select("sigue", records) == []


@pytest.mark.parametrize("environment", ["antigravity", "codex", "workspace"])
def test_distribution_is_portable_and_router_runs(tmp_path: Path, environment: str) -> None:
    output = tmp_path / "library"
    build(output, environment)
    for table in output.glob("*/references/aliases.json"):
        hub = table.parent.parent
        record = json.loads(table.read_text())["modules"][0]
        assert (hub / record["module"]).is_file()
        result = subprocess.run(
            [sys.executable, str(hub / "scripts/route.py"), "--query", record["name"]], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)[0]["name"] == record["name"]
        library_result = subprocess.run(
            [
                sys.executable,
                str(output / "_skill_router.py"),
                "--library-root",
                str(output),
                "--query",
                record["name"],
            ],
            capture_output=True,
            text=True,
        )
        assert library_result.returncode == 0, library_result.stderr
        assert json.loads(library_result.stdout) == json.loads(result.stdout)
    for p in output.glob("*/references/modules/*/MODULE.md"):
        assert "~/.gemini/config/skills/" not in p.read_text()
    assert (output / "_skill_router.py").is_file()
    checker = subprocess.run(
        [sys.executable, str(output / "_skill_checks/declarative.py"), "--root", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert checker.returncode == 0, checker.stdout + checker.stderr
    assert json.loads(checker.stdout)["status"] == "pass"
    assert not [f for f in inspect([output], remote=False)["findings"] if f["status"] == "broken"]
    with pytest.raises(FileExistsError):
        build(output, environment)


def test_codex_override_preserved(tmp_path: Path) -> None:
    codex = tmp_path / "codex"
    global_ = tmp_path / "global"
    build(codex, "codex")
    build(global_, "antigravity")
    assert (codex / "youtube-remotion-sota/SKILL.md").read_text() != (
        global_ / "youtube-remotion-sota/SKILL.md"
    ).read_text()
    assert (codex / "wrangler/SKILL.md").is_file()
    assert not (global_ / "wrangler").exists()


def test_legacy_registry_contract_preserved(tmp_path: Path) -> None:
    output = tmp_path / "library"
    build(output, "antigravity")
    registry = json.loads((output / "skills.json").read_text())
    assert isinstance(registry["entries"], list)
    assert registry["adjacency"]
    assert all("itera" not in e.get("triggers", []) for e in registry["entries"])


def test_workspace_distribution_matches_canonical_sources(tmp_path: Path) -> None:
    from scripts.c5_quality_gates.freeze_skills_manifest import inventory
    from scripts.c5_skills_ontology.build_skill_library import ROOT

    output = tmp_path / "library"
    build(output, "workspace")
    expected = inventory(output)["entries"]
    actual = inventory(ROOT / ".agents/skills")["entries"]
    # The pre-existing container's permissions do not belong to the generated port.
    actual["."] = expected["."]
    assert actual == expected


@pytest.mark.parametrize("environment", ["antigravity", "codex", "workspace"])
def test_generation_reproducible_across_seeds_and_registry_matches(tmp_path: Path, environment: str) -> None:
    import os
    import yaml
    from scripts.c5_quality_gates.freeze_skills_manifest import inventory
    from scripts.c5_skills_ontology.build_skill_library import ROOT

    builder = ROOT / "scripts/c5_skills_ontology/build_skill_library.py"
    outputs = []
    for seed in ["1", "99"]:
        output = tmp_path / seed
        subprocess.run(
            [sys.executable, str(builder), "--environment", environment, "--output", str(output)],
            env={**os.environ, "PYTHONHASHSEED": seed},
            check=True,
            capture_output=True,
        )
        outputs.append(output)
    assert inventory(outputs[0]) == inventory(outputs[1])
    output = outputs[0]
    catalog = json.loads((output / "skill_catalog.generated.json").read_text())["skills"]
    registry = json.loads((output / "skills.json").read_text())
    assert {e["name"] for e in registry["entries"]} == set(catalog)
    assert registry["total_skills"] == len(catalog)
    for name, fm in catalog.items():
        assert yaml.safe_load((output / name / "SKILL.md").read_text().split("---", 2)[1]) == fm
    for edge in registry["adjacency"]:
        assert edge["source"] in catalog and edge["target"] in catalog


def test_ambiguous_cli_does_not_claim_unique_route(tmp_path: Path) -> None:
    hub = tmp_path / "hub"
    (hub / "references").mkdir(parents=True)
    records = [{"name": name, "aliases": ["shared phrase"], "module": name + ".md"} for name in ["one", "two"]]
    for record in records:
        (hub / str(record["module"])).write_text("Specialized procedure")
    (hub / "references/aliases.json").write_text(json.dumps({"modules": records}))
    from scripts.c5_skills_ontology.build_skill_library import SOURCE

    result = subprocess.run(
        [sys.executable, str(SOURCE / "router.py"), "--hub-root", str(hub), "--query", "shared phrase"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert len(json.loads(result.stdout)) == 2


@pytest.mark.parametrize("module", ["missing.md", "../outside.md"])
def test_cli_rejects_missing_or_escaping_procedure(tmp_path: Path, module: str) -> None:
    from scripts.c5_skills_ontology.build_skill_library import SOURCE

    hub = tmp_path / "hub"
    (hub / "references").mkdir(parents=True)
    (tmp_path / "outside.md").write_text("External procedure")
    record: RouteRecord = {"name": "special", "aliases": ["special"], "module": module}
    (hub / "references/aliases.json").write_text(json.dumps({"modules": [record]}))
    result = subprocess.run(
        [sys.executable, str(SOURCE / "router.py"), "--hub-root", str(hub), "--query", "special"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "outside its hub" in result.stderr
