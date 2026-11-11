"""The git configuration a preset grants read-only (``gitconfig.py``), and what keeps a path out of it.

With a ``~/.gitconfig`` present, every git command inside ``babylon60 run`` used to die with
"unknown error occurred while reading the configuration files": no preset let git read the
user's configuration. Every preset now grants ``~/.gitconfig``,
``~/.config/git/{config,ignore,attributes}``, the files they include, the files they name
(``core.excludesFile``, ``core.attributesFile``, ``commit.template``) and the hooks directory,
read-only and one by one, after the policy guards, unless their content looks like a
credential. Symbolic links are followed unless the agent could change them.

Real files in throwaway homes, the real policy guards and, end to end, the real CLI and the real
launcher under real Landlock (Linux). Secrets are random canaries. Set BABYLON60_REQUIRE_LANDLOCK=1
to fail instead of skipping when Landlock is missing. What Seatbelt renders is checked statically
on every platform; the run itself on macOS only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import pwd
import secrets
import shutil
import subprocess
import sys
from typing import Any

import pytest

from babylon60.confine import gitconfig, launcher, seatbelt
from babylon60.confine.gitconfig import MAX_FILES, credential_findings
from babylon60.confine.persistence import MAX_INCLUDE_DEPTH, parse_git_config, parse_git_config_lines
from babylon60.confine.policy import MIN_LANDLOCK_ABI, PRESETS, Policy, account_home, build_policy

ROOT = Path(__file__).absolute().parents[1]
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
LINUX = sys.platform.startswith("linux")
LANDLOCK = LINUX and launcher.landlock_abi() >= MIN_LANDLOCK_ABI
needs_backend = pytest.mark.skipif(
    not (LANDLOCK or REQUIRED or sys.platform == "darwin"), reason="no confinement backend on this machine"
)
needs_landlock = pytest.mark.skipif(
    not LINUX or not (LANDLOCK or REQUIRED), reason="Landlock only; BABYLON60_REQUIRE_LANDLOCK=1 fails instead"
)
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
USER = "[user]\n\tname = Decoy User\n\temail = decoy@example.invalid\n"  # lines 1-3 of most configs below
PROBE = "git init -q && git commit -q --allow-empty -m probe && git log -1 --format=%an"
UNREADABLE = "unknown error occurred while reading the configuration files"
HOOKS_EFFECT = "git inside cannot run the hooks there (git commit fails when a pre-commit hook must run)"
BOM = "﻿"


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _real(path: Path) -> str:
    """Git grants name real directories (``/var`` is ``/private/var`` on macOS) and keep the file name."""
    return os.path.join(os.path.realpath(path.parent), path.name)


def _canary() -> str:
    return "B60-CANARY-git-" + secrets.token_hex(8)


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    _write(home / ".ssh" / "id_rsa", "decoy key\n").chmod(0o600)
    (tmp_path / "ws").mkdir()
    return home


def _policy(home: Path, **kwargs: Any) -> Policy:
    kwargs.setdefault("git_env", {"HOME": str(home)})
    return build_policy(home.parent / "ws", homes=[str(home)], system=False, **kwargs)


def _git_grants(policy: Policy) -> dict[str, tuple[str, bool, str]]:
    return {g.path: (g.access, g.is_dir, g.origin) for g in policy.grants if g.origin.endswith(":git")}


def _credential_warnings(policy: Policy) -> list[str]:
    return [w for w in policy.warnings if w.startswith("git configuration not granted")]


def _long_file(home: Path) -> Path:
    """A file whose real path is a little longer than a Seatbelt string literal may be, and shorter
    than macOS's PATH_MAX (1024 bytes)."""
    total = seatbelt.MAX_STRING_BYTES + 5
    directory = os.path.realpath(home)
    while len(directory) + 101 + 60 < total:
        directory += "/" + "d" * 100
    path = Path(directory) / ("f" * (total - len(directory) - 1 - len(".inc")) + ".inc")
    return _write(path, "[core]\n\tpager = cat\n")


# --- what is granted ---------------------------------------------------------------------------


@pytest.mark.parametrize("preset", sorted(PRESETS))
def test_every_preset_grants_the_global_git_files_read_only(home: Path, preset: str) -> None:
    files = [
        _write(home / ".gitconfig", USER),
        _write(home / ".config" / "git" / "config", "[core]\n\tpager = cat\n"),
        _write(home / ".config" / "git" / "ignore", "*.tmp\n"),
        _write(home / ".config" / "git" / "attributes", "*.bin binary\n"),
    ]
    policy = _policy(home, preset=preset)
    assert _git_grants(policy) == {_real(path): ("ro", False, f"preset:{preset}:git") for path in files}
    assert not policy.warnings
    assert _git_grants(_policy(home)) == {}, "no preset, no git configuration"


def test_xdg_config_home_moves_the_git_directory(home: Path, tmp_path: Path) -> None:
    moved = _write(tmp_path / "xdg" / "git" / "config", USER)
    unused = _write(home / ".config" / "git" / "config", USER)
    environ = {"HOME": str(home), "XDG_CONFIG_HOME": str(tmp_path / "xdg")}
    granted = _git_grants(_policy(home, preset="codex", git_env=environ))
    assert _real(moved) in granted and _real(unused) not in granted


def test_includes_are_followed_as_git_resolves_them(home: Path, tmp_path: Path) -> None:
    included = [
        _write(home / ".config" / "git" / "identity.inc", USER),  # ~/ from the HOME git receives
        _write(home / "dotfiles" / "git" / "base.inc", "[include]\n\tpath = ../nested/deeper.inc\n"),  # relative
        _write(home / "dotfiles" / "nested" / "deeper.inc", "[core]\n\tpager = cat\n"),  # relative to base.inc
        _write(tmp_path / "shared" / "work.inc", "[core]\n\tautocrlf = input\n"),  # absolute, whatever the condition
    ]
    _write(
        home / ".gitconfig",
        "[include]\n\tpath = ~/.config/git/identity.inc\n\tpath = dotfiles/git/base.inc\n"
        f'[includeIf "gitdir:~/work/"]\n\tpath = {tmp_path / "shared" / "work.inc"}\n'
        "[include]\n\tpath = ~/missing.inc\n",
    )
    policy = _policy(home, preset="claude-code")
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig"), *(_real(path) for path in included)}
    assert _real(home / "missing.inc") in policy.skipped  # absent, skipped quietly like any preset path
    assert not policy.warnings


