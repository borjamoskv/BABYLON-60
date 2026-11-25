"""Argument registration for confinement CLI subcommands without Unix-only imports."""

from __future__ import annotations

import argparse
from typing import Any


def register_confine_subparsers(subparsers: Any, cmd_run_fn: Any, cmd_demo_fn: Any, cmd_log_fn: Any) -> None:
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
    p_run.add_argument(
        "--accept-hardlinks",
        action="store_true",
        help="Start although a protected file has a hard link inside a grant, or the search for one did not "
        "finish; the agent can read that file (refused by default)",
    )
    p_run.add_argument("--dry-run", action="store_true", help="Print the checked policy without running")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="-- COMMAND [ARGS...]")
    p_run.set_defaults(func=cmd_run_fn)

    p_demo = subparsers.add_parser(
        "demo", help="First block: a test agent tries to read ~/.ssh/id_rsa, unconfined and confined"
    )
    p_demo.add_argument("--repeat", type=int, default=1, help="Attempts per vector (default: 1)")
    p_demo.add_argument("--workers", type=int, default=4, help="Concurrent attempts (default: 4)")
    p_demo.add_argument(
        "--journal", metavar="PATH", help="Confinement journal (default: $BABYLON_HOME/confine/journal.db)"
    )
    p_demo.add_argument("--json", metavar="PATH", help="Write the evidence document (- for stdout)")
    p_demo.add_argument("--evidence-dir", metavar="DIR", help="Also write demo-<os>-<arch>-<date>.json into DIR")
    p_demo.add_argument("--check", metavar="FILE", help="Verify a recorded evidence document instead of running")
    p_demo.set_defaults(func=cmd_demo_fn)

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
