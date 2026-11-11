"""Symbolic links on the way to the command: readable on macOS, never their directories."""

from __future__ import annotations

import os
from pathlib import Path

from babylon60.confine.cli import executable_links
from babylon60.confine.policy import build_policy
from babylon60.confine.seatbelt import render_profile


def _layout(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_rsa").write_text("decoy\n")
    versions = home / ".local" / "share" / "agent" / "versions"
    versions.mkdir(parents=True)
    binary = versions / "1.0"
    binary.write_text("#!/bin/sh\necho agent\n")
    binary.chmod(0o755)
    bindir = home / ".local" / "bin"
    bindir.mkdir(parents=True)
    ws = tmp_path / "ws"
    ws.mkdir()
    return {"home": home, "binary": binary, "bindir": bindir, "ws": ws}


def test_links_under_a_home_are_listed_in_order(tmp_path: Path) -> None:
    box = _layout(tmp_path)
    middle = box["home"] / ".local" / "share" / "agent" / "current"
    middle.symlink_to("versions/1.0")  # relative target
    entry = box["bindir"] / "agent"
    entry.symlink_to(middle)
    assert executable_links(str(entry), (str(box["home"]),)) == [str(entry), str(middle)]
    assert executable_links(str(box["binary"]), (str(box["home"]),)) == []


def test_links_outside_homes_are_not_listed(tmp_path: Path) -> None:
    box = _layout(tmp_path)
    outside = tmp_path / "opt" / "agent"
    outside.parent.mkdir()
    outside.symlink_to(box["binary"])
    assert executable_links(str(outside), (str(box["home"]),)) == []


def test_policy_keeps_links_and_refuses_ones_inside_protected_paths(tmp_path: Path) -> None:
    box = _layout(tmp_path)
    entry = box["bindir"] / "agent"
    entry.symlink_to(box["binary"])
    hidden = box["home"] / ".ssh" / "agent"
    hidden.symlink_to(box["binary"])
    policy = build_policy(
        box["ws"],
        homes=[str(box["home"])],
        runtime=[str(box["binary"])],
        links=[str(entry), str(hidden), str(box["binary"])],
        system=False,
    )
    assert policy.links == (str(entry),)
    assert f"{hidden}: Refusing a link inside protected path {box['home'] / '.ssh'}" in policy.skipped
    assert f"{box['binary']}: not a symbolic link" in policy.skipped
    assert policy.as_dict()["links"] == [str(entry)]
    # The link changes the policy: it is part of the portable digest.
    assert policy.digest() != build_policy(box["ws"], homes=[str(box["home"])], system=False).digest()


def test_seatbelt_allows_exactly_the_link_and_still_denies_the_protected_set(tmp_path: Path) -> None:
    box = _layout(tmp_path)
    entry = box["bindir"] / "agent"
    entry.symlink_to(box["binary"])
    policy = build_policy(
        box["ws"], homes=[str(box["home"])], runtime=[str(box["binary"])], links=[str(entry)], system=False
    )
    profile = render_profile(policy).splitlines()
    allow = next(
        i for i, line in enumerate(profile) if line.startswith("(allow file-read* (literal") and "agent" in line
    )
    assert f'(literal "{os.path.abspath(entry)}")' in profile[allow]
    assert f'"{box["bindir"]}"' not in profile[allow]  # the link, not its directory
    deny_home = next(i for i, line in enumerate(profile) if line.startswith("(deny file-read* file-write*"))
    protected = max(i for i, line in enumerate(profile) if line.startswith("(deny file-read* file-write* file-link"))
    assert deny_home < allow < protected
