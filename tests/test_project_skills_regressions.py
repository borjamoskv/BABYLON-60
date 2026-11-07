"""Executable counterexamples for the eleven public project-skill findings.

Document semantics are also reviewed independently; lexical assertions alone
cannot certify the behavior of an LLM using a skill.
"""

import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import struct
import subprocess
import sys
from typing import Any

import pytest

from scripts.c5_skills_ontology.build_skill_library import build


ROOT = Path(__file__).absolute().parents[1]
SOURCE = ROOT / "tools/skill_library/workspace"
KERNEL = "c5-ring0-babylon-kernel-project/references/modules"
SHARED = f"{KERNEL}/shared-manifest-kernel/MODULE.md"


def block(path: Path, language: str) -> str:
    matches = re.findall(rf"```{language}\n(.*?)\n```", path.read_text(), re.S)
    assert len(matches) == 1, (path, language, len(matches))
    result = matches[0]
    assert isinstance(result, str)
    return result


def make_reference_project(destination: Path, library: Path = SOURCE) -> Path:
    """No dependencies; never touches the workspace Cargo.toml or lockfile."""
    (destination / "src").mkdir(parents=True)
    (destination / "tests").mkdir()
    rust = block(library / SHARED, "rust")
    regression = (ROOT / "tests/fixtures/project_skills_shared_manifest_tests.rs").read_text()
    (destination / "src/lib.rs").write_text(rust + "\n" + regression)
    # The audit's deterministic interleaving, inserted before the actual final CAS.
    commit = "self.status_flag.compare_exchange(WRITING, RUNNING, Ordering::SeqCst, Ordering::SeqCst).is_ok()"
    assert rust.count(commit) == 1
    injected = rust.replace(commit, "self.epistemic_halt();\n        " + commit)
    (destination / "tests/halt_at_commit.rs").write_text(
        injected
        + """
#[test]
fn halt_at_the_commit_boundary_wins() {
    let m = SharedManifest::new();
    assert!(!m.publish(3, &[3; 4]));
    assert!(m.is_halted());
    assert_eq!(m.read(), Err(ReadError::Halted));
    assert!(!m.publish(4, &[4; 4]));
}
"""
    )
    (destination / "Cargo.toml").write_text(
        '[package]\nname = "skill-reference-check"\nversion = "0.0.0"\nedition = "2021"\n'
    )
    (destination / "Cargo.lock").write_text(
        'version = 4\n\n[[package]]\nname = "skill-reference-check"\nversion = "0.0.0"\n'
    )
    return destination / "Cargo.toml"


@pytest.fixture(scope="module")
def library(tmp_path_factory):
    destination = tmp_path_factory.mktemp("skills-relocated") / "project & spaces"
    build(destination, "workspace")
    return destination


def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=120, **kwargs)


def test_rust_examples_compile_and_satisfy_state_and_concurrency_contracts(library, tmp_path):
    manifest = make_reference_project(tmp_path / "reference", library)
    result = run(["cargo", "test", "--locked", "--offline", "--manifest-path", str(manifest)])
    assert result.returncode == 0, result.stdout + result.stderr


def test_cpp17_example_compiles_and_preserves_fifo(library, tmp_path):
    compiler = shutil.which("clang++") or shutil.which("g++")
    assert compiler, "C++17 compiler required to validate the published example"
    source = tmp_path / "spsc.cpp"
    source.write_text(
        block(library / SHARED, "cpp")
        + """
int main() {
    SPSCRingBuffer<int, 4> queue;
    int value = -1;
    for (int round = 0; round < 100; ++round) {
        assert(!queue.pop(value));
        for (int i = 0; i < 4; ++i) assert(queue.push(round * 4 + i));
        assert(!queue.push(-1));
        for (int i = 0; i < 4; ++i) {
            assert(queue.pop(value));
            assert(value == round * 4 + i);
        }
    }
    assert(!queue.pop(value));
}
"""
    )
    binary = tmp_path / "spsc"
    result = run([compiler, "-std=c++17", "-pedantic-errors", str(source), "-o", str(binary)])
    assert result.returncode == 0, result.stdout + result.stderr
    assert run([str(binary)]).returncode == 0


@pytest.mark.parametrize(
    "status,seq,expected", [(1, 2, (7, [7] * 4)), (1, 3, None), (2, 2, None), (0xDEAD6060, 2, None)]
)
def test_python_snapshot_uses_read_only_bytes_and_closes_mapping(library, tmp_path, status, seq, expected):
    namespace: dict[str, Any] = {}
    exec(compile(block(library / SHARED, "python"), str(library / SHARED), "exec"), namespace)
    snapshot = tmp_path / "snapshot.bin"
    data = struct.pack("<IIQ4Q16x", status, seq, 7, *([7] * 4))
    snapshot.write_bytes(data)
    snapshot.chmod(0o444)
    for _ in range(3):
        assert namespace["read_shared_manifest_snapshot"](snapshot) == expected
    assert snapshot.read_bytes() == data
    # Windows refuses this if the mapping or descriptor is still retained.
    snapshot.chmod(0o644)
    snapshot.unlink()


