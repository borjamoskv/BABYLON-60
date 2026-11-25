"""Declared limit L2: a hardlink of a protected file inside a grant keeps a session from starting.

Every link is a real hardlink on the test filesystem and every home is a
throwaway directory holding a canary. Nothing is mocked: the tests about the
bound lower ``_Guard.LINK_SEARCH_LIMIT`` so that a few real files exceed it.
The ``run`` tests go through the real argument parser and, where a backend
exists, a real confined process.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from babylon60.confine import aliases
from babylon60.confine import policy as pol
from babylon60.confine.launcher import landlock_abi
from babylon60.confine.policy import MIN_LANDLOCK_ABI, PolicyError, build_policy

ROOT = Path(__file__).absolute().parents[1]
BACKEND = (sys.platform.startswith("linux") and landlock_abi() >= MIN_LANDLOCK_ABI) or sys.platform == "darwin"
needs_backend = pytest.mark.skipif(
    not BACKEND and os.environ.get("BABYLON60_REQUIRE_LANDLOCK") != "1", reason="no confinement backend on this machine"
)
CANARY = "B60-CANARY-hardlink"
REFUSAL = "Refusing to start: the agent could read a protected file through a hard link (declared limit L2): "
ADVICE = ". Remove the link (a copy is not a link), or pass --accept-hardlinks to start anyway"


@pytest.fixture
def layout(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    ssh = home / ".ssh"
    ssh.mkdir(parents=True)
    key = ssh / "id_rsa"
    key.write_text(f"{CANARY}\n")
    ws = tmp_path / "ws"
    (ws / "src" / "deep").mkdir(parents=True)
    (ws / "README.md").write_text("project\n")
    other = tmp_path / "other"
    other.mkdir()
    return {"root": tmp_path, "home": home, "ssh": ssh, "key": key, "ws": ws, "other": other}


def _build(layout: dict[str, Path], **kwargs: Any) -> pol.Policy:
    kwargs.setdefault("homes", [str(layout["home"])])
    kwargs.setdefault("system", False)
    return build_policy(layout["ws"], **kwargs)


def _found(link: Path, protected: Path) -> str:
    return f"{link} is a hard link to protected {protected}"


def _l2(path: Path, links: int) -> str:
    return f"{path} has {links} links; another path to it may be readable (declared limit L2)"


# The policy ----------------------------------------------------------------------------------


def test_a_workspace_without_hardlinks_builds_without_warnings(layout: dict[str, Path]) -> None:
    os.link(layout["ws"] / "README.md", layout["ws"] / "src" / "README.link")  # a link of an ordinary file
    os.link(layout["key"], layout["ssh"] / "id_rsa.bak")  # every name of the key is protected
    policy = _build(layout, read=[str(layout["other"])])
    assert policy.warnings == ()
    assert {g.path for g in policy.grants} == {str(layout["ws"]), str(layout["other"])}


@pytest.mark.parametrize("where", ["", "src", "src/deep"])
def test_a_hardlink_of_a_protected_key_in_the_workspace_refuses_to_start(layout: dict[str, Path], where: str) -> None:
    link = layout["ws"] / where / "notes-prelinked.txt"
    os.link(layout["key"], link)
    with pytest.raises(PolicyError) as refused:
        _build(layout)
    assert str(refused.value) == REFUSAL + _found(link, layout["key"]) + ADVICE


@pytest.mark.parametrize("option", ["read", "write", "private_tmp", "runtime"])
def test_a_hardlink_inside_any_granted_directory_refuses_to_start(layout: dict[str, Path], option: str) -> None:
    link = layout["other"] / "cache" / "blob"
    link.parent.mkdir()
    os.link(layout["key"], link)
    grant: Any = str(layout["other"]) if option == "private_tmp" else [str(layout["other"])]
    with pytest.raises(PolicyError) as refused:
        _build(layout, **{option: grant})
    assert str(refused.value) == REFUSAL + _found(link, layout["key"]) + ADVICE


def test_hardlinks_of_nested_entries_and_of_protected_files_are_all_named(layout: dict[str, Path]) -> None:
    nested = layout["ssh"] / "deploy" / "ci"
    nested.mkdir(parents=True)
    (nested / "id_ed25519").write_text(f"{CANARY}-nested\n")
    netrc = layout["home"] / ".netrc"
    netrc.write_text(f"machine example login agent password {CANARY}\n")
    first, second, third = layout["ws"] / "a", layout["ws"] / "src" / "b", layout["ws"] / "src" / "c"
    os.link(nested / "id_ed25519", first)
    os.link(netrc, second)
    os.link(netrc, third)
    with pytest.raises(PolicyError) as refused:
        _build(layout)
    reasons = [_found(first, nested / "id_ed25519"), _found(second, netrc), _found(third, netrc)]
    assert str(refused.value) == REFUSAL + "; ".join(reasons) + ADVICE


def test_a_hardlink_outside_every_grant_only_warns(layout: dict[str, Path]) -> None:
    os.link(layout["key"], layout["other"] / "copy")
    policy = _build(layout)
    assert policy.warnings == (_l2(layout["key"], 2),)
    assert [g.path for g in policy.grants] == [str(layout["ws"])]


def test_a_hardlink_reached_only_through_a_symbolic_link_is_outside_the_grants(layout: dict[str, Path]) -> None:
    os.link(layout["key"], layout["other"] / "copy")
    (layout["ws"] / "elsewhere").symlink_to(layout["other"])  # the sandbox does not grant what a link points to
    assert _build(layout).warnings == (_l2(layout["key"], 2),)


def test_a_found_link_refuses_while_another_outside_the_grants_would_only_warn(layout: dict[str, Path]) -> None:
    link = layout["ws"] / "inside"
    os.link(layout["key"], link)
    os.link(layout["key"], layout["other"] / "outside")
    with pytest.raises(PolicyError) as refused:
        _build(layout)
    assert str(refused.value) == REFUSAL + _found(link, layout["key"]) + ADVICE
    accepted = _build(layout, accept_hardlinks=True)
    assert accepted.warnings == (
        _l2(layout["key"], 3),
        f"{_found(link, layout['key'])}: risk accepted (declared limit L2)",
    )


def test_accepting_the_risk_builds_the_policy_and_names_the_link(layout: dict[str, Path]) -> None:
    link = layout["ws"] / "notes-prelinked.txt"
    os.link(layout["key"], link)
    policy = _build(layout, accept_hardlinks=True)
    assert policy.warnings == (f"{_found(link, layout['key'])}: risk accepted (declared limit L2)",)
    assert policy.digest() == _build_without(layout, link).digest()  # the flag changes no grant


def _build_without(layout: dict[str, Path], link: Path) -> pol.Policy:
    link.unlink()
    return _build(layout)


def test_a_search_cut_by_the_bound_refuses_to_start(layout: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    os.link(layout["key"], layout["other"] / "copy")  # not in the workspace, but the search cannot tell
    for index in range(40):
        (layout["ws"] / "src" / f"f{index}").write_text("x")
    monkeypatch.setattr(pol._Guard, "LINK_SEARCH_LIMIT", 20)
    with pytest.raises(PolicyError) as refused:
        _build(layout)
    assert str(refused.value) == (
        f"{REFUSAL}{layout['key']} has 2 links and the search for them inside the grants did not finish: "
        f"the search of {layout['ws']} stopped at 20 entries{ADVICE}"
    )
    accepted = _build(layout, accept_hardlinks=True)
    assert accepted.warnings[0] == _l2(layout["key"], 2)
    assert len(accepted.warnings) == 2 and accepted.warnings[1].endswith(
        "stopped at 20 entries: risk accepted (declared limit L2)"
    )


def test_the_bound_is_shared_by_all_the_grants_and_the_workspace_goes_first(
    layout: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    link = layout["ws"] / "notes-prelinked.txt"
    os.link(layout["key"], link)
    for index in range(40):
        (layout["other"] / f"f{index}").write_text("x")
    monkeypatch.setattr(pol._Guard, "LINK_SEARCH_LIMIT", 10)
    # Found in the workspace: every name is accounted for, so the rest is not searched and nothing is unfinished.
    with pytest.raises(PolicyError) as refused:
        _build(layout, read=[str(layout["other"])])
    assert str(refused.value) == REFUSAL + _found(link, layout["key"]) + ADVICE
    link.unlink()
    os.link(layout["key"], layout["root"] / "far")
    with pytest.raises(PolicyError, match="did not finish: the search of .*/other stopped at"):
        _build(layout, read=[str(layout["other"])])


def test_a_search_cut_inside_a_read_only_install_prefix_only_warns(
    layout: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An interpreter prefix alone can exceed the bound: it is searched last and never refuses unfinished."""
    prefix = layout["root"] / "prefix"
    (prefix / "lib").mkdir(parents=True)
    for index in range(40):
        (prefix / "lib" / f"m{index}.py").write_text("x")
    os.link(layout["key"], layout["root"] / "far")
    monkeypatch.setattr(pol._Guard, "LINK_SEARCH_LIMIT", 20)
    policy = _build(layout, runtime=[str(prefix)])
    assert policy.warnings == (
        "the search for hard links of protected files did not finish in the read-only install prefixes "
        f"(the search of {prefix} stopped at 17 entries); one there would be readable (declared limit L2)",
        _l2(layout["key"], 2),
    )
    os.link(layout["key"], prefix / "found")  # listed with the prefix's own entries, before the bound
    with pytest.raises(PolicyError) as refused:
        _build(layout, runtime=[str(prefix)])
    assert str(refused.value) == REFUSAL + _found(prefix / "found", layout["key"]) + ADVICE