def test_an_include_if_without_a_condition_is_not_followed(home: Path) -> None:
    files = {name: _write(home / f"{name}.inc", "[core]\n\tpager = cat\n") for name in ("bare", "empty", "branch")}
    _write(
        home / ".gitconfig",
        USER + "[includeIf]\n\tpath = ~/bare.inc\n"
        '[includeIf ""]\n\tpath = ~/empty.inc\n'
        '[includeIf "onbranch:main"]\n\tpath = ~/branch.inc\n',
    )
    # git 2.43 never includes the first two: a name they set stays unset (measured).
    assert set(_git_grants(_policy(home, preset="codex"))) == {_real(home / ".gitconfig"), _real(files["branch"])}


def test_tilde_user_is_expanded_from_the_account_database(home: Path) -> None:
    account = pwd.getpwuid(os.getuid())
    name = f"b60-{secrets.token_hex(4)}.inc"  # never created: only the path git would open is checked
    _write(home / ".gitconfig", USER + f"[include]\n\tpath = ~{account.pw_name}/{name}\n")
    policy = _policy(home, preset="claude-code")
    assert os.path.join(os.path.realpath(account.pw_dir), name) in policy.skipped  # absent there
    assert not any(f"~{account.pw_name}" in entry for entry in policy.skipped), "never <dir>/~user/..."


def test_an_unknown_tilde_user_ends_the_file_where_git_dies(home: Path) -> None:
    missing = f"b60-no-such-user-{secrets.token_hex(4)}"
    before, after = (_write(home / f"{name}.inc", "[core]\n\tpager = cat\n") for name in ("before", "after"))
    # git expands an includeIf path only when its condition holds and commit.template only in git commit,
    # so it reads on; an include.path it cannot expand makes it die there (2.43: "could not expand include
    # path" and "bad config line").
    _write(
        home / ".gitconfig",
        USER + f'[includeIf "onbranch:main"]\n\tpath = ~{missing}/a.inc\n[commit]\n\ttemplate = ~{missing}/t\n'
        f"[include]\n\tpath = ~/before.inc\n\tpath = ~{missing}/x.inc\n\tpath = ~/after.inc\n",
    )
    policy = _policy(home, preset="codex")
    for value in (f"~{missing}/a.inc", f"~{missing}/t", f"~{missing}/x.inc"):
        assert f"{value}: no user {missing} in the account database, so git cannot expand it either" in policy.skipped
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig"), _real(before)}
    assert _real(after) not in _git_grants(policy)


def test_unexpandable_paths_are_named_up_to_the_bound(home: Path) -> None:
    token = secrets.token_hex(4)
    lines = "".join(
        f'[includeIf "onbranch:b{i}"]\n\tpath = ~b60-none-{i}-{token}/x.inc\n' for i in range(3 * MAX_FILES)
    )
    after = _write(home / "after.inc", "[core]\n\tpager = cat\n")
    _write(home / ".gitconfig", USER + lines + "[include]\n\tpath = ~/after.inc\n")
    policy = _policy(home, preset="claude-code")
    assert len([entry for entry in policy.skipped if "in the account database" in entry]) == MAX_FILES
    assert _real(after) in _git_grants(policy)


def test_includes_stop_at_the_depth_git_reads(home: Path) -> None:
    chain = [home / ".gitconfig", *(home / "chain" / f"{depth}.inc" for depth in range(1, MAX_INCLUDE_DEPTH + 2))]
    for current, following in zip(chain, chain[1:]):
        _write(current, f"[include]\n\tpath = {following}\n")
    _write(chain[-1], USER)
    granted = _git_grants(_policy(home, preset="codex"))
    # git reads depths 0 to 10 and dies including the eleventh ("exceeded maximum include depth").
    assert set(granted) == {_real(path) for path in chain[: MAX_INCLUDE_DEPTH + 1]}


def test_include_loops_end(home: Path) -> None:
    _write(home / ".gitconfig", USER + "[include]\n" + "\tpath = ~/.gitconfig\n" * 500 + "\tpath = ~/loop/b.inc\n")
    _write(home / "loop" / "b.inc", "[include]\n\tpath = ~/.gitconfig\n\tpath = b.inc\n")
    policy = _policy(home, preset="claude-code")
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig"), _real(home / "loop" / "b.inc")}
    assert not policy.warnings


def test_a_loop_through_ever_longer_spellings_ends_at_the_depth(home: Path) -> None:
    (home / "loop").mkdir()
    _write(home / ".gitconfig", USER + "[include]\n\tpath = loop/../.gitconfig\n")  # a new spelling at each depth
    policy = _policy(home, preset="codex")
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig")}
    assert not policy.warnings


def test_files_beyond_the_bound_are_named_not_granted(home: Path) -> None:
    names = [f"inc{index:03}.cfg" for index in range(MAX_FILES + 10)]
    for name in names:
        _write(home / "many" / name, "[core]\n\tpager = cat\n")
    _write(home / ".gitconfig", USER + "[include]\n" + "".join(f"\tpath = many/{name}\n" for name in names))
    policy = _policy(home, preset="codex")
    assert len(_git_grants(policy)) < MAX_FILES
    assert f"git configuration: more than {MAX_FILES} paths named through includes; the rest is not granted" in (
        policy.warnings
    )


def test_ordinary_settings_are_granted(home: Path) -> None:
    config = _write(
        home / ".gitconfig",
        USER + "[credential]\n\thelper = store\n\tusername = decoy\n"
        "[user]\n\tsigningkey = 0xDECAFBAD\n"
        "[http]\n\tproxy = http://proxy.example.invalid:3128\n\tsslVerify = true\n"
        '[remote "origin"]\n\turl = ssh://git@example.invalid/repo.git\n'
        '[url "git@github.com:"]\n\tinsteadOf = https://github.com/\n'
        '[url "ssh://git@example.invalid/"]\n\tpushInsteadOf = https://example.invalid/\n'
        "[core]\n\tsshCommand = ssh -i ~/.ssh/id_ed25519\n\texcludesFile = ~/.gitignore_global\n"
        '[includeIf "gitdir:~/work/"]\n\tpath = ~/.config/git/work.inc\n'
        "[alias]\n\tst = status\n",
    )
    policy = _policy(home, preset="claude-code")
    assert _real(config) in _git_grants(policy)
    assert not _credential_warnings(policy)


