"""Handlers for ``babylon60 run``, ``babylon60 demo`` and ``babylon60 log``.

Exit codes: 0 success (demo: every counted attempt blocked); 1 demo FALSIFIED,
journal chain broken or ``log --expect-head`` digest absent; 2 demo INCONCLUSIVE,
usage error or a malformed ``--expect-head``; 3 no confinement backend, a refused
policy or an unusable journal; 126 the trampoline refused to start the target;
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
import tempfile
from typing import Any

from blake3 import blake3

from babylon60.confine.policy import PRESETS, Identity, Policy, ancestry

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


def trampoline_grants() -> list[str]:
    """What the trampoline itself must read while confined: nothing on Linux, its interpreter on macOS.

    Landlock is applied by the trampoline after its imports; from then on it
    opens only ``/proc/self/status`` before ``execv`` (tests/test_confine_grants.py),
    so the agent gets no access to the launcher's Python. ``sandbox-exec``
    applies the Seatbelt profile before the interpreter starts, so an interpreter
    under a home directory (uv, pyenv, conda) must stay readable there.
    """
    from babylon60.confine import launcher

    return [launcher.interpreter_prefix()] if sys.platform == "darwin" else []


def executable_grants(executable: str, homes: tuple[str, ...]) -> list[str]:
    """Read/exec grant for the command itself when its file lives under a home directory.

    Only that file is granted: never its directory or install prefix, and nothing
    derived from its contents (a ``#!/usr/bin/env cargo`` line would otherwise
    expose ``~/.cargo/credentials.toml``). Install prefixes under a home come only
    from ``--preset`` or ``--allow-read``. ``realpath`` only locates the file;
    containment is decided by inode identity and ``build_policy`` checks the grant
    again with its guards.
    """
    real = os.path.realpath(executable)
    if not os.path.isfile(real) or not _home_ids(homes).intersection(_chain(real)[1:]):
        return []
    return [real]


def executable_links(executable: str, homes: tuple[str, ...]) -> list[str]:
    """Symbolic links under a home on the way from the command's path to its file.

    Seatbelt (macOS) checks following a link as a read of the link, so ``run -- claude``
    through ``~/.local/bin/claude`` needs that one link readable; Landlock does not
    mediate it. A link only reveals its target path. ``build_policy`` refuses links
    inside protected paths.
    """
    home_ids = _home_ids(homes)
    links: list[str] = []
    path = executable
    for _ in range(40):  # the kernel's own limit on nested links
        if not os.path.islink(path):
            break
        if home_ids.intersection(_chain(os.path.dirname(path) or "/")):
            links.append(path)
        target = os.readlink(path)
        path = target if os.path.isabs(target) else os.path.join(os.path.dirname(path), target)
    return links


def interpreter_hint(executable: str, homes: tuple[str, ...], policy: Policy) -> str | None:
    """One line for stderr when a script's ``#!`` interpreter is under a home directory and not granted.

    This is the only reader of the ``#!`` line and it never adds a grant. It
    suggests the presets that would cover the interpreter and ``--allow-read`` for
    the directory that holds it (or its virtual environment), never a wider prefix.
    """
    named = _script_interpreter(executable)
    if named is None:
        return None
    home_ids = _home_ids(homes)
    granted = {(grant.dev, grant.ino) for grant in policy.grants if grant.access in ("ro", "rw")}
    venv = os.path.dirname(os.path.dirname(named))
    needed = [venv] if os.path.isfile(os.path.join(venv, "pyvenv.cfg")) else []
    presets: set[str] | None = None
    allow: list[str] = []
    for path in [*needed, os.path.realpath(named)]:
        chain = _chain(path)
        if not chain or granted.intersection(chain) or not home_ids.intersection(chain[1:]):
            continue
        covering = _covering_presets(chain, homes[0]) if homes else set()
        presets = covering if presets is None else presets & covering
        allow.append(path if os.path.isdir(path) or chain[1] in home_ids else os.path.dirname(path))
    if not allow:
        return None
    options = [f"--preset {name}" for name in sorted(presets or ())]
    options.append(" ".join(f"--allow-read {path}" for path in dict.fromkeys(allow)))
    choice = " or ".join([", ".join(options[:-1]), options[-1]] if len(options) > 1 else options)
    hint = (
        f"{os.path.basename(executable)} starts {named} (its #! interpreter), which is under a home "
        f"directory and not granted; to allow it, pass {choice}"
    )
    # A #! line or a planted symlink can carry terminal control sequences: never print them raw.
    return "".join(char if char.isprintable() else repr(char)[1:-1] for char in hint)


def _home_ids(homes: tuple[str, ...]) -> set[Identity]:
    ids: set[Identity] = set()
    for home in homes:
        try:
            st = os.stat(home)
        except OSError:
            continue
        ids.add((st.st_dev, st.st_ino))
    return ids


def _chain(path: str) -> list[Identity]:
    try:
        return ancestry(path)
    except OSError:
        return []


def _covering_presets(chain: list[Identity], home: str) -> set[str]:
    """Presets with a grant (expanded in ``home`` as ``build_policy`` does) that contains the path of ``chain``."""
    names: set[str] = set()
    for name, spec in PRESETS.items():
        for item in (*spec["read"], *spec["write"]):
            path = home + item[1:]
            if os.path.islink(path):  # build_policy skips symlinked grants
                continue
            try:
                st = os.stat(path)
            except OSError:
                continue
            if (st.st_dev, st.st_ino) in chain:
                names.add(name)
    return names


def _script_interpreter(executable: str) -> str | None:
    """Absolute path of the interpreter a ``#!`` line names, ``env`` lookups included (hint only)."""
    if not os.path.isfile(executable):
        return None
    try:
        fd = os.open(executable, os.O_RDONLY | os.O_NONBLOCK | os.O_NOCTTY | os.O_CLOEXEC)
        try:
            head = os.read(fd, 256)
        finally:
            os.close(fd)
    except OSError:
        return None
    if not head.startswith(b"#!"):
        return None
    words = head[2:].split(b"\n", 1)[0].decode("utf-8", "replace").split(None, 1)
    if not words:
        return None
    interpreter = words[0]
    if os.path.basename(interpreter) == "env":
        command, search = _env_command(words[1] if len(words) > 1 else "")
        if command is None:
            return None
        if "/" not in command:
            found = shutil.which(command, path=search)
            return os.path.abspath(found) if found else None
        interpreter = command
    return interpreter if os.path.isabs(interpreter) else None


