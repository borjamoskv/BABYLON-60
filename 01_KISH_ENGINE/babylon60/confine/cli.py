"""Handlers for ``babylon60 run``, ``babylon60 demo`` and ``babylon60 log``.

Exit codes: 0 success (demo: every counted attempt blocked); 1 demo FALSIFIED or
journal chain broken; 2 demo INCONCLUSIVE or usage error; 3 no confinement
backend or a refused policy; 126 the trampoline refused to start the target;
127 command not found; otherwise the confined command's own exit code.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import sys
from typing import Any

from blake3 import blake3

EXIT_USAGE, EXIT_UNAVAILABLE, EXIT_REFUSED, EXIT_NOT_FOUND = 2, 3, 126, 127
AGENT_SOCKET_VARS = ("SSH_AUTH_SOCK", "GPG_AGENT_INFO")
# Files that, if an agent edits them, run code later outside the sandbox.
HOME_HOOKS = {
    "claude-code": ("~/.claude/settings.json", "~/.claude/settings.local.json", "~/.claude.json"),
    "codex": ("~/.codex/config.toml",),
}
WORKSPACE_HOOKS = (
    ".git/config",
    ".git/hooks",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".mcp.json",
    ".codex/config.toml",
)


def default_journal() -> Path:
    base = Path(os.getenv("BABYLON_HOME", str(Path.home() / ".babylon60")))
    return base / "confine" / "journal.db"


def _strip_separator(command: list[str]) -> list[str]:
    """``argparse.REMAINDER`` keeps a leading ``--`` on Python 3.11-3.13; drop exactly one."""
    return command[1:] if command[:1] == ["--"] else command


def _shebang_interpreter(executable: str) -> str | None:
    try:
        with open(executable, "rb") as handle:
            first = handle.readline(256)
    except OSError:
        return None
    if not first.startswith(b"#!"):
        return None
    parts = first[2:].decode("utf-8", "replace").split()
    if not parts:
        return None
    if os.path.basename(parts[0]) == "env" and len(parts) > 1:
        return shutil.which(parts[-1])
    return parts[0]


def install_prefixes(executable: str, homes: tuple[str, ...]) -> list[str]:
    """Read/exec grants for an agent installed under a home directory.

    ``realpath`` only locates where the binary lives; the resulting grant is
    still checked by inode identity in ``build_policy`` and skipped if a guard fails.
    """
    prefixes: list[str] = []
    for path in (executable, _shebang_interpreter(executable)):
        if not path:
            continue
        real = os.path.realpath(path)
        if any(real.startswith(home.rstrip("/") + "/") for home in homes):
            prefixes.append(os.path.dirname(os.path.dirname(real)))
    return prefixes


def _digest_tree(path: Path) -> str | None:
    if not path.exists():
        return None
    hasher = blake3()
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    for file in files:
        try:
            hasher.update(str(file.relative_to(path) if file != path else ".").encode() + b"\x00" + file.read_bytes())
        except OSError:
            hasher.update(str(file).encode() + b"\x00<unreadable>")
    return hasher.hexdigest()


def hook_digests(preset: str | None, workspace: Path, home: str) -> dict[str, str | None]:
    targets = {rel: workspace / rel for rel in WORKSPACE_HOOKS}
    for item in HOME_HOOKS.get(preset or "", ()):
        targets[item] = Path(home + item[1:])
    return {name: _digest_tree(path) for name, path in targets.items()}


def run_command(args: argparse.Namespace) -> int:
    from babylon60.confine import launcher
    from babylon60.confine.journal import ConfineJournal
    from babylon60.confine.policy import PolicyError, build_policy, default_homes

    command = _strip_separator(list(args.command))
    if not command:
        print("babylon60 run: missing command after --", file=sys.stderr)
        return EXIT_USAGE
    if os.geteuid() == 0 and not args.allow_root:
        print(
            "babylon60 run: refusing to run as root. uid 0 keeps owner access to root-owned files inside "
            "granted system paths (for example /etc/shadow); pass --allow-root to accept that limit.",
            file=sys.stderr,
        )
        return EXIT_UNAVAILABLE
    if launcher.backend() == "none":
        print("babylon60 run: no confinement backend (Linux Landlock ABI >= 3 or macOS Seatbelt).", file=sys.stderr)
        return EXIT_UNAVAILABLE
    executable = shutil.which(command[0])
    if executable is None:
        print(f"babylon60 run: command not found: {command[0]}", file=sys.stderr)
        return EXIT_NOT_FOUND
    executable = os.path.abspath(executable)
    homes = default_homes()
    journal_path = Path(args.journal) if args.journal else default_journal()
    workspace = Path(args.workspace or os.getcwd()).absolute()
    package_dir = str(Path(__file__).resolve().parents[1])
    try:
        policy = build_policy(
            workspace,
            homes=homes,
            read=args.allow_read,
            write=args.allow_write,
            runtime=[launcher.interpreter_prefix(), *install_prefixes(executable, homes)],
            preset=args.preset,
            self_paths=[str(journal_path), sys.prefix, package_dir],
        )
    except PolicyError as exc:
        print(f"babylon60 run: {exc}", file=sys.stderr)
        return EXIT_UNAVAILABLE
    for skipped in policy.skipped:
        if ": " in skipped:  # a guard refused it, as opposed to a missing path or a symlink
            print(f"babylon60 run: not granted: {skipped}", file=sys.stderr)
    if args.dry_run:
        print(
            json.dumps({"backend": launcher.backend(), "policy_digest": policy.digest(), **policy.as_dict()}, indent=2)
        )
        return 0
    env = dict(os.environ)
    if not args.keep_agent_sockets:
        for name in AGENT_SOCKET_VARS:
            env.pop(name, None)
    seccomp = sys.platform.startswith("linux") and sys.stdin.isatty()
    before = hook_digests(args.preset, workspace, homes[0])
    with ConfineJournal(journal_path) as journal:
        journal.append(
            "run_start",
            {
                "backend": launcher.backend(),
                "policy_digest": policy.digest(),
                "preset": args.preset,
                "command": os.path.basename(executable),
                "argc": len(command),
                "seccomp": seccomp,
            },
        )
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            process, status = launcher.spawn(
                launcher.Launch([executable, *command[1:]], policy, seccomp=seccomp),
                env=env,
                cwd=str(workspace),
                stdin=None,
                stdout=None,
                stderr=None,
            )
            if not status.get("ok"):
                process.wait()
                journal.append("run_refused", {"error": status.get("error", "unknown")})
                print(f"babylon60 run: confinement refused: {status.get('error')}", file=sys.stderr)
                return EXIT_REFUSED
            returncode = process.wait()
        finally:
            signal.signal(signal.SIGINT, previous)
        after = hook_digests(args.preset, workspace, homes[0])
        changed = sorted(name for name in before if before[name] != after[name])
        journal.append(
            "run_end",
            {
                "exit_code": returncode,
                "hooks_changed": changed,
                "landlock_abi": status.get("landlock_abi"),
                "caps_dropped": status.get("caps_dropped"),
            },
        )
    if changed:
        print(
            "babylon60 run: the agent changed files that run outside the sandbox later: " + ", ".join(changed),
            file=sys.stderr,
        )
    return returncode


def demo_command(args: argparse.Namespace) -> int:
    from babylon60.confine.demo import check_evidence, run_demo
    from babylon60.confine.launcher import ConfinementUnavailable

    if args.check:
        result = check_evidence(json.loads(Path(args.check).read_text(encoding="utf-8")))
        print(f"self digest: {'ok' if result['self_digest_ok'] else 'MISMATCH'}")
        print(
            f"confinement code: {'same as this installation' if result['code_matches_installation'] else 'differs from this installation'}"
        )
        return 0 if result["self_digest_ok"] else 1
    try:
        report = run_demo(
            journal_path=Path(args.journal) if args.journal else default_journal(),
            repeat=max(1, args.repeat),
            workers=max(1, args.workers),
        )
    except ConfinementUnavailable as exc:
        print(f"babylon60 demo: {exc}", file=sys.stderr)
        return EXIT_UNAVAILABLE
    print("\n".join(report.transcript))
    text = json.dumps(report.document, indent=2, ensure_ascii=False) + "\n"
    if args.json == "-":
        print(text, end="")
    elif args.json:
        Path(args.json).write_text(text, encoding="utf-8")
    if args.evidence_dir:
        plat = report.document["platform"]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        name = f"demo-{plat['system'].lower()}-{plat['machine']}-{stamp}.json"
        target = Path(args.evidence_dir) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"evidence: {target}")
    return report.exit_code


def log_command(args: argparse.Namespace) -> int:
    from babylon60.confine.journal import ConfineJournal

    path = Path(args.journal) if args.journal else default_journal()
    if not path.exists():
        print(f"babylon60 log: no journal at {path}")
        return 0
    with ConfineJournal(path) as journal:
        check = journal.verify()
        entries = journal.entries(limit=args.tail)
    if args.json:
        payload: dict[str, Any] = {
            "verified": check.ok,
            "events": check.events,
            "head": check.head,
            "first_invalid_seq": check.first_invalid_seq,
            "reason": check.reason,
            "entries": [entry.__dict__ for entry in entries],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for entry in entries:
            summary = ", ".join(f"{k}={v}" for k, v in entry.body.items() if not isinstance(v, (dict, list)))[:120]
            print(f"#{entry.seq:<6} {entry.kind:<13} blake3:{entry.digest[:12]}…  {summary}")
        state = "verified" if check.ok else f"BROKEN at #{check.first_invalid_seq}: {check.reason}"
        print(f"chain: {check.events} events, {state}, head blake3:{check.head[:16]}…")
    return 0 if check.ok else 1