def test_files_the_configuration_names_are_granted_one_by_one(home: Path) -> None:
    named = [
        _write(home / ".gitignore_global", "*.tmp\n[Bb]in/\nsecrets\n"),  # patterns, not a section and a key
        _write(home / "dotfiles" / "attributes", "*.dat binary\n"),
        _write(home / ".gitmessage", "Decoy template subject\n"),
    ]
    relative = _write(home / "relative.ignore", "*.log\n")  # relative: git resolves it from the repository
    config = _write(
        home / ".gitconfig",
        USER + "[core]\n\texcludesFile = ~/.gitignore_global\n"
        f"\tattributesFile = {named[1]}\n\texcludesFile = relative.ignore\n"
        "[commit]\n\ttemplate = ~/.gitmessage\n",
    )
    policy = _policy(home, preset="claude-code")
    assert _git_grants(policy) == {_real(path): ("ro", False, "preset:claude-code:git") for path in [config, *named]}
    assert _real(relative) not in _git_grants(policy)
    assert not policy.warnings


def test_the_hooks_directory_is_granted_read_only(home: Path) -> None:
    hooks = home / ".githooks"
    _write(hooks / "pre-commit", "#!/bin/sh\nexit 0\n").chmod(0o755)
    _write(home / ".gitconfig", USER + "[core]\n\thooksPath = ~/.githooks\n")
    policy = _policy(home, preset="codex")
    assert _git_grants(policy) == {
        _real(home / ".gitconfig"): ("ro", False, "preset:codex:git"),
        os.path.realpath(hooks): ("ro", True, "preset:codex:git"),  # read and run, never written
    }
    assert not policy.warnings
    _write(home / ".gitconfig", USER + "[core]\n\thooksPath = .githooks\n")  # relative: the repository's own
    assert os.path.realpath(hooks) not in _git_grants(_policy(home, preset="codex"))


def test_ignore_and_attributes_files_are_patterns_not_git_config(home: Path) -> None:
    files = [
        _write(home / ".config" / "git" / "ignore", "[Dd]ebug/\n[Bb]in/\nsecrets\n*.log\n"),
        _write(home / ".config" / "git" / "attributes", "[Tt]okens/\npassword\n*.dat binary\n"),
    ]
    policy = _policy(home, preset="claude-code")
    assert set(_git_grants(policy)) == {_real(path) for path in files}
    assert not policy.warnings
    # Read as git config, the same lines would keep both out ("bb.secrets", "tt.password").
    assert all(credential_findings(path.read_bytes()) for path in files)


@pytest.mark.parametrize(
    ("rewrite", "granted"),
    [
        ('[url "git@github.com:"]\n\tinsteadOf = https://github.com/\n', True),
        ('[url "ssh://git@github.com/"]\n\tpushInsteadOf = https://github.com/\n', True),
        ('[url "https://ghp_{c}@github.com/"]\n\tinsteadOf = https://github.com/\n', False),
        ('[url "git@github.com:"]\n\tinsteadOf = https://x:{c}@github.com/\n', False),
    ],
)
def test_a_url_rewrite_is_kept_out_only_with_a_credential(home: Path, rewrite: str, granted: bool) -> None:
    canary = _canary()
    config = _write(home / ".gitconfig", USER + rewrite.replace("{c}", canary))
    policy = _policy(home, preset="codex")
    assert (_real(config) in _git_grants(policy)) is granted
    assert bool(_credential_warnings(policy)) is not granted
    assert canary not in json.dumps(policy.as_dict())


# --- what is not granted -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("snippet", "line", "key"),
    [
        ('[http "https://example.invalid/"]\n\textraHeader = Authorization: Bearer {c}\n', 5, "http.*.extraheader"),
        ("[http]\n\textraheader = AUTHORIZATION: basic {c}\n", 5, "http.extraheader"),
        ('[url "https://{c}@example.invalid/"]\n\tinsteadOf = https://example.invalid/\n', 5, "url.*.insteadof"),
        (
            '[url "ssh://deploy:{c}@example.invalid/"]\n\tpushInsteadOf = https://example.invalid/\n',
            5,
            "url.*.pushinsteadof",
        ),
        ('[url "git@example.invalid:"]\n\tinsteadOf = https://deploy:{c}@example.invalid/\n', 5, "url.*.insteadof"),
        ('[remote "origin"]\n\turl = https://deploy:{c}@example.invalid/repo.git\n', 5, "remote.*.url"),
        ("[http]\n\tproxy = http://{c}@proxy.example.invalid:3128\n", 5, "http.proxy"),
        ("[sendemail]\n\tsmtpPass = {c}\n", 5, "sendemail.smtppass"),
        ("[github]\n\toauth-token = {c}\n", 5, "github.oauth-token"),
        ("[my-secrets]\n\tvalue = {c}\n", 5, "my-secrets.value"),
        ('[credential]\n\thelper = "!f() { echo password={c}; }; f"\n', 5, "credential.helper"),
        (
            '[credential "https://example.invalid"]\n\thelper = "!f() { echo token={c}; }; f"\n',
            5,
            "credential.*.helper",
        ),
        ("# old remote: https://deploy:{c}@example.invalid/repo.git\n", 4, "a URL with credentials"),
    ],
)
def test_a_config_that_looks_like_it_carries_a_credential_is_not_granted(
    home: Path, snippet: str, line: int, key: str
) -> None:
    canary = _canary()
    config = _write(home / ".gitconfig", USER + snippet.replace("{c}", canary))
    policy = _policy(home, preset="claude-code")
    assert _real(config) not in _git_grants(policy)
    [warning] = _credential_warnings(policy)
    assert f"(values never shown): {_real(config)} " in warning and f"line {line} ({key})" in warning
    assert "git inside will fail to read its configuration" in warning
    assert warning.endswith(f"--allow-read {_real(config)} grants it anyway")
    assert canary not in json.dumps(policy.as_dict())


