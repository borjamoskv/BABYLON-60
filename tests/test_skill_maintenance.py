"""Real filesystem transactions; no host installation is touched by these tests."""

import json
import os
import shutil
from pathlib import Path
import pytest
from tools.skill_library.maintenance import maintain, restore, signature


def target(tmp_path, name):
    root = tmp_path / name
    root.mkdir()
    (root / ".system").mkdir()
    (root / ".system" / "owned-by-host").write_text("leave intact")
    (root / "foreign-skill").mkdir()
    (root / "foreign-skill" / "SKILL.md").write_text("foreign")
    (root / "cortex-skill-auditor").mkdir()
    (root / "cortex-skill-auditor" / "local-note").write_text("previous version")
    return root


def test_dry_run_does_not_change_installation(tmp_path):
    destination = target(tmp_path, "skills")
    before = signature(destination, [p.name for p in destination.iterdir()])
    report = maintain({"antigravity": destination}, tmp_path / "review")
    assert report["status"] == "pass"
    assert signature(destination, [p.name for p in destination.iterdir()]) == before


def test_apply_verifies_content_and_rollback_restores_previous_entries(tmp_path):
    destination = target(tmp_path, "skills")
    output = tmp_path / "release"
    report = maintain({"antigravity": destination}, output, apply=True)
    assert report["environments"]["antigravity"]["distribution"]["status"] == "pass"
    assert (destination / "foreign-skill/SKILL.md").read_text() == "foreign"
    assert (destination / ".system/owned-by-host").read_text() == "leave intact"
    assert not (destination / "cortex-skill-auditor/local-note").exists()
    receipt = json.loads((output / "receipt.json").read_text())
    restore(receipt, output / "receipt.json")
    assert (destination / "cortex-skill-auditor/local-note").read_text() == "previous version"
    assert not (destination / "_skill_router.py").exists()
    assert (destination / "foreign-skill/SKILL.md").read_text() == "foreign"
    assert json.loads((output / "receipt.json").read_text())["phase"] == "rolled-back"


def test_rollback_refuses_to_overwrite_later_user_changes(tmp_path):
    destination = target(tmp_path, "skills")
    output = tmp_path / "release"
    maintain({"antigravity": destination}, output, apply=True)
    entry = destination / "cortex-skill-auditor/SKILL.md"
    entry.write_text("user changed this after installation")
    receipt = json.loads((output / "receipt.json").read_text())
    with pytest.raises(OSError, match="entry changed"):
        restore(receipt, output / "receipt.json")
    assert entry.read_text() == "user changed this after installation"
    assert (Path(receipt["targets"][0]["backup"]) / "cortex-skill-auditor/local-note").read_text() == "previous version"


def test_second_environment_failure_rolls_back_first_environment(tmp_path, monkeypatch):
    first = target(tmp_path, "first")
    second = target(tmp_path, "second")
    output = tmp_path / "release"
    original = os.replace
    failed = False

    def fail_once(source, destination):
        nonlocal failed
        if (
            not failed
            and Path(destination).parent == second
            and Path(source).parent.name.startswith(".skills-release-")
        ):
            failed = True
            raise OSError("Injected write failure in second installation")
        return original(source, destination)

    monkeypatch.setattr(os, "replace", fail_once)
    with pytest.raises(OSError, match="Injected write failure"):
        maintain({"antigravity": first, "codex": second}, output, apply=True)
    assert failed
    for root in [first, second]:
        assert (root / "cortex-skill-auditor/local-note").read_text() == "previous version"
        assert not (root / "_skill_router.py").exists()
        assert (root / "foreign-skill/SKILL.md").read_text() == "foreign"
    assert json.loads((output / "receipt.json").read_text())["phase"] == "rolled-back"


def test_overlapping_targets_refused_before_changes(tmp_path):
    destination = target(tmp_path, "skills")
    child = destination / "nested"
    child.mkdir()
    with pytest.raises(ValueError, match="overlap"):
        maintain({"codex": destination, "antigravity": child}, tmp_path / "release", apply=True)
    assert (destination / "cortex-skill-auditor/local-note").read_text() == "previous version"


def test_output_inside_installation_is_refused_without_mutation(tmp_path: Path) -> None:
    destination = target(tmp_path, "skills")
    before = signature(destination, [p.name for p in destination.iterdir()])
    with pytest.raises(ValueError, match="overlap"):
        maintain({"antigravity": destination}, destination / "review")
    assert not (destination / "review").exists()
    assert signature(destination, [p.name for p in destination.iterdir()]) == before


def test_physical_target_aliases_are_rejected_before_staging(tmp_path: Path) -> None:
    destination = target(tmp_path, "skills")
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    output = tmp_path / "review"
    with pytest.raises(ValueError, match="overlap"):
        maintain({"antigravity": destination, "codex": alias / "skills"}, output, apply=True)
    assert not output.exists()
    assert (destination / "cortex-skill-auditor/local-note").read_text() == "previous version"


@pytest.mark.parametrize("change", ["delete", "edit"])
def test_rollback_preflights_all_entries_before_restoring_any(tmp_path: Path, change: str) -> None:
    destination = target(tmp_path, "skills")
    output = tmp_path / "release"
    maintain({"antigravity": destination}, output, apply=True)
    receipt = json.loads((output / "receipt.json").read_text())
    if change == "delete":
        shutil.rmtree(destination / "cortex-skill-auditor")
    else:
        (destination / "_skill_router.py").write_text("User changed this after installation")
    before = signature(destination, receipt["targets"][0]["names"])
    with pytest.raises(OSError, match="entry changed"):
        restore(receipt, output / "receipt.json")
    assert signature(destination, receipt["targets"][0]["names"]) == before
    assert (Path(receipt["targets"][0]["backup"]) / "cortex-skill-auditor/local-note").is_file()


def test_dry_run_receipt_cannot_rollback_an_unapplied_release(tmp_path: Path) -> None:
    destination = target(tmp_path, "skills")
    output = tmp_path / "release"
    maintain({"antigravity": destination}, output)
    receipt = json.loads((output / "receipt.json").read_text())
    before = signature(destination, [p.name for p in destination.iterdir()])
    with pytest.raises(OSError, match="no applied installation"):
        restore(receipt, output / "receipt.json")
    assert signature(destination, [p.name for p in destination.iterdir()]) == before


def test_rollback_verifies_backup_before_replacing_installed_entries(tmp_path: Path) -> None:
    destination = target(tmp_path, "skills")
    output = tmp_path / "release"
    maintain({"antigravity": destination}, output, apply=True)
    receipt = json.loads((output / "receipt.json").read_text())
    before = signature(destination, receipt["targets"][0]["names"])
    backup = Path(receipt["targets"][0]["backup"])
    (backup / "cortex-skill-auditor/local-note").write_text("Backup was changed")
    with pytest.raises(OSError, match="backup changed"):
        restore(receipt, output / "receipt.json")
    assert signature(destination, receipt["targets"][0]["names"]) == before


def test_rollback_rejects_unmanaged_names_from_modified_receipt(tmp_path: Path) -> None:
    destination = target(tmp_path, "skills")
    output = tmp_path / "release"
    maintain({"antigravity": destination}, output, apply=True)
    receipt = json.loads((output / "receipt.json").read_text())
    receipt["targets"][0]["names"].append(".system")
    with pytest.raises(OSError, match="invalid owned entry"):
        restore(receipt, output / "receipt.json")
    assert (destination / ".system/owned-by-host").read_text() == "leave intact"
