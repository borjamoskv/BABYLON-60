"""Files an agent can leave behind that run, or steer an agent, outside the sandbox later.

``babylon60 run`` takes a ``snapshot`` before the session and another one after
it; ``changes`` names, by path, what was added, modified or removed in between.
This is detection, not prevention: inside its write grants the agent can still
write these files, and the report makes that visible.

Only what a write grant of the policy reaches is compared: a path is writable
when the identity ``(st_dev, st_ino)`` of a granted directory or file is among
its physical ancestors, as Landlock decides. Nothing is resolved with
``realpath``; material outside the write grants cannot change and is skipped.

Code and configuration (``Report.code``):

* In the workspace, in every directory granted with ``--allow-write`` and in the
  repository around them: git hooks wherever they live (``<gitdir>/hooks`` and
  every ``core.hooksPath`` of the system, global, repository and worktree
  configs, relative ones taken from the working tree), the config files with
  every ``include.path`` and ``includeIf.*.path``, ``.git`` files that point to
  a gitdir, ``commondir``, submodule gitdirs (``.git/modules/**``) and the
  ``.git`` files of their checkouts, linked worktrees (``.git/worktrees/*``),
  programs that git config names by path (``core.fsmonitor``, filters,
  ``alias.*`` with ``!`` and the other command keys), hook managers
  (``.husky/``, ``.pre-commit-config.yaml``, lefthook), direnv's ``.envrc``,
  ``.vscode/tasks.json`` (tasks may run on folder open) and
  ``.vscode/settings.json``, ``.mcp.json``, ``.codex/`` and ``.claude/``
  except its data (``worktrees``) and instruction files.
* Under every home directory: what Claude Code and Codex load or run (settings,
  hooks, plugins, commands, agents, skills, output styles, ``~/.codex/rules``
  and ``config.toml``, the local launcher ``~/.claude/local``, and scripts and
  executables anywhere else in ``~/.claude`` and ``~/.codex`` but their data
  directories), ``~/.claude.json`` by its security-relevant keys only
  (``CLAUDE_JSON_KEYS``: MCP servers, hooks, permissions, trust and API-key
  approvals, never its counters and caches), and common startup material
  (``HOME_STARTUP``: shell rc files, git config, user bin directories,
  autostart and systemd user units, package manager and editor init files).

Instructions (``Report.instructions``): ``~/.claude/CLAUDE.md``,
``~/.claude/rules`` and ``~/.codex/AGENTS.md`` are prompts, not code, but every
later session of that agent reads them, in every project and also outside the
sandbox, and no repository diff shows them. ``CLAUDE.md`` and ``AGENTS.md``
inside a project are project content, reviewed in its own diff: not compared.

A file is opened only after ``lstat`` shows a regular file, with ``O_NOFOLLOW``
and ``O_NONBLOCK``, and is compared by type, permission bits and content: whole
up to ``FULL_HASH_BYTES``; a larger (or sparse) file by size, modification and
change times, inode and its first and last ``CHUNK_BYTES``. Symbolic links are
compared by their target text and never followed; other types by type and mode.
Names are bytes, so any file name works; labels escape what is not printable.
Git configs and pointer files are read for discovery wherever they are, up to
``CONFIG_BYTES``, never below ``/proc``, ``/sys`` or a protected path. Limits
per root (``MAX_ROOT_ENTRIES``, ``MAX_DEPTH``) and per snapshot
(``MAX_ENTRIES``, ``MAX_READ_BYTES``) bound the work; a root that reaches one
is listed in ``Report.unchecked`` instead of being compared in full.

Not covered (declared limits): nested repositories that are not submodules,
scripts that a configuration names outside these locations (git config names
by path excepted), targets of symbolic links, configuration passed in
``GIT_CONFIG_*`` environment variables, and changes reverted before the
session ends.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
import errno
import json
import os
import shlex
import stat

from blake3 import blake3

from babylon60.confine.policy import Identity, Policy, ancestry

CODE, INSTRUCTIONS = "code", "instructions"
FULL_HASH_BYTES = 256 * 1024  # files up to this size are compared by their whole content
CHUNK_BYTES = 64 * 1024  # larger files: metadata plus their first and last chunk
MAX_ROOT_ENTRIES = 20_000  # entries examined below one root
MAX_ENTRIES = 100_000  # entries examined in one snapshot
MAX_READ_BYTES = 256 * 1024 * 1024  # bytes read in one snapshot
MAX_DEPTH = 32
CONFIG_BYTES = 1024 * 1024  # git config, include and pointer files read for discovery
CLAUDE_JSON_BYTES = 16 * 1024 * 1024  # larger, or not a JSON object: compared whole
MAX_GITDIRS = 256
MAX_INCLUDE_DEPTH = 10  # git's own limit
MAX_SEARCH_UP = 64  # parent directories searched for the repository around a project

_DOMAIN = b"BABYLON60-CONFINE-PERSISTENCE/v1\x00"
_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY | _CLOEXEC
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | _CLOEXEC

# Read by git, by a hook manager, by direnv or by an editor from a project directory.
PROJECT_FILES = (
    ".envrc",
    ".vscode/tasks.json",
    ".vscode/settings.json",
    ".mcp.json",
    ".codex",
    ".husky",
    ".pre-commit-config.yaml",
    "lefthook.yml",
    ".lefthook.yml",
    "lefthook-local.yml",
    ".lefthook-local.yml",
)
# Startup material under a home, compared only where a write grant reaches it.
HOME_STARTUP = (
    ".profile",
    ".bashrc",
    ".bash_profile",
    ".bash_login",
    ".bash_logout",
    ".zshenv",
    ".zprofile",
    ".zshrc",
    ".zlogin",
    ".zlogout",
    ".config/fish",
    ".gitconfig",
    ".config/git",
    ".local/bin",
    ".local/share/claude",
    ".cargo/bin",
    ".cargo/config.toml",
    ".cargo/config",
    "go/bin",
    ".deno/bin",
    ".bun/bin",
    ".volta/bin",
    ".npm-global/bin",
    ".npmrc",
    ".yarnrc",
    ".yarnrc.yml",
    ".config/pip",
    ".pip",
    ".pydistutils.cfg",
    ".config/autostart",
    ".config/systemd/user",
    ".config/environment.d",
    ".pam_environment",
    ".xprofile",
    ".xsessionrc",
    ".xinitrc",
    "Library/LaunchAgents",
    ".vimrc",
    ".config/nvim",
    ".emacs",
    ".emacs.d/init.el",
    ".config/Code/User/settings.json",
    ".config/Code/User/tasks.json",
)
# Top-level entries of the agents' own directories. Data is written by every session and never
# compared; known code is compared whole; anything else only where it looks like code.
CLAUDE_HOME_DATA = frozenset(
    {
        ".credentials.json",
        "backups",
        "cache",
        "debug",
        "downloads",
        "file-history",
        "history.jsonl",
        "ide",
        "image-cache",
        "logs",
        "paste-cache",
        "plans",
        "projects",
        "session-env",
        "shell-snapshots",
        "stats-cache.json",
        "statsig",
        "tasks",
        "teams",
        "telemetry",
        "todos",
    }
)
CLAUDE_HOME_CODE = frozenset(
    {
        "agents",
        "commands",
        "hooks",
        "local",
        "output-styles",
        "plugins",
        "settings.json",
        "settings.local.json",
        "skills",
    }
)
CLAUDE_INSTRUCTIONS = frozenset({"CLAUDE.md", "rules"})
CLAUDE_PROJECT_DATA = frozenset({"worktrees", "plans", "todos", "logs", "cache"})
CODEX_HOME_DATA = frozenset(
    {
        ".tmp",
        "archived_sessions",
        "auth.json",
        "cache",
        "history.jsonl",
        "log",
        "models_cache.json",
        "sessions",
        "shell_snapshots",
        "tmp",
        "version.json",
    }
)
CODEX_HOME_CODE = frozenset({"config.toml", "prompts", "rules", "skills"})
CODEX_INSTRUCTIONS = frozenset({"AGENTS.md", "AGENTS.override.md"})
# ~/.claude.json keys, at the top level and in each ``projects`` entry, that change what runs or
# what is allowed without asking. Everything else there (counters, tips, caches) is not compared.
CLAUDE_JSON_KEYS = frozenset(
    name.lower()
    for name in (
        "allowedTools",
        "apiKeyHelper",
        "awsAuthRefresh",
        "awsCredentialExport",
        "bypassPermissionsModeAccepted",
        "customApiKeyResponses",
        "defaultMode",
        "disableAllHooks",
        "disabledMcpjsonServers",
        "enableAllProjectMcpServers",
        "enabledMcpjsonServers",
        "enabledPlugins",
        "env",
        "extraKnownMarketplaces",
        "hasTrustDialogAccepted",
        "hasTrustDialogHooksAccepted",
        "hooks",
        "mcpServers",
        "otelHeadersHelper",
        "permissions",
        "statusLine",
    )
)
CLAUDE_JSON_PATTERNS = ("hook", "permission", "trust", "helper", "mcpserver")
# Names of unknown files in the agents' directories that make them compared as code.
CODE_SUFFIXES = (
    b".sh",
    b".bash",
    b".zsh",
    b".fish",
    b".py",
    b".pyw",
    b".js",
    b".mjs",
    b".cjs",
    b".ts",
    b".mts",
    b".cts",
    b".rb",
    b".pl",
    b".php",
    b".lua",
    b".ps1",
    b".bat",
    b".cmd",
    b".exe",
    b".jar",
    b".node",
    b".so",
    b".dylib",
)
# Git config keys whose value is a command; a first word with a slash is a program to compare.
_GIT_COMMANDS = frozenset(
    {
        "core.askpass",
        "core.editor",
        "core.fsmonitor",
        "core.gitproxy",
        "core.pager",
        "core.sshcommand",
        "credential.helper",
        "diff.external",
        "gpg.program",
        "sequence.editor",
        "uploadpack.packobjectshook",
    }
)
_GIT_COMMAND_SUFFIXES = (".clean", ".smudge", ".process", ".driver", ".textconv", ".command", ".program", ".helper")
_GIT_BOOLEANS = frozenset({"", "true", "false", "yes", "no", "on", "off", "1", "0"})


@dataclass(frozen=True)
class _Root:
    path: bytes
    category: str
    rule: str  # "all", "code", "hooks", "pointer", "commondir", "claude-home", "codex-home", "claude-project", "claude-json"
    expect: bytes | None = None  # "pointer": the gitdir git itself would have it name


@dataclass(frozen=True)
class Snapshot:
    entries: dict[bytes, tuple[str, str, str]] = field(default_factory=dict)  # path: (category, label, digest)
    unchecked: tuple[str, ...] = ()  # roots not compared in full, and why
    roots: tuple[_Root, ...] = ()  # where it looked, so a later snapshot looks there too


@dataclass(frozen=True)
class Report:
    code: tuple[str, ...]  # labels of code and configuration added, modified or removed
    instructions: tuple[str, ...]  # labels of agent instruction files added, modified or removed
    unchecked: tuple[str, ...]  # roots not compared in full in either snapshot


class _Stop(Exception):
    """A limit was reached below the current root."""


def snapshot(policy: Policy, workspace: str, *, home: str | None = None, previous: Snapshot | None = None) -> Snapshot:
    """Record what can run, or steer an agent, outside the sandbox later and lies inside a write grant.

    ``home`` is the ``$HOME`` git and the agents expand ``~`` with (default: the first home of the policy).
    With ``previous``, every place it looked is looked at again, so a ``.git`` pointer or a
    ``core.hooksPath`` changed during the session cannot hide what was written where they pointed before.
    """
    walker = _Walker(policy, workspace, home)
    walked: dict[bytes, _Root] = {}
    for root in [*walker.roots(), *(previous.roots if previous is not None else ())]:
        if root.path not in walked:
            walked[root.path] = root
            walker.walk(root)
    return Snapshot(walker.entries, tuple(dict.fromkeys(walker.unchecked)), tuple(walked.values()))


def changes(before: Snapshot, after: Snapshot) -> Report:
    """Labels of what was added, modified or removed between two snapshots, by category."""
    code: set[str] = set()
    instructions: set[str] = set()
    for key in before.entries.keys() | after.entries.keys():
        old, new = before.entries.get(key), after.entries.get(key)
        if old is not None and new is not None and old[2] == new[2]:
            continue
        category, label, _ = new if new is not None else before.entries[key]
        (instructions if category == INSTRUCTIONS else code).add(label)
    unchecked = tuple(dict.fromkeys([*before.unchecked, *after.unchecked]))
    return Report(tuple(sorted(code)), tuple(sorted(instructions)), unchecked)


def printable(text: str | bytes) -> str:
    """``text`` for a terminal or the journal: invalid UTF-8 as ``\\xNN``, other non-printables escaped."""
    if isinstance(text, bytes):
        text = text.decode("utf-8", "backslashreplace")
    return "".join(char if char.isprintable() else repr(char)[1:-1] for char in text)


class _Walker:
    def __init__(self, policy: Policy, workspace: str, home: str | None) -> None:
        self.policy = policy
        self.workspace = os.fsencode(os.path.abspath(workspace))
        self.homes = [os.fsencode(path) for path in policy.homes]
        self.home = os.fsencode(home) if home else (self.homes[0] if self.homes else b"")
        self.rw: set[Identity] = set()
        self.on_path: set[Identity] = set()  # directories with a write grant at or below them
        for grant in policy.grants:
            if grant.access != "rw":
                continue
            self.rw.add((grant.dev, grant.ino))
            chain = _chain(os.fsencode(grant.path))
            self.on_path.update(chain if chain[:1] == [(grant.dev, grant.ino)] else [(grant.dev, grant.ino)])
        self.denied: set[Identity] = set()  # discovery never reads below these
        for path in ("/proc", "/sys", *policy.protected):
            try:
                st = os.stat(path)
            except OSError:
                continue
            self.denied.add((st.st_dev, st.st_ino))
        self.entries: dict[bytes, tuple[str, str, str]] = {}
        self.unchecked: list[str] = []
        self.walked: set[Identity] = set()  # directories compared, under the first name that reached them
        self.recorded: set[Identity] = set()  # other entries compared, likewise
        self.total = 0
        self.read_bytes = 0

    # --- what to compare ------------------------------------------------------------------------

    def roots(self) -> Iterator[_Root]:
        projects = [self.workspace]
        for grant in self.policy.grants:
            if grant.access == "rw" and grant.is_dir and grant.origin == "user":
                projects.append(os.fsencode(grant.path))
        global_config = _GitConfig(self)
        for path in _global_git_configs(self.home):
            global_config.load(path, base=os.path.dirname(path))
        yield from (_Root(path, CODE, "all") for path in global_config.files)
        for project in dict.fromkeys(projects):
            repository = self._repository(project)
            if repository is not None:
                yield from self._git_roots(repository, global_config)
            for name in PROJECT_FILES:
                yield _Root(project + b"/" + name.encode(), CODE, "all")
            yield _Root(project + b"/.claude", CODE, "claude-project")
        for home in self.homes:
            yield _Root(home + b"/.claude", CODE, "claude-home")
            yield _Root(home + b"/.claude.json", CODE, "claude-json")
            yield _Root(home + b"/.codex", CODE, "codex-home")
            for name in HOME_STARTUP:
                yield _Root(home + b"/" + name.encode(), CODE, "all")

    def _repository(self, project: bytes) -> bytes | None:
        """The working tree around ``project``: the nearest directory, itself included, holding ``.git``."""
        path = project
        for _ in range(MAX_SEARCH_UP):
            try:
                os.lstat(path + b"/.git")
                return path
            except OSError:
                pass
            parent = os.path.dirname(path)
            if parent == path:
                return None
            path = parent
        return None

    def _git_roots(self, worktree: bytes, global_config: _GitConfig) -> Iterator[_Root]:
        dotgit = worktree + b"/.git"
        try:
            st = os.lstat(dotgit)
        except OSError:
            return
        if not stat.S_ISDIR(st.st_mode):
            yield _Root(dotgit, CODE, "all")  # a gitdir pointer, or a link
        gitdir = dotgit if stat.S_ISDIR(st.st_mode) else self._pointer(dotgit, worktree)
        if gitdir is None:
            return
        queue: deque[tuple[bytes, bytes | None]] = deque([(gitdir, worktree)])
        seen: set[bytes] = set()
        while queue and len(seen) < MAX_GITDIRS:
            gitdir, tree = queue.popleft()
            if gitdir in seen:
                continue
            seen.add(gitdir)
            common = gitdir
            pointer = self.read(gitdir + b"/commondir", limit=4096)
            if pointer is not None:
                yield _Root(gitdir + b"/commondir", CODE, "commondir")
                common = _join(gitdir, pointer.strip(), self.home)
            config = _GitConfig(self)
            config.load(common + b"/config", base=common)
            config.load(gitdir + b"/config.worktree", base=gitdir)
            yield from (_Root(path, CODE, "all") for path in config.files)
            for value in config.values("core.worktree"):
                tree = _join(gitdir, value, self.home)
            yield _Root(common + b"/hooks", CODE, "hooks")
            for source in (config, global_config):
                for value in source.values("core.hookspath"):
                    yield _Root(_join(tree or gitdir, value, self.home), CODE, "hooks")
                for program in source.programs():
                    yield _Root(_join(tree or gitdir, program, self.home), CODE, "all")
            # Submodule checkouts: a .git file naming the module's gitdir, or an old .git directory.
            if tree is not None:
                for name, path in self._submodules(tree):
                    checkout = _join(tree, path, self.home)
                    if os.path.isdir(checkout + b"/.git") and not os.path.islink(checkout + b"/.git"):
                        queue.append((checkout + b"/.git", checkout))
                    else:
                        yield _Root(checkout + b"/.git", CODE, "pointer", common + b"/modules/" + name)
            for module in self._module_gitdirs(common + b"/modules"):
                queue.append((module, None))
            if common == gitdir:  # linked worktrees: the admin directory and the .git file of the checkout
                for linked in self._listdir(common + b"/worktrees"):
                    entry = common + b"/worktrees/" + linked
                    target = self.read(entry + b"/gitdir", limit=4096)
                    linked_tree = None
                    if target is not None and target.strip():
                        linked_pointer = _join(entry, target.strip(), self.home)
                        yield _Root(linked_pointer, CODE, "pointer", entry)
                        linked_tree = os.path.dirname(linked_pointer)
                    queue.append((entry, linked_tree))

    def _pointer(self, dotgit: bytes, worktree: bytes) -> bytes | None:
        data = self.read(dotgit, limit=4096)
        if data is None:
            return None
        line = data.split(b"\n", 1)[0].strip()
        if not line.startswith(b"gitdir:"):
            return None
        return _join(worktree, line[len(b"gitdir:") :].strip(), self.home)

    def _submodules(self, tree: bytes) -> list[tuple[bytes, bytes]]:
        """``(name, path)`` of the submodules ``.gitmodules`` declares in the working tree ``tree``."""
        config = _GitConfig(self, follow_includes=False)
        config.load(tree + b"/.gitmodules", base=tree)
        found = []
        for key, value in config.entries:
            if key.startswith("submodule.") and key.endswith(".path") and value:
                found.append((os.fsencode(key[len("submodule.") : -len(".path")]), os.fsencode(value)))
        return found

    def _module_gitdirs(self, modules: bytes) -> Iterator[bytes]:
        """Gitdirs below ``modules`` (submodule names may hold slashes); not below a gitdir found."""
        pending = deque([(modules, 0)])
        found = listed = 0
        while pending and found < MAX_GITDIRS and listed < MAX_ROOT_ENTRIES:
            path, depth = pending.popleft()
            listed += 1
            names = self._listdir(path)
            if b"config" in names or b"HEAD" in names:
                found += 1
                yield path
                continue
            if depth < MAX_DEPTH:
                pending.extend((path + b"/" + name, depth + 1) for name in names)

    def _listdir(self, path: bytes) -> list[bytes]:
        """Names in the directory ``path`` (not a link to one), sorted; empty when it cannot be listed."""
        try:
            fd = os.open(path, _DIR_FLAGS)
        except OSError:
            return []
        try:
            names: list[bytes] = []
            with os.scandir(fd) as items:
                for item in items:
                    names.append(os.fsencode(item.name))
                    if len(names) >= MAX_ROOT_ENTRIES:
                        break
            return sorted(names)
        except OSError:
            return []
        finally:
            os.close(fd)

    # --- reading --------------------------------------------------------------------------------

    def read(self, path: bytes, *, limit: int = CONFIG_BYTES) -> bytes | None:
        """Up to ``limit`` bytes of the regular file ``path``, for discovery; None when it is not one.

        The parent path resolves as in any lookup; the file itself is never a link, and nothing
        below ``/proc``, ``/sys`` or a protected path is read.
        """
        parent, name = os.path.split(path)
        if not name or b"\x00" in path:
            return None
        try:
            dir_fd = os.open(parent or b"/", os.O_RDONLY | os.O_DIRECTORY | _CLOEXEC)
        except OSError:
            return None
        try:
            if self.denied.intersection(_fd_chain(dir_fd, parent or b"/")):
                return None
            st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
            if not stat.S_ISREG(st.st_mode):
                return None
            fd = os.open(name, _FILE_FLAGS, dir_fd=dir_fd)
            try:
                opened = os.fstat(fd)
                if (opened.st_dev, opened.st_ino) != (st.st_dev, st.st_ino):
                    return None
                return _read(fd, limit)
            finally:
                os.close(fd)
        except OSError:
            return None
        finally:
            os.close(dir_fd)

    # --- comparing ------------------------------------------------------------------------------

    def walk(self, root: _Root) -> None:
        label = self.label(root.path)
        if b"\x00" in root.path:  # _join cuts values at NUL; anything else holding one is not a path
            self.unchecked.append(f"{label} (not a path)")
            return
        try:
            st = os.lstat(root.path)
            chain = _physical_chain(root.path, st)
        except (FileNotFoundError, NotADirectoryError):
            return  # absent: nothing to compare until it appears
        except OSError as exc:
            self.unchecked.append(f"{label} ({_errname(exc)})")
            return
        if not chain or chain[0] != (st.st_dev, st.st_ino):
            self.unchecked.append(f"{label} (changed while it was being compared)")
            return
        writable = bool(self.rw.intersection(chain))
        try:
            if not stat.S_ISDIR(st.st_mode):
                if writable and not self._standard(root):
                    self._file(None, root.path, root.path, st, root.category, root.rule)
                return
            if not writable and chain[0] not in self.on_path:
                return  # nothing below it can change
            if chain[0] in self.walked:
                return  # the same directory under another name
            self.walked.add(chain[0])
            fd = os.open(root.path, _DIR_FLAGS)
            try:
                if _identity(os.fstat(fd)) != chain[0]:
                    raise _Stop("changed while it was being compared")
                self._directory(fd, root.path, root.rule, root.category, writable, 0, [MAX_ROOT_ENTRIES])
            finally:
                os.close(fd)
        except _Stop as stop:
            self.unchecked.append(f"{label} ({stop})")
        except OSError as exc:
            self.unchecked.append(f"{label} ({_errname(exc)})")

    def _standard(self, root: _Root) -> bool:
        """Whether ``root`` holds what git itself writes there (``git worktree add``, ``git submodule add``).

        ``commondir`` of a linked worktree is ``../..``; the ``.git`` file of a linked worktree or
        submodule checkout names the gitdir git made for it. Those run nothing and are not recorded,
        so creating a worktree or a submodule is not reported; any other content is compared.
        """
        if root.rule == "commondir":
            return (self.read(root.path, limit=4096) or b"").strip() == b"../.."
        if root.rule != "pointer" or root.expect is None:
            return False
        target = self._pointer(root.path, os.path.dirname(root.path))
        try:
            return target is not None and _identity(os.stat(target)) == _identity(os.stat(root.expect))
        except (OSError, ValueError):  # ValueError: a submodule name with a NUL byte
            return False

    def _directory(
        self, fd: int, path: bytes, rule: str, category: str, writable: bool, depth: int, budget: list[int]
    ) -> None:
        names: list[bytes] = []
        with os.scandir(fd) as items:
            for item in items:
                names.append(os.fsencode(item.name))
                if len(names) > budget[0]:
                    raise _Stop(f"more than {MAX_ROOT_ENTRIES} entries")
        for name in sorted(names):
            child = _child_rule(rule, name)
            if child is None:
                continue
            child_rule, child_category = child[0], child[1] or category
            budget[0] -= 1
            self.total += 1
            if budget[0] < 0:
                raise _Stop(f"more than {MAX_ROOT_ENTRIES} entries")
            if self.total > MAX_ENTRIES or self.read_bytes > MAX_READ_BYTES:
                raise _Stop("snapshot limits reached")
            child_path = path + b"/" + name
            try:
                st = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            except OSError as exc:
                if writable:
                    self._record(child_path, child_category, f"error:{_errname(exc)}")
                continue
            ident = _identity(st)
            child_writable = writable or ident in self.rw
            if not stat.S_ISDIR(st.st_mode):
                if child_writable:
                    self._file(fd, name, child_path, st, child_category, child_rule)
                continue
            if not child_writable and ident not in self.on_path:
                continue
            if depth + 1 > MAX_DEPTH:
                raise _Stop(f"deeper than {MAX_DEPTH} levels")
            if ident in self.walked:
                continue
            self.walked.add(ident)
            try:
                sub = os.open(name, _DIR_FLAGS, dir_fd=fd)
            except OSError as exc:
                if child_writable:
                    self._record(child_path, child_category, f"error:{_errname(exc)}")
                continue
            try:
                if _identity(os.fstat(sub)) != ident:
                    raise _Stop("changed while it was being compared")
                self._directory(sub, child_path, child_rule, child_category, child_writable, depth + 1, budget)
            finally:
                os.close(sub)

    def _file(self, dir_fd: int | None, name: bytes, path: bytes, st: os.stat_result, category: str, rule: str) -> None:
        """Compare one entry that is not a directory, once per identity: a file reachable under
        another name (through a linked worktree's ``commondir``, or a hard link) keeps the key of
        the first name that reached it."""
        if _identity(st) in self.recorded:
            return
        if rule == "claude-json":
            self.recorded.add(_identity(st))
            self._claude_json(path, st, category)
            return
        try:
            digest, head = self._digest(dir_fd, name, st)
        except OSError as exc:
            digest, head = f"error:{_errname(exc)}", b""
        if rule == "code" and not _looks_like_code(name, st, head):
            return
        self.recorded.add(_identity(st))
        self._record(path, category, digest)

    def _digest(self, dir_fd: int | None, name: bytes, st: os.stat_result) -> tuple[str, bytes]:
        """Digest of one entry, and the first bytes of a regular file (to recognise ``#!``)."""
        hasher = blake3(_DOMAIN)
        mode = stat.S_IMODE(st.st_mode)
        if stat.S_ISLNK(st.st_mode):
            hasher.update(b"link\x00" + os.readlink(name, dir_fd=dir_fd))
            return hasher.hexdigest(), b""
        if not stat.S_ISREG(st.st_mode):
            hasher.update(f"type:{stat.S_IFMT(st.st_mode)}:{mode:o}".encode())
            return hasher.hexdigest(), b""
        fd = os.open(name, _FILE_FLAGS, dir_fd=dir_fd)
        try:
            opened = os.fstat(fd)
            if _identity(opened) != _identity(st) or not stat.S_ISREG(opened.st_mode):
                return "error:raced", b""
            mode = stat.S_IMODE(opened.st_mode)
            if opened.st_size <= FULL_HASH_BYTES:
                data = _read(fd, FULL_HASH_BYTES + 1)
                self.read_bytes += len(data)
                hasher.update(f"file:{mode:o}:{len(data)}\x00".encode() + data)
                return hasher.hexdigest(), data[:2]
            head = os.pread(fd, CHUNK_BYTES, 0)
            tail = os.pread(fd, CHUNK_BYTES, max(0, opened.st_size - CHUNK_BYTES))
            self.read_bytes += len(head) + len(tail)
            meta = (mode, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns, opened.st_dev, opened.st_ino)
            hasher.update("large:{:o}:{}:{}:{}:{}:{}\x00".format(*meta).encode() + head + b"\x00" + tail)
            return hasher.hexdigest(), head[:2]
        finally:
            os.close(fd)

    def _claude_json(self, path: bytes, st: os.stat_result, category: str) -> None:
        """``~/.claude.json`` by its security-relevant keys; the whole file when it is not a JSON object."""
        data = b""
        if stat.S_ISREG(st.st_mode) and st.st_size <= CLAUDE_JSON_BYTES:
            data = self.read(path, limit=CLAUDE_JSON_BYTES) or b""
            self.read_bytes += len(data)
        try:
            document = json.loads(data)
            selected = _claude_json_entries(document) if isinstance(document, dict) else None
        except (ValueError, RecursionError):  # not JSON, or nested deeper than the parser goes
            selected = None
        if selected is None:
            try:
                digest, _ = self._digest(None, path, st)
            except OSError as exc:
                digest = f"error:{_errname(exc)}"
            self._record(path, category, digest)
            return
        label = self.label(path)
        for name, value in selected.items():
            key = path + b"#" + name.encode("utf-8", "surrogatepass")
            self._record(key, category, value, f"{label}: {printable(name)}")

    def _record(self, path: bytes, category: str, digest: str, label: str | None = None) -> None:
        self.entries[path] = (category, label or self.label(path), digest)

    def label(self, path: bytes) -> str:
        """``path`` relative to the workspace, as ``~/...`` under the first home, or absolute."""
        norm = os.path.normpath(path)
        home = self.homes[0] if self.homes else b""
        if norm == self.workspace or norm.startswith(self.workspace.rstrip(b"/") + b"/"):
            shown = norm[len(self.workspace) :].lstrip(b"/") or b"."
        elif home and (norm == home or norm.startswith(home.rstrip(b"/") + b"/")):
            shown = b"~" + norm[len(home.rstrip(b"/")) :]
        else:
            shown = norm
        return printable(shown)


class _GitConfig:
    """``name = value`` entries of git config files, following ``include.path`` and ``includeIf.*.path``."""

    def __init__(self, walker: _Walker, *, follow_includes: bool = True) -> None:
        self.walker = walker
        self.follow = follow_includes
        self.entries: list[tuple[str, str]] = []
        self.bases: list[bytes] = []  # the directory of the file each entry came from
        self.files: list[bytes] = []  # every config file named, read or not

    def load(self, path: bytes, *, base: bytes, depth: int = 0) -> None:
        self.files.append(path)
        data = self.walker.read(path)
        if data is None:
            return
        for name, value in parse_git_config(data):
            self.entries.append((name, value))
            self.bases.append(base)
            if not self.follow or depth >= MAX_INCLUDE_DEPTH or not name.endswith(".path"):
                continue
            if name == "include.path" or name.startswith("includeif."):
                included = _join(os.path.dirname(path), os.fsencode(value), self.walker.home)
                self.load(included, base=os.path.dirname(included), depth=depth + 1)

    def values(self, name: str) -> list[bytes]:
        return [os.fsencode(value) for key, value in self.entries if key == name and value]

    def programs(self) -> Iterable[bytes]:
        """Programs named by path in command keys (``core.fsmonitor``, filters, ``!`` aliases, ...)."""
        for name, value in self.entries:
            if not _is_command(name, value):
                continue
            text = value[1:] if value.startswith("!") else value
            try:
                words = shlex.split(text)
            except ValueError:
                words = text.split()
            if words and "/" in words[0]:
                yield os.fsencode(words[0])


def parse_git_config(data: bytes) -> list[tuple[str, str]]:
    """``(name, value)`` pairs of a git config file, as git reads them, closely enough for discovery.

    Names are ``section.key`` or ``section.subsection.key``, section and key lowercased; a key
    without ``=`` is ``"true"``. Quotes, escapes, comments and continuation lines are handled.
    Malformed lines are skipped.
    """
    text = data.decode("utf-8", "surrogateescape")
    entries: list[tuple[str, str]] = []
    section: str | None = None
    pos, end = 0, len(text)
    while pos < end:
        char = text[pos]
        if char in " \t\r\n":
            pos += 1
        elif char in "#;":
            pos = _line_end(text, pos)
        elif char == "[":
            section, pos = _section(text, pos)
        elif char.isalpha():
            start = pos
            while pos < end and (text[pos].isalnum() or text[pos] == "-"):
                pos += 1
            key = text[start:pos].lower()
            while pos < end and text[pos] in " \t":
                pos += 1
            if pos < end and text[pos] == "=":
                value, pos = _value(text, pos + 1)
            elif pos >= end or text[pos] in "\r\n#;":
                value = "true"
            else:
                pos = _line_end(text, pos)
                continue
            if section is not None:
                entries.append((f"{section}.{key}", value))
        else:
            pos = _line_end(text, pos)
    return entries


def _section(text: str, pos: int) -> tuple[str | None, int]:
    end = len(text)
    pos += 1
    start = pos
    while pos < end and (text[pos].isalnum() or text[pos] in ".-"):
        pos += 1
    name = text[start:pos].lower()
    if pos < end and text[pos] in " \t":
        while pos < end and text[pos] in " \t":
            pos += 1
        if pos >= end or text[pos] != '"':
            return None, _line_end(text, pos)
        pos += 1
        sub: list[str] = []
        while pos < end and text[pos] not in '"\n':
            if text[pos] == "\\" and pos + 1 < end and text[pos + 1] != "\n":
                pos += 1
            sub.append(text[pos])
            pos += 1
        if pos >= end or text[pos] != '"' or not text.startswith('"]', pos):
            return None, _line_end(text, pos)
        return (f"{name}.{''.join(sub)}" if name else None), pos + 2
    if pos >= end or text[pos] != "]" or not name:
        return None, _line_end(text, pos)
    section, _, sub_name = name.partition(".")  # deprecated [section.subsection]
    return (f"{section}.{sub_name}" if sub_name else section), pos + 1


def _value(text: str, pos: int) -> tuple[str, int]:
    end = len(text)
    while pos < end and text[pos] in " \t":
        pos += 1
    out: list[str] = []
    space = ""
    quoted = False
    while pos < end:
        char = text[pos]
        if char == "\n":
            break
        if char == "\\":
            following = text[pos + 1 : pos + 2]
            if following == "\n":
                pos += 2
                continue
            if text.startswith("\r\n", pos + 1):
                pos += 3
                continue
            out.append(space)
            space = ""
            out.append({"n": "\n", "t": "\t", "b": "\b"}.get(following, following))
            pos += 2
            continue
        if char == '"':
            out.append(space)
            space = ""
            quoted = not quoted
            pos += 1
            continue
        if not quoted and char in "#;":
            return "".join(out), _line_end(text, pos)
        if not quoted and char in " \t\r":
            space += char
            pos += 1
            continue
        out.append(space)
        space = ""
        out.append(char)
        pos += 1
    return "".join(out), pos


def _line_end(text: str, pos: int) -> int:
    newline = text.find("\n", pos)
    return len(text) if newline < 0 else newline + 1


def _is_command(name: str, value: str) -> bool:
    if name.startswith("alias.") or (name.startswith("submodule.") and name.endswith(".update")):
        return value.startswith("!")
    if name in _GIT_COMMANDS:
        return value.lower() not in _GIT_BOOLEANS
    section = name.split(".", 1)[0]
    if section in ("filter", "merge", "diff", "gpg", "credential", "pager", "remote"):
        return (
            name.endswith(_GIT_COMMAND_SUFFIXES) or section == "pager" or name.endswith((".receivepack", ".uploadpack"))
        )
    return False


def _global_git_configs(home: bytes) -> list[bytes]:
    paths = [b"/etc/gitconfig"]
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        paths.append(os.fsencode(xdg) + b"/git/config")
    if home:
        paths.extend([home + b"/.config/git/config", home + b"/.gitconfig"])
    return list(dict.fromkeys(paths))


def _join(base: bytes, value: bytes, home: bytes) -> bytes:
    """``value`` as git takes a path: up to a NUL byte (a C string), ``~/`` from ``home``,
    relative to ``base``; never normalized."""
    value = value.split(b"\x00", 1)[0]
    if value == b"~" or value.startswith(b"~/"):
        return home + value[1:]
    if value.startswith(b"/"):
        return value
    return base.rstrip(b"/") + b"/" + value


def _child_rule(rule: str, name: bytes) -> tuple[str, str | None] | None:
    """``(rule, category or None to inherit)`` for an entry named ``name`` below a directory, or None to skip it."""
    if rule in ("all", "code"):
        return ("git", None) if name == b".git" else (rule, None)
    if rule == "hooks":  # git never runs a hook named *.sample
        return None if name.endswith(b".sample") else ("hooks", None)
    if rule == "git":  # a .git directory found inside a compared tree: its config and hooks only
        if name in (b"config", b"config.worktree", b"commondir"):
            return "all", None
        return ("hooks", None) if name == b"hooks" else None
    text = os.fsdecode(name)
    if rule == "claude-home":
        if text in CLAUDE_HOME_DATA:
            return None
        if text in CLAUDE_INSTRUCTIONS:
            return "all", INSTRUCTIONS
        return ("all" if text in CLAUDE_HOME_CODE else "code"), None
    if rule == "codex-home":
        if text in CODEX_HOME_DATA:
            return None
        if text in CODEX_INSTRUCTIONS:
            return "all", INSTRUCTIONS
        return ("all" if text in CODEX_HOME_CODE else "code"), None
    if rule == "claude-project":  # instruction files are project content; worktrees are checkouts
        if text in CLAUDE_INSTRUCTIONS or text in CLAUDE_PROJECT_DATA:
            return None
        return "all", None
    return None


def _looks_like_code(name: bytes, st: os.stat_result, head: bytes) -> bool:
    if stat.S_ISLNK(st.st_mode):
        return True
    return bool(st.st_mode & 0o111) or head.startswith(b"#!") or name.lower().endswith(CODE_SUFFIXES)


def _claude_json_entries(document: dict[str, object]) -> dict[str, str]:
    """``{name: digest}`` of the security-relevant keys of ``~/.claude.json``, and of each project's."""
    entries = {key: _json_digest(value) for key, value in _relevant(document).items()}
    projects = document.get("projects")
    if isinstance(projects, dict):
        for project, settings in projects.items():
            relevant = _relevant(settings) if isinstance(settings, dict) else {}
            if relevant:
                entries[f"projects[{project}]"] = _json_digest(relevant)
    return entries


def _relevant(settings: dict[str, object]) -> dict[str, object]:
    found: dict[str, object] = {}
    for key, value in settings.items():
        lowered = key.lower()
        if lowered in CLAUDE_JSON_KEYS or any(pattern in lowered for pattern in CLAUDE_JSON_PATTERNS):
            found[key] = value
    return found


def _json_digest(value: object) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return blake3(_DOMAIN + b"json\x00" + text.encode()).hexdigest()


def _read(fd: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while size < limit:
        chunk = os.read(fd, min(limit - size, 1024 * 1024))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
    return b"".join(chunks)


def _identity(st: os.stat_result) -> Identity:
    return st.st_dev, st.st_ino


def _chain(path: bytes) -> list[Identity]:
    try:
        return ancestry(os.fsdecode(path))
    except OSError:
        return []


def _physical_chain(path: bytes, st: os.stat_result) -> list[Identity]:
    """Identities of ``path`` itself (never followed) and of its physical ancestors."""
    if stat.S_ISDIR(st.st_mode):
        return ancestry(os.fsdecode(path))
    return [_identity(st), *ancestry(os.fsdecode(os.path.dirname(path) or b"/"))]


def _fd_chain(dir_fd: int, path: bytes) -> list[Identity]:
    """Physical ancestry of the directory open at ``dir_fd`` (through ``/proc`` where it exists)."""
    if os.path.isdir("/proc/self/fd"):
        return ancestry(f"/proc/self/fd/{dir_fd}")
    return ancestry(os.fsdecode(path))


def _errname(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, str(exc.errno))