@pytest.mark.parametrize(
    ("snippet", "key"),
    [
        ('[http "https://example.invalid/"]\n\textraHeader = Authorization: Bearer {c}\n', "http.*.extraheader"),
        ("[github]\n\ttoken = {c}\n", "github.token"),
    ],
)
@pytest.mark.parametrize("included", [False, True], ids=["gitconfig", "included"])
def test_a_byte_order_mark_does_not_hide_the_first_section(home: Path, snippet: str, key: str, included: bool) -> None:
    canary = _canary()
    target = home / ("tokens.inc" if included else ".gitconfig")
    target.write_bytes((BOM + snippet.replace("{c}", canary) + USER).encode())  # git skips the mark, reads line 1
    if included:
        _write(home / ".gitconfig", USER + "[include]\n\tpath = tokens.inc\n")
    policy = _policy(home, preset="claude-code")
    assert _real(target) not in _git_grants(policy)
    [warning] = _credential_warnings(policy)
    assert f"{_real(target)} line 2 ({key})" in warning
    assert canary not in json.dumps(policy.as_dict())


def test_a_credential_in_an_included_file_keeps_only_that_file_out(home: Path) -> None:
    canary = _canary()
    tokens = _write(home / ".config" / "git" / "tokens.inc", f"[core]\n\tpager = cat\n[gitlab]\n\ttoken = {canary}\n")
    config = _write(home / ".gitconfig", USER + "[include]\n\tpath = ~/.config/git/tokens.inc\n")
    policy = _policy(home, preset="codex")
    assert set(_git_grants(policy)) == {_real(config)}
    [warning] = _credential_warnings(policy)
    assert f"{_real(tokens)} line 4 (gitlab.token)" in warning
    assert canary not in json.dumps(policy.as_dict())
    # --allow-read grants it anyway; a file another grant covers gets no git grant and no check.
    allowed = _policy(home, preset="codex", read=[str(tokens)])
    assert [g.origin for g in allowed.grants if g.path == str(tokens)] == ["user"]
    assert not _credential_warnings(allowed)


def test_ignore_and_attributes_files_name_their_own_effect(home: Path) -> None:
    canary = _canary()
    ignore = _write(home / ".config" / "git" / "ignore", f"*.tmp\n# https://deploy:{canary}@example.invalid/\n")
    [warning] = _credential_warnings(_policy(home, preset="codex"))
    assert f"{_real(ignore)} line 2 (a URL with credentials)" in warning
    assert "git add, commit and status inside will fail (it cannot use it as an exclude file)" in warning
    assert canary not in warning


@pytest.mark.parametrize(
    ("setting", "effect"),
    [
        ("core.excludesFile", "git add, commit and status inside will fail"),
        ("core.attributesFile", "git inside will warn on every command and ignore those attributes"),
        ("commit.template", "git commit inside will fail unless it is given a message"),
    ],
)
def test_a_named_file_with_a_credential_url_is_kept_out_with_its_effect(home: Path, setting: str, effect: str) -> None:
    canary = _canary()
    named = _write(home / "named.txt", f"# from https://deploy:{canary}@example.invalid/\n")
    section, key = setting.split(".")
    _write(home / ".gitconfig", USER + f"[{section}]\n\t{key} = ~/named.txt\n")
    policy = _policy(home, preset="codex")
    assert _real(named) not in _git_grants(policy)
    [warning] = _credential_warnings(policy)
    assert f"{_real(named)} line 1 (a URL with credentials)" in warning and effect in warning
    assert canary not in json.dumps(policy.as_dict())


@pytest.mark.parametrize("protected", [".ssh/id_rsa", ".git-credentials"])
def test_a_gitconfig_hardlinked_to_a_protected_file_is_refused_unread(home: Path, protected: str) -> None:
    canary = _canary()
    target = _write(home / protected, f"[gitlab]\n\ttoken = {canary}\n")  # flagged, were it ever read
    os.link(target, home / ".gitconfig")
    policy = _policy(home, preset="claude-code")
    assert _git_grants(policy) == {}
    refused = [s for s in policy.skipped if s.startswith(f"{_real(home / '.gitconfig')}: Refusing")]
    assert len(refused) == 1 and "protected" in refused[0]
    assert not _credential_warnings(policy) and canary not in json.dumps(policy.as_dict())


def test_a_gitconfig_symlinked_to_a_protected_file_is_followed_to_the_guards_unread(home: Path) -> None:
    canary = _canary()
    key = _write(home / ".ssh" / "id_rsa", f"[gitlab]\n\ttoken = {canary}\n")  # flagged, were it ever read
    (home / ".gitconfig").symlink_to(".ssh/id_rsa")
    policy = _policy(home, preset="codex")
    assert _git_grants(policy) == {}
    assert any(s.startswith(f"{_real(key)}: Refusing a grant inside protected path") for s in policy.skipped)
    assert (
        f"{home / '.gitconfig'}: a symbolic link to {_real(key)}, which is not granted; "
        "git inside reads it only if its target is granted"
    ) in policy.skipped
    assert not _credential_warnings(policy) and canary not in json.dumps(policy.as_dict())
    assert _real(home / ".gitconfig") not in policy.links


def test_an_include_of_a_protected_path_is_refused_unread(home: Path) -> None:
    canary = _canary()
    key = _write(home / ".ssh" / "id_rsa", f"[gitlab]\n\ttoken = {canary}\n")
    config = _write(
        home / ".gitconfig", USER + "[include]\n\tpath = ~/.ssh/id_rsa\n\tpath = ~/.ssh\n\tpath = ~\n\tpath = /\n"
    )
    policy = _policy(home, preset="claude-code")
    assert set(_git_grants(policy)) == {_real(config)}
    assert any(s.startswith(f"{_real(key)}: Refusing a grant inside protected path") for s in policy.skipped)
    for directory in (home / ".ssh", home):
        assert f"{os.path.realpath(directory)}: not a regular file" in policy.skipped
    assert "/: not a regular file" in policy.skipped
    assert not any(g.path.startswith(os.path.realpath(home / ".ssh")) for g in policy.grants)
    assert not _credential_warnings(policy) and canary not in json.dumps(policy.as_dict())


