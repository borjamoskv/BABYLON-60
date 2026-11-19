# ruff: noqa: F401
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


def _parse_short_env_flags(word: str, words: list[str], search: str | None) -> tuple[str | None, str | None]:
    for index, flag in enumerate(word[1:], start=2):
        if flag == "S":
            return word[index:], search
        if flag in "uCaP":
            value = word[index:] or (words.pop(0) if words else "")
            if flag == "P":
                search = value
            return None, search
    return None, search


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
            split, search = _parse_short_env_flags(word, words, search)
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


def private_tmp_environment(
    environ: Mapping[str, str], private_tmp: str, *, platform: str = sys.platform
) -> dict[str, str]:
    """``TMPDIR`` and the variables ``run`` points into the agent's private TMPDIR when ``environ`` lacks them.

    Some tools ignore ``TMPDIR`` and write where the agent may not, so they fail confined; and what
    the agent could write there would outlive the session, for the user's own unconfined builds to
    load. Each value lives in the private TMPDIR, removed when the session ends:

    * ``CLANG_MODULE_CACHE_PATH``, read by clang's driver (LLVM D126678) when no
      ``-fmodules-cache-path`` is given: clang ``-fmodules`` otherwise caches modules in the per-user
      cache directory on macOS (``/private/var/folders/.../C``, which the Seatbelt profile denies)
      and in ``~/.cache/clang/ModuleCache`` on Linux (under the denied home). A value the user set is
      kept, even empty, as outside ``run``: with an empty one the driver passes no cache path, and a
      compile that needs a module fails (measured unconfined with clang 18.1.3: "fatal error: module
      'B60' is needed but has not been provided, and implicit use of module files is disabled").
    * ``MAC_CHROMIUM_TMPDIR`` (macOS), also when empty: Chromium's ``base::GetTempDir``
      (base/files/file_util_apple.mm) reads it when it is not empty and otherwise
      ``NSTemporaryDirectory()``. Chrome creates its ProcessSingleton socket directory there and
      aborts without one. That ``NSTemporaryDirectory()`` gives the per-user ``T`` directory the
      profile denies, not ``$TMPDIR``, is inferred from the CI of f3747db (Chrome aborted with the
      private TMPDIR writable) and matches swift-foundation, whose temporary directory reads
      ``_CS_DARWIN_USER_TEMP_DIR`` before ``TMPDIR``.
    """
    values = {"CLANG_MODULE_CACHE_PATH": os.path.join(private_tmp, "clang-module-cache")}
    if platform == "darwin":
        values["MAC_CHROMIUM_TMPDIR"] = private_tmp

    def users(name: str) -> bool:
        # Chromium ignores an empty MAC_CHROMIUM_TMPDIR, so only a non-empty one is the user's choice.
        return bool(environ.get(name)) if name == "MAC_CHROMIUM_TMPDIR" else name in environ

    return {"TMPDIR": private_tmp, **{name: value for name, value in values.items() if not users(name)}}


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
