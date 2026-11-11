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
    # Protect the journal file itself: the ancestry of a symlink walks the link's directory, not the target's.
    journal_path = Path(os.path.realpath(journal_path))
    if not args.dry_run:
        # The guard refuses write grants only over paths that exist: create the journal
        # (directories 0700, file 0600) first, so a new one never sits inside a writable grant.
        from babylon60.confine.journal import JournalError

        try:
            ConfineJournal(journal_path).close()
        except JournalError as exc:
            print(f"babylon60 run: {exc}", file=sys.stderr)
            return EXIT_UNAVAILABLE
    try:
        policy = build_policy(
            workspace,
            homes=homes,
            read=args.allow_read,
            write=args.allow_write,
            runtime=[launcher.interpreter_prefix(), *install_prefixes(executable, homes)],
            preset=args.preset,
            self_paths=[str(journal_path), sys.prefix, package_dir],
            allow_ptys=args.allow_ptys,
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
    launch = launcher.session_launch([executable, *command[1:]], policy, unix_sockets=args.allow_unix_sockets)
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
                "seccomp": launch.seccomp,
                "unix_sockets": launch.unix_sockets,
                "new_session": launch.new_session,
            },
        )
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            process, status = launcher.spawn(
                launch,
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
    """Exit 0 when the chain verifies (and contains ``--expect-head``), 1 otherwise, 2 for a malformed head."""
    from babylon60.confine.journal import ConfineJournal, JournalError

    path = Path(args.journal) if args.journal else default_journal()
    expected: str | None = None
    if args.expect_head is not None:
        # The head as ``log`` prints it, with or without ``blake3:``, in any case; never a shortened one.
        expected = args.expect_head.strip().lower().removeprefix("blake3:")
        if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
            print("babylon60 log: --expect-head needs a full head digest (64 hex digits)", file=sys.stderr)
            return EXIT_USAGE

    def expected_report(seq: int | None, after: int | None) -> dict[str, Any] | None:
        if expected is None:
            return None
        return {"digest": expected, "found": seq is not None, "seq": seq, "events_after": after}

    if not path.exists():
        if args.json:
            missing: dict[str, Any] = {
                "verified": expected is None,
                "chain_intact": True,
                "events": 0,
                "head": None,
                "first_invalid_seq": None,
                "reason": f"no journal at {path}",
                "expected_head": expected_report(None, None),
                "entries": [],
            }
            print(json.dumps(missing, indent=2, ensure_ascii=False))
        else:
            print(f"babylon60 log: no journal at {path}")
            if expected is not None:
                print(f"expected head blake3:{expected}: NOT FOUND, there is no journal")
        return 0 if expected is None else 1
    entries_error: str | None = None
    try:
        with ConfineJournal(path) as journal:
            check = journal.verify(expect_head=expected)
            try:
                entries = journal.entries(limit=args.tail)
            except JournalError as exc:
                entries, entries_error = [], str(exc)
    except JournalError as exc:
        print(f"babylon60 log: {exc}", file=sys.stderr)
        return 1
    if args.json:
        payload: dict[str, Any] = {
            "verified": check.ok,
            "chain_intact": check.chain_intact,
            "events": check.events,
            "head": check.head,
            "first_invalid_seq": check.first_invalid_seq,
            "reason": check.reason,
            "expected_head": expected_report(check.expected_seq, check.events_after_expected),
            "entries": [entry.__dict__ for entry in entries],
        }
        if entries_error:
            payload["entries_error"] = entries_error
        # repr() only for values a tampered row can hold that JSON cannot (blobs).
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=repr))
    else:
        for entry in entries:
            fields = entry.body.items() if isinstance(entry.body, dict) else ()
            summary = ", ".join(f"{k}={v}" for k, v in fields if not isinstance(v, (dict, list)))[:120]
            print(f"#{entry.seq!s:<6} {entry.kind!s:<13} blake3:{entry.digest!s:.12}…  {summary}")
        if entries_error:
            print(f"entries: {entries_error}")
        if check.chain_intact:
            print(f"chain: {check.events} events, verified, head blake3:{check.head}")
        else:
            where = "" if check.first_invalid_seq is None else f" at #{check.first_invalid_seq}"
            print(
                f"chain: {check.events} events, BROKEN{where}: {check.reason}; last verified head blake3:{check.head}"
            )
        if expected is not None:
            label = f"expected head blake3:{expected}"
            after = check.events_after_expected
            if check.expected_seq is None and check.chain_intact:
                print(
                    f"{label}: NOT FOUND, the journal was truncated, rolled back or replaced after it was published, "
                    "or the head is from another journal"
                )
            elif check.expected_seq is None:
                print(f"{label}: not found before the break")
            elif not check.chain_intact:
                print(f"{label}: found at #{check.expected_seq}, but the chain breaks after it")
            else:
                print(f"{label}: found at #{check.expected_seq}, followed by {after} event{'' if after == 1 else 's'}")
    return 0 if check.ok else 1
