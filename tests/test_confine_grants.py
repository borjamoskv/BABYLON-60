"""What ``babylon60 run`` grants for the command itself, and the ``#!`` hint.

A script starting ``#!/usr/bin/env cargo`` used to grant all of ``~/.cargo``,
``credentials.toml`` (a crates.io token) included. Now the command's own file is
the only grant derived from it; the ``#!`` line only words a hint on stderr.

Real files and, end to end, the real CLI under real Landlock (Linux) or Seatbelt
(macOS), in throwaway homes whose secrets are random canaries. Set
BABYLON60_REQUIRE_LANDLOCK=1 to fail instead of skipping when Landlock is missing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess
import sys
from typing import Any

import pytest

from babylon60.confine import launcher
from babylon60.confine.cli import executable_grants, interpreter_hint
from babylon60.confine.policy import MIN_LANDLOCK_ABI, SYSTEM_READ_EXEC, Policy, ancestry, build_policy

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
HINT = "(its #! interpreter)"


def _executable(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o755)
    return path


def _policy(ws: Path, home: Path, **kwargs: Any) -> Policy:
    return build_policy(ws, homes=[str(home)], system=False, **kwargs)


def _real(path: Path) -> str:
    """Grants and suggested directories name real paths (``/var`` is ``/private/var`` on macOS)."""
    return os.path.realpath(path)


@pytest.fixture
def layout(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    ws = tmp_path / "ws"
    ws.mkdir()
    return {"root": tmp_path, "home": home, "ws": ws}


# --- executable_grants -------------------------------------------------------


def test_symlink_chain_grants_only_the_installed_file(layout: dict[str, Path]) -> None:
    home = layout["home"]
    versions = home / ".local" / "share" / "claude" / "versions"
    installed = _executable(versions / "2.0.1", "binary placeholder\n")
    (versions / "2.0.0").write_text("previous version\n")
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "claude-latest").symlink_to("../share/claude/versions/2.0.1")
    (bin_dir / "claude").symlink_to("claude-latest")
    grants = executable_grants(str(bin_dir / "claude"), (str(home),))
    assert grants == [_real(installed)]
    runtime = [g for g in _policy(layout["ws"], home, runtime=grants).grants if g.origin == "runtime"]
    assert [(g.path, g.access, g.is_dir) for g in runtime] == [(_real(installed), "ro", False)]


def test_executable_outside_every_home_gets_no_grant(layout: dict[str, Path]) -> None:
    outside = _executable(layout["root"] / "opt" / "bin" / "tool", "#!/bin/sh\n")
    homes = (str(layout["home"]),)
    assert executable_grants(str(outside), homes) == []
    assert executable_grants("/bin/sh", homes) == []
    assert executable_grants(str(layout["root"] / "missing"), homes) == []


def test_link_from_outside_into_a_home_grants_the_file_it_reaches(layout: dict[str, Path]) -> None:
    target = _executable(layout["home"] / ".tools" / "tool", "#!/bin/sh\n")
    link = layout["root"] / "usr-local-bin" / "tool"
    link.parent.mkdir()
    link.symlink_to(target)
    assert executable_grants(str(link), (str(layout["home"]),)) == [_real(target)]


def test_home_spelled_through_a_symlink_is_matched_by_identity(layout: dict[str, Path]) -> None:
    alias = layout["root"] / "home-alias"
    alias.symlink_to(layout["home"])
    tool = _executable(layout["home"] / ".tools" / "tool", "#!/bin/sh\n")
    # The tool's real path does not start with the alias; inode identity still places it in the home.
    assert executable_grants(str(tool), (str(alias),)) == [_real(tool)]


def test_shebang_never_widens_the_grant(layout: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    home = layout["home"]
    cargo = _executable(home / ".cargo" / "bin" / "cargo", "#!/bin/sh\n")
    (home / ".cargo" / "credentials.toml").write_text('token = "B60-CANARY-unit"\n')
    monkeypatch.setenv("PATH", os.pathsep.join([str(cargo.parent), "/usr/bin", "/bin"]))
    for line in ("#!/usr/bin/env cargo", "#!/usr/bin/env -S cargo +nightly -Zscript", f"#!{cargo}"):
        in_home = _executable(home / "scripts" / "setup", line + "\n")
        assert executable_grants(str(in_home), (str(home),)) == [_real(in_home)]
        in_workspace = _executable(layout["ws"] / "setup", line + "\n")
        assert executable_grants(str(in_workspace), (str(home),)) == []


def test_policy_guards_still_check_the_executable_grant(layout: dict[str, Path]) -> None:
    tool = _executable(layout["home"] / ".ssh" / "tool", "#!/bin/sh\n")
    grants = executable_grants(str(tool), (str(layout["home"]),))
    policy = _policy(layout["ws"], layout["home"], runtime=grants)
    assert grants == [_real(tool)] and _real(tool) not in {g.path for g in policy.grants}
    assert any(skipped.startswith(f"{_real(tool)}: ") for skipped in policy.skipped)


# --- interpreter_hint --------------------------------------------------------


@pytest.fixture
def cargo(layout: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> Path:
    home = layout["home"]
    cargo = _executable(home / ".cargo" / "bin" / "cargo", "#!/bin/sh\necho cargo\n")
    (home / ".cargo" / "credentials.toml").write_text('token = "B60-CANARY-hint"\n')
    monkeypatch.setenv("PATH", os.pathsep.join([str(cargo.parent), "/usr/bin", "/bin"]))
    return cargo


def _hint(layout: dict[str, Path], line: str, **policy: Any) -> str | None:
    script = _executable(layout["ws"] / "setup-tool", line + "\n")
    homes = (str(layout["home"]),)
    return interpreter_hint(str(script), homes, _policy(layout["ws"], layout["home"], **policy))


def _suggested(hint: str) -> list[str]:
    return re.findall(r"--allow-read (\S+)", hint)


@pytest.mark.parametrize(
    "line",
    [
        "#!/usr/bin/env cargo",
        "#!/usr/bin/env -S cargo +nightly -Zscript",
        "#!/usr/bin/env -Scargo -q",
        "#!/usr/bin/env --split-string=cargo -q",
        "#!/usr/bin/env -vS cargo",
        "#!/usr/bin/env -S RUST_LOG=info cargo",
        "#!/usr/bin/env -u RUSTFLAGS cargo",
        "#!/usr/bin/env -- cargo",
        "#!  {cargo} --offline",
        "#!{cargo}",
    ],
)
def test_hint_names_an_interpreter_under_a_home(layout: dict[str, Path], cargo: Path, line: str) -> None:
    hint = _hint(layout, line.format(cargo=cargo))
    assert hint is not None and "\n" not in hint
    assert hint.startswith(f"setup-tool starts {cargo} {HINT}")
    # The directory that holds the interpreter, never ~/.cargo with credentials.toml in it.
    assert _suggested(hint) == [_real(cargo.parent)]
    assert "--preset" not in hint  # no preset covers ~/.cargo


def test_hint_follows_the_path_a_shebang_sets(
    layout: dict[str, Path], cargo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    assert _hint(layout, "#!/usr/bin/env cargo") is None  # not on the inherited PATH
    for line in (f"#!/usr/bin/env -S PATH={cargo.parent} cargo", f"#!/usr/bin/env -P {cargo.parent} cargo"):
        hint = _hint(layout, line)
        assert hint is not None and _suggested(hint) == [_real(cargo.parent)]


@pytest.mark.parametrize(
    "line",
    [
        "#!/bin/sh",
        "#!/usr/bin/env sh",
        "#!/usr/bin/env -S sh -e",
        "#!",
        "#!/usr/bin/env",
        "#!/usr/bin/env -i",
        "#!/usr/bin/env -S",
        "#!relative/cargo",
        "echo no shebang",
    ],
)
def test_no_hint_without_an_interpreter_under_a_home(layout: dict[str, Path], cargo: Path, line: str) -> None:
    assert _hint(layout, line) is None


def test_no_hint_once_a_grant_covers_the_interpreter(layout: dict[str, Path], cargo: Path) -> None:
    assert _hint(layout, "#!/usr/bin/env cargo", read=[str(cargo.parent)]) is None
    assert _hint(layout, "#!/usr/bin/env cargo", read=[str(cargo)]) is None


def test_hint_offers_only_presets_that_cover_the_interpreter(
    layout: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    node = _executable(layout["home"] / ".nvm" / "versions" / "node" / "v22.0.0" / "bin" / "node", "#!/bin/sh\n")
    monkeypatch.setenv("PATH", os.pathsep.join([str(node.parent), "/usr/bin", "/bin"]))
    hint = _hint(layout, "#!/usr/bin/env node")
    assert hint is not None
    assert hint.endswith(f"pass --preset claude-code, --preset codex or --allow-read {_real(node.parent)}")
    assert _hint(layout, "#!/usr/bin/env node", preset="codex") is None


def test_hint_points_at_a_virtual_environment_under_a_home(layout: dict[str, Path]) -> None:
    venv = layout["home"] / ".local" / "share" / "pipx" / "venvs" / "tool"
    (venv / "bin").mkdir(parents=True)
    (venv / "pyvenv.cfg").write_text("home = /usr/bin\n")
    python = venv / "bin" / "python"
    python.symlink_to("/bin/sh")  # a real interpreter outside every home
    hint = _hint(layout, f"#!{python}")
    assert hint is not None and _suggested(hint) == [str(venv)]


def test_hint_escapes_control_characters_in_file_names(layout: dict[str, Path], cargo: Path) -> None:
    # A symlink planted in the workspace by an earlier session, named to drive the terminal.
    link = layout["ws"] / "bin" / "\x1b]0;owned\x07cargo"
    link.parent.mkdir()
    link.symlink_to(cargo)
    hint = _hint(layout, f"#!{link}")
    assert hint is not None and hint.isprintable()
    assert "\\x1b]0;owned\\x07cargo" in hint and _suggested(hint) == [_real(cargo.parent)]


def test_hint_does_not_open_a_fifo(layout: dict[str, Path]) -> None:
    fifo = layout["ws"] / "fifo-tool"
    os.mkfifo(fifo)
    fifo.chmod(0o755)
    policy = _policy(layout["ws"], layout["home"])
    assert interpreter_hint(str(fifo), (str(layout["home"]),), policy) is None


# --- the trampoline needs no interpreter grant (Linux) -----------------------


def _without(roots: list[str], excluded: list[str]) -> list[str]:
    """Paths that cover ``roots`` except ``excluded``; containment by inode identity."""
    chains = [set(ancestry(path)) for path in excluded]
    excluded_ids = {ancestry(path)[0] for path in excluded}
    paths: list[str] = []

    def walk(path: str) -> None:
        if os.path.islink(path) or not os.path.exists(path):
            return
        st = os.stat(path)
        ident = (st.st_dev, st.st_ino)
        if ident in excluded_ids:
            return
        if any(ident in chain for chain in chains):
            try:
                names = sorted(os.listdir(path))
            except PermissionError:  # siblings we cannot list stay ungranted: narrower, never wider
                return
            for name in names:
                walk(os.path.join(path, name))
        else:
            paths.append(path)

    for root in roots:
        walk(root)
    return paths


@needs_landlock
def test_trampoline_reads_nothing_of_its_interpreter_once_restricted(layout: dict[str, Path]) -> None:
    """Why ``run`` grants no interpreter on Linux: once restricted, the trampoline opens /proc/self/status only."""
    probe = subprocess.run(
        [
            launcher.interpreter(),
            "-I",
            "-S",
            "-c",
            "import os, _ctypes; print(os.path.dirname(os.__file__)); "
            "print(os.path.dirname(getattr(_ctypes, '__file__', os.__file__)))",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    stdlib, extensions = probe.stdout.splitlines()
    readme = layout["ws"] / "README.md"
    readme.write_text("workspace\n")
    policy = _policy(layout["ws"], layout["home"], runtime=_without(list(SYSTEM_READ_EXEC), [stdlib, extensions]))
    env = {"PATH": "/usr/bin:/bin", "HOME": str(layout["home"]), "LC_ALL": "C"}

    def run(argv: list[str]) -> launcher.Result:
        return launcher.run(launcher.session_launch(argv, policy), env=env, cwd=str(layout["ws"]))

    # Not vacuous: the interpreter's own standard library is unreadable under this policy.
    blocked = run(["/bin/cat", os.path.join(stdlib, "os.py")])
    assert blocked.status.get("ok") and blocked.returncode != 0 and blocked.stdout == b""
    result = run(["/bin/cat", str(readme)])
    assert result.status.get("ok"), result.status
    assert result.status.get("seccomp") and result.status["caps"]["CapEff"] is not None
    assert result.returncode == 0 and result.stdout == b"workspace\n"


# --- end to end through the real CLI -------------------------------------------


@pytest.fixture
def box(tmp_path: Path) -> dict[str, Any]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    token = "B60-CANARY-cargo-" + secrets.token_hex(8)
    credentials = home / ".cargo" / "credentials.toml"
    credentials.parent.mkdir()
    credentials.write_text(f'[registry]\ntoken = "{token}"\n')
    credentials.chmod(0o600)
    cargo = _executable(
        home / ".cargo" / "bin" / "cargo", f"#!/bin/sh\necho cargo ran\ncat {shlex.quote(str(credentials))}\n"
    )
    agent = _executable(
        home / ".cargo" / "bin" / "agent-tool",
        "#!/bin/sh\necho agent-tool ran\n"
        f"cat {shlex.quote(str(credentials))} || echo credentials: denied\n"
        f"cat {shlex.quote(str(cargo))} || echo sibling: denied\n",
    )
    ws = tmp_path / "ws"
    _executable(ws / "bin" / "setup-tool", "#!/usr/bin/env cargo\n")
    env = {
        **os.environ,
        "HOME": str(home),
        "PATH": os.pathsep.join([str(ws / "bin"), str(cargo.parent), "/usr/bin", "/bin"]),
        "PYTHONPATH": str(ROOT / "01_KISH_ENGINE"),
    }
    journal = tmp_path / "state" / "journal.db"
    return {"home": home, "ws": ws, "cargo": cargo, "agent": agent, "token": token, "env": env, "journal": journal}


def _run(box: dict[str, Any], *command: str, options: tuple[str, ...] = ()) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", "run", "--allow-root"]
        + ["--journal", str(box["journal"]), *options, "--", *command],
        env=box["env"],
        cwd=str(box["ws"]),
        capture_output=True,
        text=True,
        timeout=120,
    )


@needs_backend
def test_shebang_naming_a_tool_under_home_grants_none_of_it(box: dict[str, Any]) -> None:
    dry = _run(box, "setup-tool", options=("--dry-run",))
    assert dry.returncode == 0, dry.stderr
    cargo_dirs = {str(box["home"] / ".cargo"), _real(box["home"] / ".cargo")}
    granted = [grant["path"] for grant in json.loads(dry.stdout)["grants"]]
    assert not [path for path in granted for d in cargo_dirs if path == d or path.startswith(d + os.sep)]
    assert f"babylon60 run: setup-tool starts {box['cargo']} {HINT}" in dry.stderr
    assert f"--allow-read {_real(box['cargo'].parent)}" in dry.stderr
    ran = _run(box, "setup-tool")
    assert ran.returncode != 0 and "cargo ran" not in ran.stdout
    assert box["token"] not in ran.stdout + ran.stderr


@needs_backend
def test_granting_the_whole_prefix_is_what_exposes_the_credentials(box: dict[str, Any]) -> None:
    """Control: the grant the shebang used to add hands the canary to any script."""
    ran = _run(box, "setup-tool", options=("--allow-read", str(box["home"] / ".cargo")))
    assert ran.returncode == 0 and "cargo ran" in ran.stdout, ran.stderr
    assert box["token"] in ran.stdout


@needs_backend
def test_hinted_grant_runs_the_interpreter_without_its_credentials(box: dict[str, Any]) -> None:
    ran = _run(box, "setup-tool", options=("--allow-read", str(box["cargo"].parent)))
    assert "cargo ran" in ran.stdout, ran.stderr
    assert box["token"] not in ran.stdout + ran.stderr
    assert HINT not in ran.stderr


@needs_backend
def test_executable_under_home_runs_but_its_siblings_stay_unreadable(box: dict[str, Any]) -> None:
    dry = _run(box, "agent-tool", options=("--dry-run",))
    assert dry.returncode == 0, dry.stderr
    runtime = [
        (g["path"], g["access"], g["is_dir"]) for g in json.loads(dry.stdout)["grants"] if g["origin"] == "runtime"
    ]
    trampoline = [(launcher.interpreter_prefix(), "ro", True)] if sys.platform == "darwin" else []
    assert runtime == [*trampoline, (os.path.realpath(box["agent"]), "ro", False)]
    ran = _run(box, "agent-tool")
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.splitlines() == ["agent-tool ran", "credentials: denied", "sibling: denied"]
    assert box["token"] not in ran.stdout + ran.stderr
    assert HINT not in ran.stderr
