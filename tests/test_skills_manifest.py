"""A frozen inventory must detect changes across all active port resources."""

from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.c5_quality_gates.freeze_skills_manifest import inventory


def test_port_inventory_uses_relative_paths_and_all_resource_types(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for name, content in [
        ("SKILL.md", b"clean"),
        ("aliases.json", b"{}"),
        ("route.py", b"pass"),
        ("helper.sh", b"exit 0"),
        ("asset.bin", b"\x00\xff"),
    ]:
        (source / name).write_bytes(content)
    dest = tmp_path / "dest"
    shutil.copytree(source, dest)
    assert inventory(source) == inventory(dest)
    (dest / "aliases.json").write_text('{"changed":true}')
    assert inventory(source) != inventory(dest)


def test_link_target_contents_and_cycles_are_inventoried(tmp_path: Path) -> None:
    root = tmp_path / "root"
    external = tmp_path / "external"
    root.mkdir()
    external.mkdir()
    (external / "MODULE.md").write_text("clean")
    (root / "shared").symlink_to(external, target_is_directory=True)
    (external / "cycle").symlink_to(root, target_is_directory=True)
    before = inventory(root)
    (external / "MODULE.md").write_text("changed")
    assert inventory(root) != before


def test_missing_or_broken_tree_is_not_a_manifest(tmp_path: Path) -> None:
    root = tmp_path / "root"
    with pytest.raises(OSError):
        inventory(root)
    root.mkdir()
    with pytest.raises(OSError):
        inventory(root)
    (root / "broken").symlink_to(tmp_path / "missing")
    with pytest.raises(OSError):
        inventory(root)


def test_archives_and_generated_caches_are_explicitly_excluded(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    (root / "SKILL.md").write_text("clean")
    before = inventory(root)
    archive = root / "_archive"
    archive.mkdir()
    (archive / "SKILL.md").write_text("historical")
    assert inventory(root) == before
    assert "_archive" in before["excluded_names"]


def test_manifest_cli_rejects_tampering_and_never_overwrites(tmp_path: Path) -> None:
    script = Path(__file__).absolute().parents[1] / "scripts/c5_quality_gates/freeze_skills_manifest.py"
    root = tmp_path / "root"
    root.mkdir()
    (root / "SKILL.md").write_text("clean")
    manifest = tmp_path / "manifest.json"
    base = [sys.executable, str(script), "--root", str(root)]

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([*base, *args], capture_output=True, text=True, check=False)

    assert run("--output", str(manifest)).returncode == 0
    before = manifest.read_bytes()
    assert run("--verify", str(manifest)).returncode == 0
    assert run("--output", str(manifest)).returncode == 2
    assert manifest.read_bytes() == before
    (root / "SKILL.md").write_text("tampered")
    assert run("--verify", str(manifest)).returncode == 1
    assert run("--output", str(root / "manifest.json")).returncode == 2
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    assert run("--output", str(alias / "manifest.json")).returncode == 2
    assert not (root / "manifest.json").exists()


def test_subset_verification_preserves_existing_siblings_but_rejects_import_changes(tmp_path: Path) -> None:
    script = Path(__file__).absolute().parents[1] / "scripts/c5_quality_gates/freeze_skills_manifest.py"
    source, dest = tmp_path / "source", tmp_path / "dest"
    source.mkdir()
    (source / "new-skill").mkdir()
    (source / "new-skill/SKILL.md").write_text("audited")
    dest.mkdir(mode=0o700)
    (dest / "existing").mkdir()
    protected = dest / "existing/SKILL.md"
    protected.write_text("preserve this")
    shutil.copytree(source / "new-skill", dest / "new-skill")
    manifest = tmp_path / "manifest.json"
    made = subprocess.run(
        [sys.executable, str(script), "--root", str(source), "--output", str(manifest)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert made.returncode == 0
    command = [sys.executable, str(script), "--root", str(dest), "--verify", str(manifest), "--subset"]
    checked = subprocess.run(command, capture_output=True, text=True, check=False)
    assert checked.returncode == 0, checked.stderr
    assert protected.read_text() == "preserve this"
    (dest / "new-skill/unexpected.json").write_text("{}")
    changed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert changed.returncode == 1
    assert protected.read_text() == "preserve this"
