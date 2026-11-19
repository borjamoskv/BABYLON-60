"""Command-line handlers for ``babylon60 run`` and ``babylon60 log``."""
# ruff: noqa: F401, F811

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import tempfile
from typing import Any

from babylon60.confine import gitconfig, launcher, metadata, persistence, shm, terminal_proxy, terminals
from babylon60.confine.journal import ConfineJournal
from babylon60.confine.persistence import printable
from babylon60.confine.policy import Policy, PolicyError, build_policy
from babylon60.confine._cli_env import (  # noqa: F401
    AGENT_CREDENTIALS,
    AGENT_SOCKET_VARS,
    CREDENTIAL_LAST_WORDS,
    CREDENTIAL_VARS,
    CREDENTIAL_WORDS,
    EXIT_NOT_FOUND,
    EXIT_REFUSED,
    EXIT_UNAVAILABLE,
    EXIT_USAGE,
    IMPORT_DIR_VAR,
    JOURNAL_NAMES,
    LABEL_CHARS,
    LANDLOCK_SCOPE_ABI,
    PASSWORD_WORDS,
    SHOWN_NAMES,
    URL_WITH_PASSWORD,
    WITHHELD_VAR,
    _T,
    _bounded,
    _chain,
    _covering_presets,
    _env_command,
    _env_words,
    _home_ids,
    _install_root,
    _script_interpreter,
    _shared_directory,
    _strip_separator,
    agent_environment,
    credential_like,
    default_journal,
    executable_grants,
    executable_links,
    interpreter_flags,
    interpreter_hint,
    launcher_paths,
    outside_grants_hint,
    password_in_value,
    private_tmp_environment,
    reexec_without_withheld,
    trampoline_grants,
    writable_import_paths,
)


