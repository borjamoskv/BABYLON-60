"""Handlers for ``babylon60 run``, ``babylon60 demo`` and ``babylon60 log``.

Exit codes: 0 success (demo: every counted attempt blocked); 1 demo FALSIFIED,
a ``demo --check`` document that cannot be read or whose self digest does not
match, and for ``log`` a broken chain, an unusable journal or an absent
``--expect-head`` digest; 2 demo INCONCLUSIVE, usage error or a malformed
``--expect-head``; 3 for ``run`` no confinement backend, uid 0 without
``--allow-root``, a refused policy (or, on macOS, one naming a path Seatbelt
cannot hold), a launcher that imports from a write grant, an unusable journal
(or one with more than one hard link) or no private pseudo-terminal, and for
``demo`` no backend or an unusable journal; 126 the trampoline refused to start
the target; 127 command not found; otherwise the confined command's own exit
code (128 + n when signal n ended the session).
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import sys
import sysconfig
import tempfile
from typing import TYPE_CHECKING, Any, TypeVar

from babylon60.confine import persistence
from babylon60.confine.persistence import printable
from babylon60.confine.policy import PRESETS, SHARED_DIR_BITS, Identity, Policy, ancestry

if TYPE_CHECKING:
    from babylon60.confine.journal import ConfineJournal

EXIT_USAGE, EXIT_UNAVAILABLE, EXIT_REFUSED, EXIT_NOT_FOUND = 2, 3, 126, 127
LANDLOCK_SCOPE_ABI = 6  # LANDLOCK_SCOPE_SIGNAL and LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET
AGENT_SOCKET_VARS = ("SSH_AUTH_SOCK", "GPG_AGENT_INFO")
# Environment variables whose names look like credentials, or whose value is a URL with a password,
# are not passed to the agent, unless kept with --pass-env (the agent's own credential is kept when
# its preset is used).
CREDENTIAL_VARS = frozenset(
    {
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SECURITY_TOKEN",
        "AWS_SESSION_TOKEN",
        "DOCKER_AUTH_CONFIG",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "KRB5CCNAME",
        "MYSQL_PWD",
        *AGENT_SOCKET_VARS,
    }
)
CREDENTIAL_WORDS = ("SECRET", "PASSWORD", "PASSWD", "PASSPHRASE", "CREDENTIAL")  # anywhere in the name
CREDENTIAL_LAST_WORDS = ("KEY", "APIKEY", "PAT", "AUTH")  # NAME_KEY, NAME_API_KEY, NAME_PAT, NPM_CONFIG__AUTH
# The bare password conventions, as any word but the first: DB_PASS, SMTP_PASS_1, ORACLE_PWD.
# First or alone they are something else: PWD and OLDPWD are the shell's working directories,
# and GIT_ASKPASS names a program (ASKPASS is one word).
PASSWORD_WORDS = ("PASS", "PWD")
# A value that carries a password whatever its name: a URL with one in its userinfo
# (DATABASE_URL=postgres://user:secret@host, PIP_EXTRA_INDEX_URL=https://user:token@host).
URL_WITH_PASSWORD = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^/?#@\s:]*:[^/?#@\s]+@")
AGENT_CREDENTIALS = {
    "claude-code": ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN"),
    "codex": ("OPENAI_API_KEY", "CODEX_*"),
}
# Names (never values) the first launcher withheld before it re-executed itself without them.
WITHHELD_VAR = "BABYLON60_RUN_WITHHELD"
# The directory the first launcher imported from (sys.path[0]) when it ran without -P: the re-exec
# runs with -P, so only this tells it whether the user started babylon60 from the workspace.
IMPORT_DIR_VAR = "BABYLON60_RUN_IMPORT_DIR"
JOURNAL_NAMES = 100  # labels journaled per list; the rest are counted
SHOWN_NAMES = 20  # labels printed per list
LABEL_CHARS = 512
_T = TypeVar("_T")


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


def outside_grants_hint(executable: str, homes: tuple[str, ...], policy: Policy) -> str | None:
    """One line for stderr when Landlock will refuse to start the command (Linux only).

    The file the command resolves to, or its ``#!`` interpreter, lies outside every
    granted path and outside the home directories (those have their own grants and
    hint). Without this line the trampoline only reports ``Permission denied``. It
    suggests ``--allow-read`` for the smallest directory that holds the install: the
    first ``node_modules`` of an npm package, the root of a virtual environment, or
    the file's own directory.
    """
    home_ids = _home_ids(homes)
    granted = {(grant.dev, grant.ino) for grant in policy.grants if grant.access in ("ro", "rw")}
    candidates = [os.path.realpath(executable)]
    named = _script_interpreter(executable)
    if named is not None:
        candidates.append(os.path.realpath(named))
    allow: list[str] = []
    for path in dict.fromkeys(candidates):
        chain = _chain(path)
        if not chain or granted.intersection(chain) or home_ids.intersection(chain[1:]):
            continue
        allow.append(_install_root(path))
    if not allow:
        return None
    shared = [path for path in allow if _shared_directory(path)]
    if shared:
        advice = (
            f"it is in a shared directory ({', '.join(shared)}) that cannot be granted; "
            "copy it to a directory of your own and pass --allow-read for that directory"
        )
    else:
        advice = "to allow it, pass " + " ".join(f"--allow-read {path}" for path in dict.fromkeys(allow))
    hint = f"{os.path.basename(executable)} resolves to {candidates[0]}, outside every granted path; {advice}"
    return "".join(char if char.isprintable() else repr(char)[1:-1] for char in hint)


def _install_root(path: str) -> str:
    """The directory to grant for an installed program: npm's first node_modules, a venv root, or its folder."""
    marker = os.sep + "node_modules" + os.sep
    if marker in path:
        return path[: path.index(marker) + len(marker) - 1]
    folder = os.path.dirname(path)
    venv = os.path.dirname(folder)
    return venv if os.path.isfile(os.path.join(venv, "pyvenv.cfg")) else folder