def test_the_bound_never_matters_without_a_link_outside_the_protected_paths(
    layout: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    for index in range(40):
        (layout["ws"] / f"f{index}").write_text("x")
    monkeypatch.setattr(pol._Guard, "LINK_SEARCH_LIMIT", 1)
    assert _build(layout).warnings == ()


@pytest.mark.skipif(os.geteuid() == 0, reason="root lists directories whatever their mode")
def test_an_unlistable_directory_in_the_workspace_refuses_while_a_link_is_unaccounted(layout: dict[str, Path]) -> None:
    locked = layout["ws"] / "locked"
    locked.mkdir()
    locked.chmod(0o300)
    try:
        assert _build(layout).warnings == ()  # no link to look for: nothing is searched
        os.link(layout["key"], layout["other"] / "copy")
        with pytest.raises(PolicyError, match=r"did not finish: 1 directories below .*/ws could not be listed"):
            _build(layout)
    finally:
        locked.chmod(0o700)


def test_scan_for_given_files_records_only_their_names(layout: dict[str, Path]) -> None:
    link = layout["ws"] / "src" / "deep" / "link"
    os.link(layout["key"], link)
    os.link(layout["ws"] / "README.md", layout["ws"] / "README.link")
    st = os.stat(layout["key"])
    scan = aliases.scan_tree(str(layout["ws"]), only={(st.st_dev, st.st_ino)})
    assert [(item.path, item.ident, item.nlink) for item in scan.linked] == [(str(link), (st.st_dev, st.st_ino), 2)]
    assert scan.entries == {} and scan.listed == 5 and not scan.stopped
    everything = aliases.scan_tree(str(layout["ws"]))
    assert len(everything.linked) == 3 and len(everything.entries) == 4


# ``babylon60 run`` ---------------------------------------------------------------------------


@pytest.fixture
def sandbox(layout: dict[str, Path]) -> dict[str, Path]:
    return {**layout, "journal": layout["root"] / "state" / "journal.db"}


def _run(sandbox: dict[str, Path], *command: str, options: tuple[str, ...] = ()) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HOME": str(sandbox["home"]), "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}
    argv = ["run", "--allow-root", "--journal", str(sandbox["journal"]), *options, "--", *command]
    return subprocess.run(
        [sys.executable, "-P", "-m", "babylon60.cli.main_dispatcher", *argv],
        env=env,
        cwd=str(sandbox["ws"]),
        capture_output=True,
        text=True,
        timeout=300,
    )