def _env_command(argument: str) -> tuple[str | None, str | None]:
    """The command ``env ARGUMENT`` runs and the PATH it searches (``None``: the inherited one).

    ``-S``/``--split-string`` takes the rest of the line (Linux passes a ``#!``
    argument as one string) and splits it with quotes and ``${NAME}``. Also
    handled: ``-u NAME``, ``-C DIR``, ``-a ARG``, BSD ``-P PATH``, flags such as
    ``-i`` or ``-v``, ``NAME=VALUE`` assignments (``PATH=`` changes the search), ``--``.
    """
    words = argument.split()
    search: str | None = None
    while words:
        word = words.pop(0)
        if word == "--":
            break
        if word == "-" or ("=" in word and not word.startswith("-")):
            if word.startswith("PATH="):
                search = word[5:]
            continue
        if not word.startswith("-"):
            return word, search
        split: str | None = None
        if word.startswith("--"):
            name, has_value, value = word[2:].partition("=")
            if name == "split-string":
                split = value
            elif name in ("unset", "chdir", "argv0") and not has_value and words:
                words.pop(0)
        else:
            for index, flag in enumerate(word[1:], start=2):
                if flag == "S":
                    split = word[index:]
                elif flag in "uCaP":
                    value = word[index:] or (words.pop(0) if words else "")
                    if flag == "P":
                        search = value
                else:
                    continue
                break
        if split is not None:
            words = _env_words(" ".join([split, *words]))
    return (words[0], search) if words else (None, search)


