"""Confinement policy guards, Landlock masks per ABI and Seatbelt rendering."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from babylon60.confine import policy as pol
from babylon60.confine.policy import PolicyError, build_policy
from babylon60.confine.seatbelt import render_profile


@pytest.fixture
def layout(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_rsa").write_text("canary")
    (home / ".config" / "gh").mkdir(parents=True)
    (home / "project").mkdir()
    state = tmp_path / "launcher-state"
    state.mkdir()
    return {"root": tmp_path, "home": home, "ws": home / "project", "state": state}


def _build(layout: dict[str, Path], **kwargs: object) -> pol.Policy:
    kwargs.setdefault("homes", [str(layout["home"])])
    kwargs.setdefault("system", False)
    return build_policy(kwargs.pop("workspace", layout["ws"]), **kwargs)  # type: ignore[arg-type]


def test_workspace_inside_home_is_accepted(layout: dict[str, Path]) -> None:
    policy = _build(layout)
    assert [g.path for g in policy.grants] == [str(layout["ws"])]
    assert policy.grants[0].access == "rw"


@pytest.mark.parametrize("target", ["home", "root"])
def test_home_and_its_ancestors_are_refused(layout: dict[str, Path], target: str) -> None:
    with pytest.raises(PolicyError, match="home directory"):
        _build(layout, workspace=layout[target])


def test_grant_inside_protected_set_is_refused(layout: dict[str, Path]) -> None:
    with pytest.raises(PolicyError, match="inside protected"):
        _build(layout, read=[str(layout["home"] / ".ssh" / "id_rsa")])


def test_grant_containing_protected_set_is_refused(layout: dict[str, Path]) -> None:
    with pytest.raises(PolicyError, match="contains protected"):
        _build(layout, read=[str(layout["home"] / ".config")])


def test_symlink_grant_is_refused(layout: dict[str, Path]) -> None:
    link = layout["ws"] / "keys"
    link.symlink_to(layout["home"] / ".ssh")
    with pytest.raises(PolicyError, match="symbolic link"):
        _build(layout, read=[str(link)])


def test_physical_identity_defeats_symlinked_parents(layout: dict[str, Path]) -> None:
    alias = layout["root"] / "alias"
    alias.symlink_to(layout["home"])
    with pytest.raises(PolicyError, match="inside protected"):
        _build(layout, read=[str(alias / ".ssh" / "id_rsa")])


def test_missing_user_grant_is_refused(layout: dict[str, Path]) -> None:
    with pytest.raises(PolicyError, match="does not exist"):
        _build(layout, read=[str(layout["root"] / "missing")])


def test_write_over_launcher_state_is_refused_but_read_is_allowed(layout: dict[str, Path]) -> None:
    journal = layout["state"] / "journal.db"
    journal.write_text("")
    with pytest.raises(PolicyError, match="launcher's own state"):
        _build(layout, write=[str(layout["state"])], self_paths=[str(journal)])
    policy = _build(layout, read=[str(layout["state"])], self_paths=[str(journal)])
    assert any(g.path == str(layout["state"]) and g.access == "ro" for g in policy.grants)


def test_tmp_is_not_granted_when_it_contains_a_home(layout: dict[str, Path]) -> None:
    home_under_tmp = Path("/tmp") / f"confine-home-{os.getpid()}"
    home_under_tmp.mkdir(exist_ok=True)
    try:
        policy = build_policy(layout["ws"], homes=[str(home_under_tmp)], system=True)
        assert "/tmp" not in {g.path for g in policy.grants}
    finally:
        home_under_tmp.rmdir()


def test_system_grants_skip_symlinks_without_failing(layout: dict[str, Path]) -> None:
    policy = build_policy(layout["ws"], homes=[str(layout["home"])], system=True)
    assert "/usr" in {g.path for g in policy.grants}
    for path in ("/bin", "/lib"):
        if os.path.islink(path):
            assert path in policy.skipped


def test_masks_follow_the_abi(layout: dict[str, Path]) -> None:
    (layout["ws"] / "file.txt").write_text("x")
    policy = _build(layout, read=[str(layout["ws"] / "file.txt")])
    handled1, scoped1, rules1 = policy.landlock_rules(1)
    assert handled1 == (1 << 13) - 1 and scoped1 == 0
    handled3, _, _ = policy.landlock_rules(3)
    assert handled3 & pol.TRUNCATE and handled3 & pol.REFER and not handled3 & pol.IOCTL_DEV
    handled7, scoped7, rules7 = policy.landlock_rules(7)
    assert handled7 & pol.IOCTL_DEV and scoped7 == 3
    workspace_rule = next(r for r in rules7 if r["path"] == str(layout["ws"]))
    assert not workspace_rule["access"] & (pol.MAKE_CHAR | pol.MAKE_BLOCK)
    file_rule = next(r for r in rules7 if r["path"].endswith("file.txt"))
    assert file_rule["access"] & ~pol.FILE_RIGHTS == 0
    assert all(rule["access"] & ~handled1 == 0 for rule in rules1)


def test_digest_ignores_inode_numbers(layout: dict[str, Path]) -> None:
    first = _build(layout).digest()
    layout["ws"].rmdir()
    layout["ws"].mkdir()
    assert _build(layout).digest() == first


def test_unknown_preset_is_refused(layout: dict[str, Path]) -> None:
    with pytest.raises(PolicyError, match="Unknown preset"):
        _build(layout, preset="nope")


def test_preset_paths_are_granted_when_present(layout: dict[str, Path]) -> None:
    (layout["home"] / ".codex").mkdir()
    policy = _build(layout, preset="codex")
    codex = next(g for g in policy.grants if g.path == str(layout["home"] / ".codex"))
    assert codex.access == "rw" and codex.origin == "preset:codex"


def test_seatbelt_profile_orders_denies_around_grants(layout: dict[str, Path]) -> None:
    alias = layout["root"] / "home-alias"
    alias.symlink_to(layout["home"])
    policy = _build(layout, workspace=alias / "project")
    profile = render_profile(policy)
    lines = profile.splitlines()
    assert lines[:2] == ["(version 1)", "(allow default)"]
    assert lines[2].startswith('(deny file-read* file-write* (subpath "/Users")')
    assert f'(subpath "{layout["home"]}")' in lines[2]
    assert lines[-1].startswith("(deny file-read* file-write*") and ".ssh" in lines[-1]
    workspace_rule = next(line for line in lines if line.startswith("(allow file-read* file-write*"))
    assert f'"{alias / "project"}"' in workspace_rule and f'"{layout["ws"]}"' in workspace_rule
    assert any(line.startswith("(allow file-read-metadata") for line in lines)


def test_seatbelt_escapes_quotes(layout: dict[str, Path]) -> None:
    odd = layout["ws"] / 'quo"te'
    odd.mkdir()
    profile = render_profile(_build(layout, read=[str(odd)]))
    assert '"' + str(odd).replace('"', '\\"') + '"' in profile


def test_stat_ancestry_matches_descriptor_ancestry(layout: dict[str, Path]) -> None:
    alias = layout["root"] / "alias"
    alias.symlink_to(layout["home"])
    for path in (layout["ws"], layout["home"] / ".ssh" / "id_rsa", alias / "project", Path("/"), Path("/dev/null")):
        assert pol._ancestry_by_stat(path) == pol.ancestry(path), path
    # ``..`` after a symbolic link is resolved by the kernel, never lexically, on both variants.
    (layout["home"] / "notes.txt").write_text("x")
    assert pol._ancestry_by_stat(f"{alias}/../home/notes.txt") == pol.ancestry(f"{alias}/../home/notes.txt")
    for missing in (f"{alias}/new/..", f"{alias}/new/../.."):
        for variant in (pol._ancestry_by_stat, pol.ancestry):
            with pytest.raises(FileNotFoundError):
                variant(missing)