def _kinds(sandbox: dict[str, Path]) -> list[str]:
    env = {**os.environ, "HOME": str(sandbox["home"]), "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}
    log = subprocess.run(
        [
            sys.executable,
            "-P",
            "-m",
            "babylon60.cli.main_dispatcher",
            "log",
            "--journal",
            str(sandbox["journal"]),
            "--json",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return [entry["kind"] for entry in json.loads(log.stdout)["entries"]]


@needs_backend
def test_run_refuses_to_start_and_names_the_link(sandbox: dict[str, Path]) -> None:
    link = sandbox["ws"] / "notes-prelinked.txt"
    os.link(sandbox["key"], link)
    result = _run(sandbox, "sh", "-c", "cat notes-prelinked.txt; touch started")
    assert result.returncode == 3 and result.stdout == ""
    assert f"babylon60 run: {REFUSAL}{_found(link, sandbox['key'])}{ADVICE}" in result.stderr
    assert not (sandbox["ws"] / "started").exists()
    assert _kinds(sandbox) == []  # no session: nothing started, nothing journaled as a run


@needs_backend
def test_run_dry_run_refuses_too(sandbox: dict[str, Path]) -> None:
    os.link(sandbox["key"], sandbox["ws"] / "src" / "alias")
    result = _run(sandbox, "true", options=("--dry-run",))
    assert result.returncode == 3 and result.stdout == ""
    assert f"{sandbox['ws'] / 'src' / 'alias'} is a hard link to protected {sandbox['key']}" in result.stderr


@needs_backend
def test_run_starts_as_before_without_hardlinks(sandbox: dict[str, Path]) -> None:
    result = _run(sandbox, "cat", "README.md")
    assert result.returncode == 0 and result.stdout == "project\n", result.stderr
    assert "hard link" not in result.stderr and "L2" not in result.stderr
    assert _kinds(sandbox) == ["run_start", "run_end"]


@needs_backend
def test_run_with_the_risk_accepted_starts_and_the_link_is_readable(sandbox: dict[str, Path]) -> None:
    """What the refusal prevents: once a session starts, neither Landlock nor Seatbelt denies the second name."""
    link = sandbox["ws"] / "notes-prelinked.txt"
    os.link(sandbox["key"], link)
    result = _run(sandbox, "cat", "notes-prelinked.txt", options=("--accept-hardlinks",))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{CANARY}\n"
    assert f"babylon60 run: warning: {_found(link, sandbox['key'])}: risk accepted (declared limit L2)" in result.stderr
    assert _kinds(sandbox) == ["run_start", "run_end"]


@needs_backend
def test_run_prints_the_name_of_a_link_without_its_control_characters(sandbox: dict[str, Path]) -> None:
    link = sandbox["ws"] / "evil\x1b[2Jname"
    os.link(sandbox["key"], link)
    result = _run(sandbox, "true")
    assert result.returncode == 3 and "\x1b" not in result.stderr
    assert "is a hard link to protected" in result.stderr