def _shared_directory(path: str) -> bool:
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return False
    return stat.S_ISDIR(mode) and mode & SHARED_DIR_BITS == SHARED_DIR_BITS


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


def launcher_paths(journal: str, package_dir: str) -> list[str]:
    """The launcher's own state and code: write grants over them, above them or inside them are refused.

    Besides the journal and this package: the virtual environment the launcher
    runs from (all of it), the base interpreter that runs the trampoline, the
    standard library and extension modules it imports with ``-I -S`` before it
    confines itself, and the site-packages the launcher imports its dependencies
    from. The interpreter's prefix is not listed: the binary's own path already
    covers the directories above it, and a grant elsewhere under it (for example
    ``/usr/local/src``) touches nothing the launcher runs.
    """
    from babylon60.confine import launcher

    paths = [journal, package_dir, launcher.interpreter()]
    if sys.prefix != sys.base_prefix:  # a virtual environment
        paths.append(sys.prefix)
    paths.extend(sysconfig.get_path(name) for name in ("stdlib", "platstdlib", "purelib", "platlib"))
    dynload = sysconfig.get_config_var("DESTSHARED")
    if isinstance(dynload, str) and dynload:
        paths.append(dynload)
    return list(dict.fromkeys(path for path in paths if path))


def credential_like(name: str) -> bool:
    """Whether an environment variable's name looks like a credential (``GH_TOKEN``, ``AWS_SECRET_ACCESS_KEY``).

    Words are separated by ``_``: one ending in ``TOKEN`` (not ``MAX_THINKING_TOKENS``
    or ``TOKENIZERS_PARALLELISM``), one containing ``SECRET``, ``PASSWORD``, ``PASSWD``,
    ``PASSPHRASE`` or ``CREDENTIAL``, a last word ``KEY``, ``APIKEY``, ``PAT`` or ``AUTH``,
    a word ``PASS`` or ``PWD`` other than the first (``SMTP_PASS``, ``DB_PASS_PROD``,
    ``ORACLE_PWD``; never ``PWD`` itself), ``..._KEY_ID``, ``OP_SESSION_*`` and the names in
    ``CREDENTIAL_VARS``.
    """
    upper = name.upper()
    if upper in CREDENTIAL_VARS or upper.startswith("OP_SESSION_"):
        return True
    words = [word for word in upper.split("_") if word]
    if not words:
        return False
    if any(word.endswith("TOKEN") or any(part in word for part in CREDENTIAL_WORDS) for word in words):
        return True
    if any(word in PASSWORD_WORDS for word in words[1:]):
        return True
    return words[-1] in CREDENTIAL_LAST_WORDS or words[-2:] == ["KEY", "ID"]


def password_in_value(value: str) -> bool:
    """Whether a value carries a password: a URL with one in its userinfo (``scheme://user:secret@host``).

    The value is only matched here; it is never stored, journaled or printed.
    """
    return URL_WITH_PASSWORD.search(value) is not None


def agent_environment(
    environ: Mapping[str, str], *, preset: str | None, keep_agent_sockets: bool, passed: Iterable[str]
) -> tuple[dict[str, str], list[str]]:
    """The environment for the agent and the sorted names removed from it (never their values).

    Removed: names that look like credentials (``credential_like``), variables whose
    value is a URL with a password (``password_in_value``) and the agent sockets
    ``SSH_AUTH_SOCK`` and ``GPG_AGENT_INFO``. Kept: the names in ``passed``
    (``--pass-env``), the sockets with ``keep_agent_sockets``, and the agent's own
    credential when its preset is used (``AGENT_CREDENTIALS``).
    """
    keep = set(passed)
    if keep_agent_sockets:
        keep.update(AGENT_SOCKET_VARS)
    own = AGENT_CREDENTIALS.get(preset or "", ())
    env: dict[str, str] = {}
    removed: list[str] = []
    for name, value in environ.items():
        secret = credential_like(name) or password_in_value(value)
        if name not in keep and secret and not any(fnmatchcase(name, item) for item in own):
            removed.append(name)
        else:
            env[name] = value
    return env, sorted(removed)