class SessionChecks:
    """What ``run`` compares before and after a session: persistence material, home metadata and,
    on Linux, what is left in ``/dev/shm``.

    A check that fails is named in ``failed`` with its error and never keeps
    ``run_end`` out of the journal; everything it reports is printable text.
    """

    def __init__(self, policy: Policy, workspace: str, home: str | None) -> None:
        from babylon60.confine import metadata, shm

        self.policy, self.workspace, self.home = policy, workspace, home
        self.failed: list[str] = []
        self.report: persistence.Report | None = None
        self.metadata_changed: list[str] = []
        self.shm_changed: list[str] = []
        self.shm_unchecked: list[str] = []
        self.persistence_before = self._attempt("persistence", self._persistence)
        self.metadata_before = self._attempt("metadata", lambda: metadata.snapshot(policy.homes, policy.protected))
        shm_root = shm.granted(policy)
        self.shm_before = self._attempt("shm", lambda: shm.snapshot(shm_root)) if shm_root else None

    def _persistence(self, previous: persistence.Snapshot | None = None) -> persistence.Snapshot:
        return persistence.snapshot(self.policy, self.workspace, home=self.home, previous=previous)

    def _attempt(self, name: str, check: Callable[[], _T]) -> _T | None:
        try:
            return check()
        except Exception as exc:  # a failed check is reported, never fatal
            self.failed.append(printable(f"{name}: {type(exc).__name__}: {exc}")[:LABEL_CHARS])
            return None

    def finish(self, end: dict[str, Any]) -> None:
        """Compare again after the session and fill the ``run_end`` body ``end``."""
        from babylon60.confine import metadata, shm

        end.update(
            hooks_changed=[],
            instructions_changed=[],
            persistence_unchecked=[],
            metadata_changed=[],
            metadata_truncated=[],
            shm_changed=[],
            checks_failed=self.failed,
        )
        before = self.persistence_before
        after = self._attempt("persistence", lambda: self._persistence(before)) if before is not None else None
        if before is not None and after is not None:
            self.report = self._attempt("persistence", lambda: persistence.changes(before, after))
        if self.report is not None:
            end["hooks_changed"] = _bounded(self.report.code, JOURNAL_NAMES, self.report.ranks)
            end["instructions_changed"] = _bounded(self.report.instructions, JOURNAL_NAMES, self.report.ranks)
        shm_before = self.shm_before
        if shm_before is not None:
            shm_after = self._attempt("shm", lambda: shm.snapshot(shm_before.root))
            if shm_after is not None:
                self.shm_changed = shm.changes(shm_before, shm_after, os.geteuid())
                self.shm_unchecked = list(dict.fromkeys([*shm_before.unchecked, *shm_after.unchecked]))
                end["shm_changed"] = _bounded(self.shm_changed, JOURNAL_NAMES)
        end["persistence_unchecked"] = _bounded(self.unchecked(), JOURNAL_NAMES)
        meta_before = self.metadata_before
        if meta_before is not None:
            meta_after = self._attempt("metadata", lambda: metadata.snapshot(self.policy.homes, self.policy.protected))
            if meta_after is not None:
                self.metadata_changed = (
                    self._attempt("metadata", lambda: metadata.changes(meta_before, meta_after)) or []
                )
                end["metadata_changed"] = self.metadata_changed
                end["metadata_truncated"] = [meta_after.display(path) for path in meta_after.truncated]
        end["checks_failed"] = list(self.failed)

    def unchecked(self) -> list[str]:
        """What was not compared in full: persistence roots, then ``/dev/shm``."""
        return [*(self.report.unchecked if self.report is not None else ()), *self.shm_unchecked]

    def print_report(self) -> None:
        report = self.report
        if report is not None and report.code:
            print(
                "babylon60 run: the agent changed files that run outside the sandbox later: "
                + ", ".join(_bounded(report.code, SHOWN_NAMES, report.ranks)),
                file=sys.stderr,
            )
        if report is not None and report.instructions:
            print(
                "babylon60 run: the agent changed instructions that its later sessions read (prompts, not code): "
                + ", ".join(_bounded(report.instructions, SHOWN_NAMES, report.ranks)),
                file=sys.stderr,
            )
        if self.shm_changed:
            print(
                "babylon60 run: entries of /dev/shm owned by you were added, changed or removed during the session, "
                "by the agent or by another of your processes, and outlive it: "
                + ", ".join(_bounded(self.shm_changed, SHOWN_NAMES)),
                file=sys.stderr,
            )
        unchecked = self.unchecked()
        if unchecked:
            print(
                "babylon60 run: warning: not compared in full, changes there may be missing: "
                + ", ".join(_bounded(unchecked, SHOWN_NAMES)),
                file=sys.stderr,
            )
        if self.metadata_changed:
            print(
                "babylon60 run: permissions or ownership changed on the home or protected paths during the session "
                "(Landlock does not mediate metadata):",
                file=sys.stderr,
            )
            for line in self.metadata_changed:
                print(f"  {line}", file=sys.stderr)
        for failure in self.failed:
            print(
                f"babylon60 run: warning: a check did not complete, its changes are unknown: {failure}", file=sys.stderr
            )


def launch_warnings(backend: str, *, clipboard: bool) -> list[str]:
    """What a launch flag opens beyond the policy, which ``Policy.warnings`` already names.

    ``--allow-clipboard`` only changes the Seatbelt profile; elsewhere it opens nothing to warn about.
    """
    from babylon60.confine.seatbelt import CLIPBOARD_WARNING

    return [CLIPBOARD_WARNING] if clipboard and backend == "seatbelt" else []


def journal_run_end(journal: ConfineJournal, end: dict[str, Any]) -> None:
    """Append ``run_end``; if the journal refuses that body, append its exit code and the reason instead."""
    try:
        journal.append("run_end", end)
    except ValueError as exc:  # JournalError: not canonical, or too large
        minimal = {key: end.get(key) for key in ("exit_code", "landlock_abi", "caps_dropped", "ended_by", "leftovers")}
        minimal["checks_failed"] = [printable(f"journal: {exc}")[:LABEL_CHARS]]
        journal.append("run_end", minimal)