def test_another_homes_protected_paths_are_refused_unread(home: Path, tmp_path: Path) -> None:
    """``~user/`` and absolute paths reach other homes, whose protected paths the guards do not know."""
    canary = _canary()
    other = tmp_path / "other-home"
    config = _write(other / ".ssh" / "config.inc", f"[gitlab]\n\ttoken = {canary}\n")  # flagged, were it read
    (other / ".aws" / "hooks").mkdir(parents=True)
    _write(home / ".gitconfig", USER + f"[include]\n\tpath = {config}\n[core]\n\thooksPath = {other}/.aws/hooks\n")
    policy = _policy(home, preset="claude-code")
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig")}
    for path, name in ((_real(config), ".ssh"), (os.path.realpath(other / ".aws" / "hooks"), ".aws")):
        assert f"{path}: Refusing a path named like protected ~/{name}, of a home not protected here" in policy.skipped
    assert not _credential_warnings(policy) and canary not in json.dumps(policy.as_dict())


@pytest.mark.parametrize(
    ("value", "refusal"),
    [("~", "Refusing to grant a home directory"), ("~/.ssh", "Refusing a grant inside protected path")],
)
def test_a_hooks_directory_the_guards_refuse_is_named_with_its_effect(home: Path, value: str, refusal: str) -> None:
    _write(home / ".gitconfig", USER + f"[core]\n\thooksPath = {value}\n")
    policy = _policy(home, preset="claude-code")
    target = os.path.realpath(home if value == "~" else home / ".ssh")
    assert target not in _git_grants(policy)
    assert any(s.startswith(f"{target}: {refusal}") for s in policy.skipped)
    # --allow-read would meet the same guard: no hint to use it.
    assert [w for w in policy.warnings if "core.hooksPath" in w] == [
        f"git configuration: core.hooksPath {target} is not granted; {HOOKS_EFFECT}"
    ]


def test_a_hooks_directory_holding_a_file_kept_out_is_not_granted(home: Path) -> None:
    canary = _canary()
    dotfiles = home / "dotfiles"
    _write(dotfiles / "pre-commit", "#!/bin/sh\nexit 0\n").chmod(0o755)
    _write(dotfiles / "tokens.inc", f"[gitlab]\n\ttoken = {canary}\n")
    _write(home / ".gitconfig", USER + "[include]\n\tpath = ~/dotfiles/tokens.inc\n[core]\n\thooksPath = ~/dotfiles\n")
    policy = _policy(home, preset="codex")
    target = os.path.realpath(dotfiles)
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig")}
    assert f"{target}: holds a git configuration file kept out as a credential" in policy.skipped
    assert (
        f"git configuration: core.hooksPath {target} is not granted; {HOOKS_EFFECT}; --allow-read {target} grants it"
    ) in policy.warnings
    assert canary not in json.dumps(policy.as_dict())


def test_includes_named_by_a_file_the_agent_can_write_are_ignored(home: Path) -> None:
    private = _write(home / "notes" / "private.cfg", "[core]\n\tpager = cat\n")  # clean: only the rule keeps it out
    local = _write(home.parent / "ws" / ".gitconfig.local", f"[include]\n\tpath = {private}\n")
    _write(home / ".gitconfig", USER + f"[include]\n\tpath = {local}\n")
    policy = _policy(home, preset="claude-code")
    # The workspace grant already makes .gitconfig.local readable (and writable): no grant, includes ignored.
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig")}
    assert not any(_real(private) in entry for entry in policy.skipped)
    # The same include from a file the agent cannot write is followed.
    readonly = _write(home / "dotfiles" / "local.inc", f"[include]\n\tpath = {private}\n")
    _write(home / ".gitconfig", USER + f"[include]\n\tpath = {readonly}\n")
    assert _real(private) in _git_grants(_policy(home, preset="claude-code"))


def test_a_file_already_granted_keeps_its_grant_and_its_includes_are_followed(home: Path) -> None:
    identity = _write(home / ".config" / "git" / "identity.inc", USER)
    config = _write(
        home / ".gitconfig", f"[gitlab]\n\ttoken = {_canary()}\n[include]\n\tpath = ~/.config/git/identity.inc\n"
    )
    policy = _policy(home, preset="codex", read=[str(config)])
    origins = {g.path: g.origin for g in policy.grants}
    assert origins[str(config)] == "user" and origins[_real(identity)] == "preset:codex:git"
    assert not _credential_warnings(policy)


@pytest.mark.parametrize("on_macos", [False, True], ids=["landlock", "seatbelt"])
def test_names_from_a_config_are_escaped_in_messages(
    home: Path, monkeypatch: pytest.MonkeyPatch, on_macos: bool
) -> None:
    monkeypatch.setattr(gitconfig, "SEATBELT", on_macos)
    _write(home / "\x1b]0;owned\x07.cfg", "[gitlab]\n\ttoken = x\n")
    _write(home / ".gitconfig", USER + '[include]\n\tpath = "~/\x1b]0;owned\x07.cfg"\n')
    policy = _policy(home, preset="codex")
    texts = [*policy.skipped, *policy.warnings]
    expected = "Seatbelt cannot name it in a rule" if on_macos else "\\x1b]0;owned\\x07.cfg line 2 (gitlab.token)"
    assert any(expected in text and "\\x1b]0;owned\\x07.cfg" in text for text in texts)
    assert all(text.isprintable() for text in texts)


def test_the_parser_reports_the_line_each_key_starts_on() -> None:
    data = b'# c\n[a]\n\tk = v \\\n continued\n\n[b "s"]\r\n\tflag\r\n\tx = "q;#" ; c\n[c]\n\ty = 1\n'
    entries = parse_git_config_lines(data)
    assert [(line, name) for line, name, _ in entries] == [(3, "a.k"), (7, "b.s.flag"), (8, "b.s.x"), (10, "c.y")]
    assert parse_git_config(data) == [(name, value) for _, name, value in entries]


def test_the_parser_skips_one_byte_order_mark_as_git_does() -> None:
    data = BOM.encode() + b"[a]\n\tk = v\n[b]\n\tflag\n"
    assert parse_git_config_lines(data) == [(2, "a.k", "v"), (4, "b.flag", "true")]
    assert parse_git_config_lines(data[len(BOM.encode()) :]) == parse_git_config_lines(data)


# --- symbolic links ------------------------------------------------------------------------------


def test_a_gitconfig_symlinked_into_dotfiles_is_followed(home: Path) -> None:
    target = _write(home / "dotfiles" / "git" / ".gitconfig", USER)
    (home / ".gitconfig").symlink_to("dotfiles/git/.gitconfig")  # as GNU stow makes it
    policy = _policy(home, preset="claude-code")
    assert _git_grants(policy) == {_real(target): ("ro", False, "preset:claude-code:git")}
    assert _real(home / ".gitconfig") in policy.links  # Seatbelt reads a link to follow it
    assert (
        f"git configuration: {home / '.gitconfig'} is a symbolic link, followed: git reads {_real(target)}, "
        "granted read-only"
    ) in policy.warnings


