"""The git configuration a preset grants read-only (``gitconfig.py``), and what keeps a file out of it.

With a ``~/.gitconfig`` present, every git command inside ``babylon60 run`` used to die with
"unknown error occurred while reading the configuration files": no preset let git read the
user's configuration. Every preset now grants ``~/.gitconfig``,
``~/.config/git/{config,ignore,attributes}`` and the files they include, read-only and one
by one, after the policy guards, unless their content looks like a credential.

Real files in throwaway homes, the real policy guards and, end to end, the real CLI under
real Landlock (Linux). Secrets are random canaries. Set BABYLON60_REQUIRE_LANDLOCK=1 to fail
instead of skipping when Landlock is missing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from typing import Any

import pytest

from babylon60.confine import launcher, seatbelt
from babylon60.confine.gitconfig import MAX_FILES
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
    assert f"git configuration: more than {MAX_FILES} files named through includes; the rest is not granted" in (
        policy.warnings
    )


def test_ordinary_settings_are_granted(home: Path) -> None:
    config = _write(
        home / ".gitconfig",
        USER + "[credential]\n\thelper = store\n\tusername = decoy\n"
        "[user]\n\tsigningkey = 0xDECAFBAD\n"
        "[http]\n\tproxy = http://proxy.example.invalid:3128\n\tsslVerify = true\n"
        '[remote "origin"]\n\turl = ssh://git@example.invalid/repo.git\n'
        "[core]\n\tsshCommand = ssh -i ~/.ssh/id_ed25519\n\texcludesFile = ~/.gitignore_global\n"
        '[includeIf "gitdir:~/work/"]\n\tpath = ~/.config/git/work.inc\n'
        "[alias]\n\tst = status\n",
    )
    policy = _policy(home, preset="claude-code")
    assert _real(config) in _git_grants(policy)
    assert not _credential_warnings(policy)


# --- what is not granted -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("snippet", "line", "key"),
    [
        ('[http "https://example.invalid/"]\n\textraHeader = Authorization: Bearer {c}\n', 5, "http.*.extraheader"),
        ("[http]\n\textraheader = AUTHORIZATION: basic {c}\n", 5, "http.extraheader"),
        ('[url "https://{c}@example.invalid/"]\n\tinsteadOf = https://example.invalid/\n', 5, "url.*.insteadof"),
        ('[url "ssh://{c}.example.invalid/"]\n\tpushInsteadOf = https://example.invalid/\n', 5, "url.*.pushinsteadof"),
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
    assert "git status inside will fail (it cannot use it as an exclude file)" in warning
    assert canary not in warning


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


def test_a_gitconfig_symlinked_to_a_protected_file_is_skipped_unread(home: Path) -> None:
    canary = _canary()
    _write(home / ".ssh" / "id_rsa", f"[gitlab]\n\ttoken = {canary}\n")
    (home / ".gitconfig").symlink_to(".ssh/id_rsa")
    policy = _policy(home, preset="codex")
    assert _git_grants(policy) == {}
    assert f"{_real(home / '.gitconfig')}: a symbolic link, not followed" in "\n".join(policy.skipped)
    assert not _credential_warnings(policy) and canary not in json.dumps(policy.as_dict())


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


def test_names_from_a_config_are_escaped_in_messages(home: Path) -> None:
    _write(home / "\x1b]0;owned\x07.cfg", "[gitlab]\n\ttoken = x\n")
    _write(home / ".gitconfig", USER + '[include]\n\tpath = "~/\x1b]0;owned\x07.cfg"\n')
    policy = _policy(home, preset="codex")
    texts = [*policy.skipped, *policy.warnings]
    assert any("\\x1b]0;owned\\x07.cfg line 2 (gitlab.token)" in text for text in texts)
    assert all(text.isprintable() for text in texts)


def test_the_parser_reports_the_line_each_key_starts_on() -> None:
    data = b'# c\n[a]\n\tk = v \\\n continued\n\n[b "s"]\r\n\tflag\r\n\tx = "q;#" ; c\n[c]\n\ty = 1\n'
    entries = parse_git_config_lines(data)
    assert [(line, name) for line, name, _ in entries] == [(3, "a.k"), (7, "b.s.flag"), (8, "b.s.x"), (10, "c.y")]
    assert parse_git_config(data) == [(name, value) for _, name, value in entries]


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