def _env_words(text: str) -> list[str]:
    """Split like ``env -S`` (quotes, backslashes, ``${NAME}``), closely enough for a hint."""
    import shlex

    try:
        return shlex.split(os.path.expandvars(text))
    except ValueError:
        return text.split()


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
    from babylon60.confine import launcher, metadata
    from babylon60.confine.journal import ConfineJournal, JournalError
    from babylon60.confine.policy import PolicyError, build_policy, default_homes
    from babylon60.confine.terminals import session_ttys

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
        try:
            ConfineJournal(journal_path).close()
        except JournalError as exc:
            print(f"babylon60 run: {exc}", file=sys.stderr)
            return EXIT_UNAVAILABLE
        links = os.stat(journal_path).st_nlink
        if links > 1:
            print(
                f"babylon60 run: the journal has {links} hard links, so another path to it could be writable "
                f"inside the sandbox: {journal_path}. Use a fresh --journal path.",
                file=sys.stderr,
            )
            return EXIT_UNAVAILABLE
    # Each session gets its own temporary directory instead of the shared /tmp.
    private_tmp = None if args.dry_run else tempfile.mkdtemp(prefix="babylon60-run-")
    try:
        try:
            policy = build_policy(
                workspace,
                homes=homes,
                read=args.allow_read,
                write=args.allow_write,
                runtime=[*trampoline_grants(), *executable_grants(executable, homes)],
                preset=args.preset,
                private_tmp=private_tmp,
                self_paths=[str(journal_path), sys.prefix, package_dir],
                ttys=session_ttys(),
                allow_ptys=args.allow_ptys,
                links=executable_links(executable, homes),
            )
        except PolicyError as exc:
            print(f"babylon60 run: {exc}", file=sys.stderr)
            return EXIT_UNAVAILABLE
        for skipped in policy.skipped:
            if ": " in skipped:  # a guard refused it, as opposed to a missing path or a symlink
                print(f"babylon60 run: not granted: {skipped}", file=sys.stderr)
        for warning in policy.warnings:
            print(f"babylon60 run: warning: {warning}", file=sys.stderr)
        hint = interpreter_hint(executable, homes, policy)
        if hint:
            print(f"babylon60 run: {hint}", file=sys.stderr)
        if args.dry_run:
            document = {"backend": launcher.backend(), "policy_digest": policy.digest(), **policy.as_dict()}
            document["tmpdir"] = "a private directory, created for each run and removed afterwards"
            print(json.dumps(document, indent=2))
            return 0
        assert private_tmp is not None
        env = dict(os.environ)
        if not args.keep_agent_sockets:
            for name in AGENT_SOCKET_VARS:
                env.pop(name, None)
        env["TMPDIR"] = private_tmp
        launch = launcher.session_launch([executable, *command[1:]], policy, unix_sockets=args.allow_unix_sockets)
        before = hook_digests(args.preset, workspace, homes[0])
        meta_before = metadata.snapshot(policy.homes, policy.protected)
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
                    "allow_ptys": policy.allow_ptys,
                    "policy_warnings": len(policy.warnings),
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
                if launch.new_session:
                    # The agent left the terminal session: relay Ctrl-C, hangups, resizes and job control to it.
                    with launcher.forward_signals(process):
                        returncode = process.wait()
                else:
                    returncode = process.wait()  # same session: the terminal signals the agent directly
            finally:
                signal.signal(signal.SIGINT, previous)
            after = hook_digests(args.preset, workspace, homes[0])
            changed = sorted(name for name in before if before[name] != after[name])
            meta_after = metadata.snapshot(policy.homes, policy.protected)
            meta_changed = metadata.changes(meta_before, meta_after)
            journal.append(
                "run_end",
                {
                    "exit_code": returncode,
                    "hooks_changed": changed,
                    "metadata_changed": meta_changed,
                    "metadata_truncated": [meta_after.display(path) for path in meta_after.truncated],
                    "landlock_abi": status.get("landlock_abi"),
                    "caps_dropped": status.get("caps_dropped"),
                },
            )
        if changed:
            print(
                "babylon60 run: the agent changed files that run outside the sandbox later: " + ", ".join(changed),
                file=sys.stderr,
            )
        if meta_changed:
            print(
                "babylon60 run: permissions or ownership changed on the home or protected paths during the session "
                "(Landlock does not mediate metadata):",
                file=sys.stderr,
            )
            for line in meta_changed:
                print(f"  {line}", file=sys.stderr)
        return returncode
    finally:
        if private_tmp is not None:
            shutil.rmtree(private_tmp, ignore_errors=True)


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