def test_link_chains_and_folded_directories_are_followed(home: Path) -> None:
    store = _write(home / "store" / "hm_gitconfig", USER)  # home-manager: a link to a link to the file
    (home / "hm-files").mkdir()
    (home / "hm-files" / "config").symlink_to(store)
    (home / ".config" / "git").mkdir(parents=True)
    (home / ".config" / "git" / "config").symlink_to(home / "hm-files" / "config")
    extra = _write(home / "dotfiles" / "conf.d" / "extra.inc", "[core]\n\tpager = cat\n")
    (home / "conf.d").symlink_to("dotfiles/conf.d")  # a folded directory, as stow folds it
    _write(home / ".gitconfig", USER + "[include]\n\tpath = ~/conf.d/extra.inc\n")
    policy = _policy(home, preset="codex")
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig"), _real(store), _real(extra)}
    for link in (home / ".config" / "git" / "config", home / "hm-files" / "config", home / "conf.d"):
        assert _real(link) in policy.links
    assert (
        f"git configuration: {home / 'conf.d' / 'extra.inc'} is below a symbolic link, followed: "
        f"git reads {_real(extra)}, granted read-only"
    ) in policy.warnings


def test_below_a_followed_link_an_absent_file_is_quiet_and_a_refused_one_is_named(home: Path) -> None:
    config = _write(home / "dotfiles" / "git" / "config", USER)  # ignore and attributes absent
    (home / ".config").mkdir()
    (home / ".config" / "git").symlink_to("../dotfiles/git")
    (home / "keys").symlink_to(".ssh")
    key = home / ".ssh" / "id_rsa"
    _write(home / ".gitconfig", USER + "[include]\n\tpath = ~/keys/id_rsa\n")
    policy = _policy(home, preset="claude-code")
    assert set(_git_grants(policy)) == {_real(home / ".gitconfig"), _real(config)}
    for name in ("ignore", "attributes"):
        assert _real(home / "dotfiles" / "git" / name) in policy.skipped  # absent: git reads nothing there
        assert not any(entry.startswith(f"{home / '.config' / 'git' / name}:") for entry in policy.skipped)
    assert any(s.startswith(f"{_real(key)}: Refusing a grant inside protected path") for s in policy.skipped)
    assert (
        f"{home / 'keys' / 'id_rsa'}: below a symbolic link to {_real(key)}, which is not granted; "
        "git inside reads it only if its target is granted"
    ) in policy.skipped


def test_a_link_the_agent_could_change_is_not_followed(home: Path) -> None:
    canary = _canary()
    private = _write(home / "notes" / "private.cfg", f"[gitlab]\n\ttoken = {canary}\n")  # flagged, were it read
    xdg = home.parent / "ws" / "xdg"  # inside the workspace, which the agent can write
    (xdg / "git").mkdir(parents=True)
    (xdg / "git" / "config").symlink_to(private)
    policy = _policy(home, preset="codex", git_env={"HOME": str(home), "XDG_CONFIG_HOME": str(xdg)})
    assert _git_grants(policy) == {}
    assert (
        f"{xdg / 'git' / 'config'}: the symbolic link {_real(xdg / 'git' / 'config')} is inside a write grant, "
        "so it is not followed; git inside reads it only if its target is granted (--allow-read its target)"
    ) in policy.skipped
    assert not _credential_warnings(policy) and canary not in json.dumps(policy.as_dict())
    assert _real(xdg / "git" / "config") not in policy.links


# --- macOS rendering (static, every platform) --------------------------------------------------


def test_seatbelt_renders_each_git_file_as_a_literal_read_grant(home: Path) -> None:
    files = [
        _write(home / ".gitconfig", USER + "[include]\n\tpath = ~/.config/git/identity.inc\n"),
        _write(home / ".config" / "git" / "identity.inc", USER),
    ]
    lines = seatbelt.render_profile(_policy(home, preset="claude-code")).splitlines()
    assert lines[2].startswith('(deny file-read* file-write* (subpath "/Users")') and f'"{home}"' in lines[2]
    for path in files:
        index = next(
            i
            for i, line in enumerate(lines)
            if line.startswith(f'(allow file-read* file-clone (literal "{_real(path)}")')
        )
        assert "file-write" not in lines[index] and "(subpath" not in lines[index]
        assert 2 < index < len(lines) - 1, "after the home deny, before the protected deny"
    metadata = next(line for line in lines if line.startswith("(allow file-read-metadata"))
    for ancestor in (home, home / ".config" / "git"):
        assert f'(literal "{os.path.realpath(ancestor)}")' in metadata
    assert lines[-1].startswith("(deny file-read* file-write* file-link file-clone") and "/.ssh" in lines[-1]


def test_seatbelt_lets_git_read_the_links_it_follows_and_run_the_hooks(home: Path) -> None:
    target = _write(home / "dotfiles" / ".gitconfig", USER + "[core]\n\thooksPath = ~/.githooks\n")
    (home / ".gitconfig").symlink_to("dotfiles/.gitconfig")
    _write(home / ".githooks" / "pre-commit", "#!/bin/sh\nexit 0\n").chmod(0o755)
    lines = seatbelt.render_profile(_policy(home, preset="claude-code")).splitlines()
    links = next(line for line in lines if line.startswith("(allow file-read* (literal"))
    assert f'(literal "{_real(home / ".gitconfig")}")' in links and "file-write" not in links
    assert any(line.startswith(f'(allow file-read* file-clone (literal "{_real(target)}")') for line in lines)
    hooks = next(line for line in lines if f'(subpath "{os.path.realpath(home / ".githooks")}")' in line)
    assert hooks.startswith("(allow file-read* file-clone (subpath") and "file-write" not in hooks