def run_command(args: argparse.Namespace) -> int:
    from babylon60.confine import launcher
    from babylon60.confine.journal import ConfineJournal, JournalError
    from babylon60.confine.policy import PolicyError, build_policy, default_homes
    from babylon60.confine.terminal_proxy import PrivateTerminal

    command = _strip_separator(list(args.command))
    if not command:
        print("babylon60 run: missing command after --", file=sys.stderr)
        return EXIT_USAGE
    pass_env = list(getattr(args, "pass_env", None) or [])
    if any(not name or "=" in name for name in pass_env):
        print("babylon60 run: --pass-env takes a variable name, never NAME=VALUE", file=sys.stderr)
        return EXIT_USAGE
    reexec_without_withheld(args, pass_env)
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
    terminal: PrivateTerminal | None = None
    try:
        if not args.dry_run:
            try:  # a terminal on 0-2 reaches the agent only through a private pseudo-terminal (terminal_proxy)
                terminal = PrivateTerminal.open()
            except OSError as exc:
                print(f"babylon60 run: cannot allocate a private terminal for the agent: {exc}", file=sys.stderr)
                return EXIT_UNAVAILABLE
        try:
            policy = build_policy(
                workspace,
                homes=homes,
                read=args.allow_read,
                write=args.allow_write,
                runtime=[*trampoline_grants(), *executable_grants(executable, homes)],
                preset=args.preset,
                private_tmp=private_tmp,
                self_paths=launcher_paths(str(journal_path), package_dir),
                ttys=terminal.ttys if terminal else [],
                allow_ptys=args.allow_ptys,
                links=executable_links(executable, homes),
                git_env=os.environ,  # the agent inherits HOME and XDG_CONFIG_HOME
            )
        except PolicyError as exc:
            print(f"babylon60 run: {exc}", file=sys.stderr)
            return EXIT_UNAVAILABLE
        # Paths named by a git config file may hold terminal control sequences: never printed raw.
        for skipped in policy.skipped:
            if ": " in skipped:  # a guard refused it, as opposed to a missing path or a symlink
                print(f"babylon60 run: not granted: {printable(skipped)}", file=sys.stderr)
        clipboard = bool(getattr(args, "allow_clipboard", False))
        for warning in [*policy.warnings, *launch_warnings(launcher.backend(), clipboard=clipboard)]:
            print(f"babylon60 run: warning: {printable(warning)}", file=sys.stderr)
        hint = interpreter_hint(executable, homes, policy)
        if hint:
            print(f"babylon60 run: {hint}", file=sys.stderr)
        outside = outside_grants_hint(executable, homes, policy) if launcher.backend() == "landlock" else None
        if outside:
            print(f"babylon60 run: {outside}", file=sys.stderr)
        first = os.environ.get(IMPORT_DIR_VAR)  # set by the re-exec: where the first launcher imported from
        unsafe = writable_import_paths(policy, [*sys.path, *([first] if first else [])])
        if unsafe:
            print(
                "babylon60 run: refusing: babylon60 imports its Python modules from "
                f"{', '.join(printable(entry) for entry in unsafe)}, which the agent could write; a module "
                "left there would run outside the sandbox the next time babylon60 starts. Start it with "
                "the babylon60 command or python -P -m babylon60.cli.main_dispatcher, and keep the "
                "workspace out of PYTHONPATH.",
                file=sys.stderr,
            )
            return EXIT_UNAVAILABLE
        if launcher.backend() == "landlock" and launcher.landlock_abi() < LANDLOCK_SCOPE_ABI:
            print(
                f"babylon60 run: warning: Landlock ABI {launcher.landlock_abi()} does not scope signals "
                f"(ABI {LANDLOCK_SCOPE_ABI}): the agent can signal your other processes"
                + (" and reach abstract Unix sockets" if args.allow_unix_sockets else ""),
                file=sys.stderr,
            )
        env, removed = agent_environment(
            os.environ, preset=args.preset, keep_agent_sockets=args.keep_agent_sockets, passed=pass_env
        )
        withheld = env.pop(WITHHELD_VAR, "")  # removed before the re-exec: names only
        env.pop(IMPORT_DIR_VAR, None)
        removed = sorted({*removed, *(name for name in withheld.split(",") if name)})
        env_removed = [printable(name) for name in removed]
        by_name = [printable(name) for name in removed if credential_like(name)]
        by_value = [printable(name) for name in removed if not credential_like(name)]
        if by_name:
            sockets = " (--keep-agent-sockets keeps the agent sockets)" if set(removed) & set(AGENT_SOCKET_VARS) else ""
            print(
                f"babylon60 run: not passed to the agent, names that look like credentials: {', '.join(by_name)}; "
                f"--pass-env NAME keeps one{sockets}",
                file=sys.stderr,
            )
        if by_value:
            print(
                "babylon60 run: not passed to the agent, values that are URLs with a password: "
                f"{', '.join(by_value)}; --pass-env NAME keeps one",
                file=sys.stderr,
            )
        if args.dry_run:
            document = {"backend": launcher.backend(), "policy_digest": policy.digest(), **policy.as_dict()}
            document["tmpdir"] = "a private directory, created for each run and removed afterwards"
            document["terminal"] = (
                "a private pseudo-terminal, allocated for each run when stdin, stdout or stderr is a terminal "
                "and relayed to it; the agent never holds the user's terminal"
            )
            document["env_removed"] = env_removed
            print(json.dumps(document, indent=2))
            return 0
        assert private_tmp is not None
        env.update(private_tmp_environment(env, private_tmp))
        launch = launcher.run_launch(
            [executable, *command[1:]],
            policy,
            unix_sockets=args.allow_unix_sockets,
            private_tty=terminal.private_tty if terminal else None,
            clipboard=clipboard,
        )
        # Inherited as ignored (nohup, a background job): the agent keeps them and nothing relays them.
        ignored = launcher.ignored_signals()
        # SIGINT is ignored below only for this process while it starts the agent.
        launch.default_signals = () if signal.SIGINT in ignored else ("SIGINT",)
        # git and the agents inside expand ~ with the HOME the agent receives.
        checks = SessionChecks(policy, str(workspace), env.get("HOME"))
        with ConfineJournal(journal_path) as journal:
            journal.append(
                "run_start",
                {
                    "backend": launcher.backend(),
                    "policy_digest": policy.digest(),
                    "preset": args.preset,
                    "command": os.path.basename(executable),
                    "argc": len(command),
                    "env_removed": env_removed,
                    "seccomp": launch.seccomp,
                    "unix_sockets": launch.unix_sockets,
                    "new_session": launch.new_session,
                    "terminal": "private" if terminal else "none",
                    "allow_ptys": policy.allow_ptys,
                    "policy_warnings": len(policy.warnings),
                },
            )
            previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                launcher.become_subreaper()
                stdin, stdout, stderr = terminal.agent_stdio() if terminal else (None, None, None)
                try:
                    process, status = launcher.spawn(
                        launch,
                        env=env,
                        cwd=str(workspace),
                        stdin=stdin,
                        stdout=stdout,
                        stderr=stderr,
                    )
                except ValueError as exc:  # macOS: a granted path Seatbelt cannot name in its profile
                    journal.append("run_refused", {"error": str(exc)})
                    print(f"babylon60 run: cannot start the confined command: {exc}", file=sys.stderr)
                    return EXIT_UNAVAILABLE
                if not status.get("ok"):
                    process.wait()
                    journal.append("run_refused", {"error": status.get("error", "unknown")})
                    print(f"babylon60 run: confinement refused: {status.get('error')}", file=sys.stderr)
                    return EXIT_REFUSED
                # Relay the terminal (or signals) until the agent exits, then end whatever it left running:
                # nothing it started can change files after the checks below.
                session = launcher.supervise(process, status, terminal, ignored=ignored)
                returncode = session.returncode
            finally:
                signal.signal(signal.SIGINT, previous)
                launcher.become_subreaper(False)
            # supervise() ended every descendant first, so the checks see the final state.
            # run_end is journaled even when a check fails (named in checks_failed) or is interrupted.
            end: dict[str, Any] = {
                "exit_code": returncode,
                "landlock_abi": status.get("landlock_abi"),
                "landlock_scoped": status.get("landlock_scoped"),
                "caps_dropped": status.get("caps_dropped"),
                "ended_by": signal.Signals(session.ended_by).name if session.ended_by else None,
                "leftovers": session.leftovers,
            }
            try:
                checks.finish(end)
            finally:
                journal_run_end(journal, end)
        checks.print_report()
        return session.exit_code  # 128 + n when signal n killed the agent or (SIGTERM, SIGHUP) ended the session
    finally:
        if terminal is not None:
            terminal.close()
        if private_tmp is not None:
            shutil.rmtree(private_tmp, ignore_errors=True)


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