@pytest.mark.parametrize("length", [0, 63, 65])
def test_python_snapshot_rejects_incomplete_or_trailing_data(library, tmp_path, length):
    namespace: dict[str, Any] = {}
    exec(compile(block(library / SHARED, "python"), str(library / SHARED), "exec"), namespace)
    snapshot = tmp_path / "invalid.bin"
    snapshot.write_bytes(bytes(length))
    with pytest.raises(ValueError):
        namespace["read_shared_manifest_snapshot"](snapshot)


@pytest.mark.parametrize(
    "relative",
    [
        "c5-anti-slop-ui/scripts/audit_ui_slop.py",
        "c5-audiovisual-acreativo-sota-project/references/modules/c5-anti-slop-ui/scripts/audit_ui_slop.py",
    ],
)
@pytest.mark.parametrize(
    "html",
    [
        '<p style="color:#fff;background:#fff">Invisible</p>',
        "<button></button>",
    ],
)
def test_ui_counterexamples_are_not_certified(library, tmp_path, relative, html):
    source = tmp_path / "counterexample.html"
    source.write_text(html)
    result = run([sys.executable, str(library / relative), str(source), "--json"])
    assert result.returncode == 0  # No lexical findings; explicitly not a WCAG pass.
    report = json.loads(result.stdout)
    assert report["conformance"] == "not_verified"
    assert {"rendered_contrast", "accessible_names"} <= set(report["unverified"])
    assert report["files_scanned"] == 1
    assert report["scope"] == "lexical_patterns_only"
    human = run([sys.executable, str(library / relative), str(source)])
    assert "NO_VERIFICADO" in human.stdout
    assert "cumple con" not in human.stdout


def test_linter_scans_source_directories_and_reports_empty_scope(library, tmp_path):
    directory = tmp_path / "distributed-ui"
    directory.mkdir()
    (directory / "bad.html").write_text('<p class="text-zinc-600">Text</p>')
    ignored = directory / "dist"
    ignored.mkdir()
    (ignored / "bad.html").write_text('<p class="text-zinc-600">Text</p>')
    linter = library / "c5-anti-slop-ui/scripts/audit_ui_slop.py"
    result = run([sys.executable, str(linter), str(directory), "--json"])
    assert result.returncode == 1
    assert json.loads(result.stdout)["files_scanned"] == 1
    empty = tmp_path / "empty"
    empty.mkdir()
    result = run([sys.executable, str(linter), str(empty), "--json"])
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "no_files"


def test_launch_agent_paths_survive_relocation_and_xml_characters(library, tmp_path):
    module = library / f"{KERNEL}/c5-sovereign-daemon-deployment/MODULE.md"
    namespace: dict[str, Any] = {}
    exec(compile(block(module, "python"), str(module), "exec"), namespace)
    project = tmp_path / "Proyecto & prueba"
    project.mkdir()
    binary = project / "daemon inerte"
    binary.write_bytes(b"")
    logs = project / "logs"
    logs.mkdir()
    before = sorted(project.rglob("*"))
    blob = namespace["render_launch_agent"](str(project), str(binary), str(logs))
    plist = plistlib.loads(blob)
    assert plist["WorkingDirectory"] == str(project)
    assert plist["ProgramArguments"] == [str(binary)]
    assert plist["StandardOutPath"] == str(logs / "daemon_stdout.log")
    assert plist["RunAtLoad"] is False and plist["KeepAlive"] is False
    assert sorted(project.rglob("*")) == before
    with pytest.raises(ValueError):
        namespace["render_launch_agent"]("relative-root", str(binary), str(logs))
    with pytest.raises(ValueError):
        namespace["render_launch_agent"](str(project), str(project / "missing"), str(logs))


def test_documented_grill_alias_routes_through_both_entrypoints(library):
    hub = library / "c5-epistemic-thermodynamics-project/scripts/route.py"
    for command in ([str(hub)], [str(library / "_skill_router.py"), "--library-root", str(library)]):
        result = run([sys.executable, *command, "--query", "/grill-me"])
        assert result.returncode == 0, result.stdout + result.stderr
        assert [entry["name"] for entry in json.loads(result.stdout)] == ["grill-me-v2"]


def test_legacy_launcher_resolves_in_another_checkout(tmp_path):
    relative = Path("tools/skills/babylon60-kernel-invariants/SKILL.md")
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / relative, target)
    distribution = tmp_path / ".agents/skills"
    build(distribution, "workspace")
    links = re.findall(r"\]\(([^)]+)\)", target.read_text())
    assert links and all(not os.path.isabs(link) for link in links)
    assert all((target.parent / link).is_file() for link in links)