@pytest.mark.parametrize("on_macos", [True, False], ids=["seatbelt", "landlock"])
def test_paths_seatbelt_cannot_name_are_skipped_on_macos(
    home: Path, monkeypatch: pytest.MonkeyPatch, on_macos: bool
) -> None:
    monkeypatch.setattr(gitconfig, "SEATBELT", on_macos)
    control = _write(home / "a\x1bb.inc", "[core]\n\tpager = cat\n")
    long = _long_file(home)
    _write(home / ".gitconfig", USER + f'[include]\n\tpath = "~/a\x1bb.inc"\n\tpath = {long}\n')
    policy = _policy(home, preset="claude-code")
    if on_macos:
        assert set(_git_grants(policy)) == {_real(home / ".gitconfig")}
        texts = "\n".join(policy.skipped)
        assert "Seatbelt cannot name it in a rule (Control character in sandbox path), so it is not granted" in texts
        assert "Seatbelt cannot name it in a rule (Path too long for a Seatbelt string literal" in texts
        assert seatbelt.render_profile(policy)  # renders: run can start
    else:  # Landlock takes any path; a Seatbelt profile of this policy raises, which run reports with exit 3
        assert {_real(control), _real(long)} <= set(_git_grants(policy))
        with pytest.raises(ValueError):
            seatbelt.render_profile(policy)


# --- end to end ----------------------------------------------------------------------------------


@pytest.fixture
def box(home: Path) -> dict[str, Any]:
    """A decoy home whose user name comes from an included file, so the name proves both were read."""
    _write(home / ".config" / "git" / "identity.inc", USER)
    _write(home / ".gitconfig", "[include]\n\tpath = ~/.config/git/identity.inc\n")
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONPATH": str(ROOT / "01_KISH_ENGINE"),
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    if "TMPDIR" in os.environ:
        env["TMPDIR"] = os.environ["TMPDIR"]
    return {"home": home, "ws": home.parent / "ws", "env": env, "journal": home.parent / "state" / "journal.db"}


def _workspace(box: dict[str, Any], name: str) -> Path:
    path = box["ws"] / name
    path.mkdir()
    return path