def reexec_without_withheld(args: argparse.Namespace, passed: Sequence[str]) -> None:
    """Replace this process with itself, minus the variables the agent will not receive.

    A process's exec-time environment stays readable to the user's other processes outside
    any sandbox (``/proc/<pid>/environ`` on Linux, sysctl KERN_PROCARGS2 and ``ps -E`` on
    macOS). Landlock's ptrace scope and Seatbelt's process-info rule keep the agent from
    reading it; this is defence in depth, so the launcher no longer holds what ``run``
    withholds at all. It costs one interpreter start and runs on every platform. Returns
    only when there is nothing to withhold or this process is not the ``run`` command line.
    """
    if WITHHELD_VAR in os.environ or args.dry_run or "run" not in sys.argv[1:]:
        return
    env, removed = agent_environment(
        os.environ, preset=args.preset, keep_agent_sockets=args.keep_agent_sockets, passed=passed
    )
    if not removed:
        return
    env[WITHHELD_VAR] = ",".join(removed)
    if not sys.flags.safe_path and sys.path:
        env[IMPORT_DIR_VAR] = os.path.abspath(sys.path[0])
    sys.stdout.flush()
    sys.stderr.flush()
    argv = [sys.executable, *interpreter_flags(), "-m", "babylon60.cli.main_dispatcher", *sys.argv[1:]]
    os.execve(sys.executable, argv, env)


def interpreter_flags() -> list[str]:
    """This interpreter's isolation flags for the re-exec, always with ``-P``.

    ``-P`` keeps the working directory off ``sys.path``: ``python -m`` would otherwise import
    from it, and the default workspace is the working directory, where the agent can leave a
    ``json.py`` that the next launcher start would run outside the sandbox.
    """
    if sys.flags.isolated:
        return ["-I"]  # implies -E, -P and -s
    flags = ["-E"] if sys.flags.ignore_environment else []
    flags += ["-s"] if sys.flags.no_user_site else []
    flags += ["-S"] if sys.flags.no_site else []
    return [*flags, "-P"]


def writable_import_paths(policy: Policy, entries: Iterable[str]) -> list[str]:
    """Entries of the launcher's import path that the agent could write (inside a rw grant).

    A module or ``.pth`` file the agent leaves in one of them runs outside the sandbox the next
    time babylon60 starts: ``python -m`` from the workspace, a ``PYTHONPATH`` or a user site
    inside a write grant. Compared by identity, like the grants themselves.
    """
    writable = {(grant.dev, grant.ino) for grant in policy.grants if grant.access == "rw"}
    found: list[str] = []
    for entry in dict.fromkeys(os.path.abspath(entry) for entry in entries if entry is not None):
        try:
            chain = ancestry(entry)
        except OSError:
            continue  # a missing entry imports nothing
        if any(ident in writable for ident in chain):
            found.append(entry)
    return found


def _bounded(labels: Sequence[str], limit: int, ranks: Mapping[str, int] | None = None) -> list[str]:
    """At most ``limit`` labels, each shortened to ``LABEL_CHARS``, then how many were left out.

    When some must be left out, ``ranks`` (``persistence.Report.ranks``) decides which stay, riskiest
    first: git hooks, git configs and the programs they name, agent and tool settings, instruction
    files, then the rest. So many harmless files changed at once never push a hook's name out.
    """
    if ranks and len(labels) > limit:
        labels = sorted(labels, key=lambda label: (ranks.get(label, persistence.RANK_OTHER), label))
    shown = [label if len(label) <= LABEL_CHARS else label[: LABEL_CHARS - 1] + "…" for label in labels[:limit]]
    return shown + ([f"... and {len(labels) - limit} more"] if len(labels) > limit else [])


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
        for warning in policy.warnings:
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
        env["TMPDIR"] = private_tmp
        launch = launcher.run_launch(
            [executable, *command[1:]],
            policy,
            unix_sockets=args.allow_unix_sockets,
            private_tty=terminal.private_tty if terminal else None,
            clipboard=bool(getattr(args, "allow_clipboard", False)),
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


def demo_command(args: argparse.Namespace) -> int:
    from babylon60.confine.demo import check_evidence, run_demo
    from babylon60.confine.journal import JournalError
    from babylon60.confine.launcher import ConfinementUnavailable

    if args.check:
        try:
            document = json.loads(Path(args.check).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"babylon60 demo --check: cannot read {args.check}: {exc}", file=sys.stderr)
            return 1  # nothing verified
        result = check_evidence(document)
        print(f"self digest: {'ok' if result['self_digest_ok'] else 'MISMATCH'}")
        print("  a checksum of the document, not a signature: whoever edits it can recompute it")
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
    except (ConfinementUnavailable, JournalError) as exc:  # 1 means FALSIFIED: never for an unusable journal
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