def register_confine_subparsers(subparsers: Any, cmd_run_fn: Any, cmd_log_fn: Any) -> None:
    """Register ``run``, ``demo`` and ``log`` subcommands on the root CLI parser."""
    p_run = subparsers.add_parser(
        "run",
        help="Run an agent command with OS read confinement: no home directory unless granted",
        description="Linux: Landlock (ABI >= 3). macOS: Seatbelt. Usage: babylon60 run [options] -- COMMAND [ARGS...]",
    )
    p_run.add_argument(
        "--preset",
        choices=["claude-code", "codex"],
        help="Grant this agent's own state and install prefixes, and the git configuration read-only",
    )
    p_run.add_argument("--allow-read", action="append", default=[], metavar="PATH", help="Extra read-only path")
    p_run.add_argument("--allow-write", action="append", default=[], metavar="PATH", help="Extra writable path")
    p_run.add_argument("--workspace", metavar="DIR", help="Writable project directory (default: current directory)")
    p_run.add_argument(
        "--journal", metavar="PATH", help="Confinement journal (default: $BABYLON_HOME/confine/journal.db)"
    )
    p_run.add_argument("--allow-root", action="store_true", help="Accept running as uid 0 (weaker; see help text)")
    p_run.add_argument("--keep-agent-sockets", action="store_true", help="Keep SSH_AUTH_SOCK and GPG_AGENT_INFO")
    p_run.add_argument(
        "--allow-clipboard",
        action="store_true",
        help="macOS: let the agent read and replace the pasteboard (pbcopy/pbpaste, pasting images); denied by default",
    )
    p_run.add_argument(
        "--pass-env",
        action="append",
        default=[],
        metavar="NAME",
        help="Pass this environment variable although its name looks like a credential (repeatable)",
    )
    p_run.add_argument(
        "--allow-unix-sockets",
        action="store_true",
        help="Allow Unix domain sockets (ssh-agent, tmux, D-Bus, Docker); blocked by default",
    )
    p_run.add_argument(
        "--allow-ptys",
        action="store_true",
        help="Grant new pseudo-terminals; other terminals of this user become readable and writable",
    )
    p_run.add_argument("--dry-run", action="store_true", help="Print the checked policy without running")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="-- COMMAND [ARGS...]")
    p_run.set_defaults(func=cmd_run_fn)

    p_log = subparsers.add_parser("log", help="Show and verify the confinement journal")
    p_log.add_argument(
        "--journal", metavar="PATH", help="Confinement journal (default: $BABYLON_HOME/confine/journal.db)"
    )
    p_log.add_argument("--tail", type=int, default=20, help="Events to show (default: 20)")
    p_log.add_argument("--json", action="store_true", help="Print entries and verification as JSON")
    p_log.add_argument(
        "--expect-head",
        metavar="BLAKE3",
        help="Fail unless the verified chain contains this head digest (one you published earlier)",
    )
    p_log.set_defaults(func=cmd_log_fn)