def _cli(box: dict[str, Any], cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-P", "-m", "babylon60.cli.main_dispatcher", "run", "--allow-root"]
        + ["--journal", str(box["journal"]), "--workspace", str(cwd), *args],
        env=box["env"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=120,
    )


def _real_agent_state() -> str | None:
    """A path ``--preset claude-code`` would grant read-write from this account's real home, if any exists."""
    home = account_home()
    return next((home + item[1:] for item in PRESETS["claude-code"]["write"] if os.path.lexists(home + item[1:])), None)


def _dotfiles(home: Path) -> tuple[str, str]:
    """A stow-style ``~/.gitconfig`` with an ssh rewrite, the files it names and a hooks directory, and a
    script whose output proves git used each of them, with that output."""
    (home / ".gitconfig").unlink()
    _write(
        home / "dotfiles" / "git" / ".gitconfig",
        "[include]\n\tpath = ~/.config/git/identity.inc\n"
        '[url "git@github.com:"]\n\tinsteadOf = https://github.com/\n'
        "[core]\n\texcludesFile = ~/.gitignore_global\n\tattributesFile = ~/.gitattributes_global\n"
        "\thooksPath = ~/.githooks\n[commit]\n\ttemplate = ~/.gitmessage\n",
    )
    (home / ".gitconfig").symlink_to("dotfiles/git/.gitconfig")
    _write(home / ".gitignore_global", "*.tmp\n")
    _write(home / ".gitattributes_global", "*.dat binary\n")
    _write(home / ".gitmessage", "Decoy template subject\n")
    _write(home / ".githooks" / "pre-commit", "#!/bin/sh\necho hook-ran > hook.out\n").chmod(0o755)
    script = (
        "git init -q && touch a.tmp b && git add -A && GIT_EDITOR=true git commit -q --allow-empty-message"
        " && git log -1 --format=%an:%s && git ls-files && git check-attr binary -- x.dat && cat hook.out"
        " && git ls-remote --get-url https://github.com/decoy/repo.git"
    )
    expected = "Decoy User:Decoy template subject\nb\nx.dat: binary: set\nhook-ran\ngit@github.com:decoy/repo.git\n"
    return script, expected


@needs_backend
def test_dry_run_lists_the_git_grants_and_warns_without_values(box: dict[str, Any]) -> None:
    canary = _canary()
    tokens = _write(box["home"] / "tokens.inc", f"[gitlab]\n\ttoken = {canary}\n")
    _write(box["home"] / ".gitconfig", "[include]\n\tpath = ~/.config/git/identity.inc\n\tpath = tokens.inc\n")
    dry = _cli(box, _workspace(box, "dry"), "--dry-run", "--preset", "claude-code", "--", "true")
    assert dry.returncode == 0, dry.stderr
    grants = [
        (g["path"], g["access"], g["is_dir"], g["origin"])
        for g in json.loads(dry.stdout)["grants"]
        if g["origin"].endswith(":git")
    ]
    expected = [box["home"] / ".gitconfig", box["home"] / ".config" / "git" / "identity.inc"]
    assert grants == [(_real(path), "ro", False, "preset:claude-code:git") for path in expected]
    assert (
        "babylon60 run: warning: git configuration not granted, it looks like it carries a credential "
        f"(values never shown): {_real(tokens)} line 2 (gitlab.token)"
    ) in dry.stderr
    assert canary not in dry.stdout + dry.stderr


@needs_backend
def test_dry_run_says_which_link_it_followed_and_what_it_granted(box: dict[str, Any]) -> None:
    _dotfiles(box["home"])
    dry = _cli(box, _workspace(box, "dry-links"), "--dry-run", "--preset", "codex", "--", "true")
    assert dry.returncode == 0, dry.stderr
    document = json.loads(dry.stdout)
    granted = {g["path"]: g["is_dir"] for g in document["grants"] if g["origin"] == "preset:codex:git"}
    home = box["home"]
    assert granted == {
        _real(home / "dotfiles" / "git" / ".gitconfig"): False,
        _real(home / ".config" / "git" / "identity.inc"): False,
        _real(home / ".gitignore_global"): False,
        _real(home / ".gitattributes_global"): False,
        _real(home / ".gitmessage"): False,
        os.path.realpath(home / ".githooks"): True,
    }
    assert _real(home / ".gitconfig") in document["links"]
    assert (
        f"babylon60 run: warning: git configuration: {home / '.gitconfig'} is a symbolic link, followed: "
        f"git reads {_real(home / 'dotfiles' / 'git' / '.gitconfig')}, granted read-only"
    ) in dry.stderr


@pytest.mark.skipif(sys.platform != "darwin", reason="Seatbelt only: Landlock takes any path")
def test_run_exits_3_when_seatbelt_cannot_name_a_grant(box: dict[str, Any], tmp_path: Path) -> None:
    odd = _write(tmp_path / "odd\x1bname", "decoy\n")
    ran = _cli(box, _workspace(box, "odd"), "--allow-read", str(odd), "--", "/usr/bin/true")
    assert ran.returncode == 3, ran.stderr
    assert "babylon60 run: cannot start the confined command: Control character in sandbox path" in ran.stderr


@needs_landlock
@needs_git
def test_without_a_preset_git_cannot_read_its_configuration(box: dict[str, Any]) -> None:
    control = subprocess.run(
        ["/bin/sh", "-c", PROBE], env=box["env"], cwd=str(_workspace(box, "control")), capture_output=True, text=True
    )
    assert control.returncode == 0 and control.stdout == "Decoy User\n", control.stderr
    bare = _cli(box, _workspace(box, "bare"), "--", "/bin/sh", "-c", PROBE)
    assert bare.returncode == 128 and UNREADABLE in bare.stderr, bare.stderr
    assert "Decoy User" not in bare.stdout


@needs_landlock
@needs_git
def test_git_reads_its_configuration_inside_run_with_a_preset(box: dict[str, Any]) -> None:
    reached = _real_agent_state()
    if reached:
        pytest.skip(f"--preset claude-code would grant this account's real agent state ({reached}) to the test")
    ran = _cli(box, _workspace(box, "preset"), "--preset", "claude-code", "--", "/bin/sh", "-c", PROBE)
    assert ran.returncode == 0 and ran.stdout == "Decoy User\n", ran.stderr


@needs_landlock
@needs_git
def test_run_with_a_preset_follows_dotfiles_and_runs_the_hooks(box: dict[str, Any]) -> None:
    reached = _real_agent_state()
    if reached:
        pytest.skip(f"--preset claude-code would grant this account's real agent state ({reached}) to the test")
    script, expected = _dotfiles(box["home"])
    control = subprocess.run(
        ["/bin/sh", "-c", script],
        env=box["env"],
        cwd=str(_workspace(box, "dot-control")),
        capture_output=True,
        text=True,
    )
    assert control.returncode == 0 and control.stdout == expected, control.stderr
    ran = _cli(box, _workspace(box, "dot-preset"), "--preset", "claude-code", "--", "/bin/sh", "-c", script)
    assert ran.returncode == 0 and ran.stdout == expected, ran.stderr


@needs_landlock
@needs_git
def test_the_preset_grants_let_git_read_but_never_write_or_link_them(box: dict[str, Any], tmp_path: Path) -> None:
    """The same launch layers as ``run`` (Landlock and seccomp), with the presets expanded in the decoy home."""
    private = tmp_path / "private-tmp"
    private.mkdir()
    env = {**box["env"], "TMPDIR": str(private)}
    config = box["home"] / ".gitconfig"
    original = config.read_bytes()

    def run(preset: str | None, script: str) -> launcher.Result:
        ws = _workspace(box, f"inproc-{preset}-{len(script)}")
        policy = build_policy(
            ws, homes=[str(box["home"])], preset=preset, git_env={"HOME": str(box["home"])}, private_tmp=str(private)
        )
        return launcher.run(launcher.session_launch(["/bin/sh", "-c", script], policy), env=env, cwd=str(ws))

    granted = run("claude-code", PROBE)
    assert granted.status.get("ok"), granted.status
    assert granted.returncode == 0 and granted.stdout == b"Decoy User\n", granted.stderr
    bare = run(None, PROBE)
    assert bare.status.get("ok") and bare.returncode == 128 and UNREADABLE.encode() in bare.stderr
    # Read-only: no write, and no hard link into the writable workspace (Landlock answers EXDEV).
    tamper = run("codex", 'ln "$HOME/.gitconfig" linked; echo "$?"; echo planted >> "$HOME/.gitconfig"; echo "$?"')
    assert tamper.status.get("ok"), tamper.status
    assert [code != "0" for code in tamper.stdout.decode().split()] == [True, True], tamper.stderr
    assert b"Invalid cross-device link" in tamper.stderr
    assert config.read_bytes() == original and config.stat().st_nlink == 1


@needs_landlock
@needs_git
def test_git_uses_dotfiles_named_files_and_hooks_inside_the_launcher(box: dict[str, Any], tmp_path: Path) -> None:
    """The launcher's layers as ``run`` applies them, with the decoy home only (also as root)."""
    home = box["home"]
    script, expected = _dotfiles(home)
    control = subprocess.run(
        ["/bin/sh", "-c", script],
        env=box["env"],
        cwd=str(_workspace(box, "all-control")),
        capture_output=True,
        text=True,
    )
    assert control.returncode == 0 and control.stdout == expected, control.stderr
    private = tmp_path / "private-tmp"
    private.mkdir()
    env = {**box["env"], "TMPDIR": str(private)}
    for preset in (*sorted(PRESETS), None):
        ws = _workspace(box, f"all-{preset}")
        policy = build_policy(
            ws, homes=[str(home)], preset=preset, git_env={"HOME": str(home)}, private_tmp=str(private)
        )
        ran = launcher.run(launcher.session_launch(["/bin/sh", "-c", script], policy), env=env, cwd=str(ws))
        assert ran.status.get("ok"), ran.status
        if preset is None:
            assert ran.returncode == 128 and UNREADABLE.encode() in ran.stderr, ran.stderr
        else:
            assert ran.returncode == 0 and ran.stdout.decode() == expected, ran.stderr
    # The hooks directory is read-only inside: a hook cannot be replaced from there.
    ws = _workspace(box, "all-tamper")
    policy = build_policy(ws, homes=[str(home)], preset="codex", git_env={"HOME": str(home)}, private_tmp=str(private))
    hook = home / ".githooks" / "pre-commit"
    original = hook.read_bytes()
    tamper = launcher.run(
        launcher.session_launch(["/bin/sh", "-c", f'echo planted >> "{hook}"; echo "$?"'], policy), env=env, cwd=str(ws)
    )
    assert tamper.status.get("ok") and tamper.stdout.strip() != b"0", tamper.stderr
    assert hook.read_bytes() == original
