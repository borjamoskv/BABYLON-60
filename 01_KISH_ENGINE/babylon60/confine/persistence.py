"""Files an agent can leave behind that run, or steer an agent, outside the sandbox later.

``babylon60 run`` takes a ``snapshot`` before the session and another one after
it; ``changes`` names, by path, what was added, modified or removed in between.
This is detection, not prevention: inside its write grants the agent can still
write these files, and the report makes that visible.

Only what a write grant of the policy reaches is compared: a path is writable
when the identity ``(st_dev, st_ino)`` of a granted directory or file is among
its physical ancestors, as Landlock decides. A link is resolved (``realpath``)
only to find a target to look at; whether that target is writable is decided the
same way. Material outside the write grants cannot change and is skipped. The
snapshot after the session runs outside the sandbox, so nothing here runs git or
any other program: every file is parsed here, and nothing found is ever executed.

Code and configuration (``Report.code``):

* Every project (the workspace and each directory granted with ``--allow-write``)
  is walked once, breadth first, up to ``MAX_TREE_ENTRIES`` names and
  ``MAX_DEPTH`` levels. Directories are listed by entry type: an ordinary file
  is never ``stat``-ed, and nothing is listed below ``.git``, a known gitdir or
  the agents' data directories. In every directory reached:

  - the files that git hook managers, direnv, package and environment
    managers, editors and coding agents read from a project directory
    (``HOOK_MANAGERS``, ``PROJECT_FILES``, ``*.code-workspace``, the run
    configurations of ``.idea/workspace.xml``), and the agents' directories:
    ``.claude`` but for its data and instruction files, and ``.cursor``,
    ``.gemini``, ``.windsurf``, ``.continue``, ``.roo``, ``.kilocode`` and
    ``.amazonq`` whole (their rule, mode, workflow, prompt and command files as
    instructions, their ``mcp.json`` and the rest as code, ``AGENT_PROJECT_DIRS``);
  - a nested repository, compared like the one around the project;
  - ``node_modules/.bin``, the ``bin`` (``Scripts``) of a virtual environment,
    and the ``*.pth``, ``sitecustomize.py`` and ``usercustomize.py`` that an
    interpreter runs at startup from any ``site-packages``: dependency
    directories are usually kept out of the repository, so out of its diff.

* In every repository found (around a project, nested in one, submodules and
  linked worktrees): git hooks wherever they live (``<gitdir>/hooks`` and every
  ``core.hooksPath`` of the system, global, repository and worktree configs,
  relative ones taken from the working tree), the config files with every
  ``include.path`` and ``includeIf.*.path`` (one holding only what ``git init``
  writes runs nothing and is not recorded), ``.git`` files that point to a
  gitdir, ``commondir``, the programs that git config names by path (every word
  with a slash of a command value, and the script a shell or an interpreter is
  given: ``core.fsmonitor``, filters, drivers, ``alias.*`` with ``!``, merge and
  diff tools, ``interactive.diffFilter`` and the other command keys), and what
  hides a change from ``git status`` and ``git diff``: ``info/exclude`` and the
  file ``core.excludesFile`` names, by their patterns, and the paths that the
  index marks assume-unchanged or skip-worktree (``.git/index: skip-worktree
  Makefile``), read from the index itself (versions 2 to 4, split or not).
  A file that a config includes, by any name and however often (loops too), is
  read once for that config, and ``MAX_INCLUDES`` included files are read per
  snapshot (past it they are compared, not read). The index is read in
  place: ``MAX_HIDDEN`` hidden paths (``HIDDEN_NAMED_BYTES`` of them) are named
  one by one, more are compared as one set by a digest and a count, and an index
  whose hidden paths add up to more than ``INDEX_PATH_BYTES`` (version 4
  rebuilds each path from the one before it, so a small file can describe a
  great deal) is named in ``Report.unchecked``.

* Under every home directory: what Claude Code and Codex load or run (settings,
  hooks, plugins, commands, agents, skills, output styles, ``~/.codex/rules``,
  ``config.toml`` and ``.env``, the local launcher ``~/.claude/local``, and
  scripts and executables anywhere else in ``~/.claude`` and ``~/.codex`` but
  their data directories), ``~/.claude.json`` by its security-relevant keys only
  (``CLAUDE_JSON_KEYS``: MCP servers, hooks, permissions, trust, API-key and
  external-include approvals, never its counters and caches), the global files
  of other coding agents (``HOME_AGENT_FILES``), common startup material
  (``HOME_STARTUP``: shell, tmux and direnv rc files, git config, user bin
  directories, autostart and systemd user units, package, environment manager
  and editor init files) and the ``*.pth`` of the user site-packages.

Instructions (``Report.instructions``): ``~/.claude/CLAUDE.md``,
``~/.claude/rules``, ``~/.codex/AGENTS.md``, every file those two pull in with
``@path`` (``MAX_IMPORT_DEPTH`` deep, whatever its name), Claude Code's
auto-memory (``~/.claude/projects/*/memory/*.md``), and, in every directory of
a project, ``CLAUDE.local.md``, the rule files of other agents
(``PROJECT_INSTRUCTIONS``) and every file that ``CLAUDE.md``,
``CLAUDE.local.md`` or ``.claude/CLAUDE.md`` there pulls in with ``@path``:
every later session of the agent reads them, also outside the sandbox, and no
repository diff shows them (``CLAUDE.local.md`` is kept out of the repository by
design, and so may be what it or ``CLAUDE.md`` imports). ``CLAUDE.md`` and
``AGENTS.md`` inside a project are project content, reviewed in its own diff:
not compared themselves. ``MAX_IMPORT_FILES`` files are followed for @imports
per snapshot.

A file is opened only after ``lstat`` shows a regular file, with ``O_NOFOLLOW``
and ``O_NONBLOCK``, and is compared by type, permission bits and content: whole
up to ``FULL_HASH_BYTES``; a larger (or sparse) file by size, modification and
change times, inode and its first and last ``CHUNK_BYTES``. Symbolic links are
compared by their target text; the link of a git hook, a hooks directory, a git
config, a home startup or agent file or an agent instruction file is also
followed once, so a target inside a write grant is compared as well. Other types
are compared by type and mode. Names are bytes, so any file name works; labels
escape what is not printable. Git configs, pointer files and instruction files
are read for discovery wherever they are, up to ``CONFIG_BYTES`` each and
``DISCOVERY_BYTES`` in all, never below ``/proc``, ``/sys`` or a protected path.
Limits per root (``MAX_ROOT_ENTRIES``, ``MAX_DEPTH``), per project
(``MAX_TREE_ENTRIES``), for git directories (``MAX_GITDIRS``) and per snapshot
(``MAX_ENTRIES``, ``MAX_READ_BYTES``) bound the work; reaching one is named in
``Report.unchecked``, and so is a project directory that cannot be listed (its
known names are still compared). A root, an index or a part of the search that
fails in any other way (even for want of memory) is named there too, and the
rest of the snapshot goes on: one failure never drops the whole report.

Not covered (declared limits): scripts that a configuration names outside these
locations (git config names by path excepted), targets of other symbolic links,
``.gitignore`` files (they can hide a new file from ``git status``),
configuration passed in ``GIT_CONFIG_*`` environment variables, and changes
reverted before the session ends.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
import errno
import heapq
import itertools
import json
import operator
import os
import re
import shlex
import stat
import struct

from blake3 import blake3

from babylon60.confine.policy import Identity, Policy, ancestry

CODE, INSTRUCTIONS = "code", "instructions"
# Report.ranks: which labels a report too long to show whole keeps first.
RANK_HOOK, RANK_GIT, RANK_SETTINGS, RANK_INSTRUCTIONS, RANK_OTHER = range(5)
FULL_HASH_BYTES = 256 * 1024  # files up to this size are compared by their whole content
CHUNK_BYTES = 64 * 1024  # larger files: metadata plus their first and last chunk
MAX_ROOT_ENTRIES = 20_000  # entries examined below one root
MAX_TREE_ENTRIES = 250_000  # names listed below one project while looking for nested configurations
MAX_ENTRIES = 100_000  # entries examined in one snapshot
MAX_READ_BYTES = 256 * 1024 * 1024  # bytes read in one snapshot
MAX_DEPTH = 32
CONFIG_BYTES = 1024 * 1024  # git config, include, pointer and instruction files read for discovery
DISCOVERY_BYTES = 64 * 1024 * 1024  # all of those, in one snapshot
MAX_PATH_BYTES = 64 * 1024  # a longer path in a git index makes it unreadable here (git's are far shorter)
CLAUDE_JSON_BYTES = 16 * 1024 * 1024  # larger, or not a JSON object: compared whole
INDEX_BYTES = 128 * 1024 * 1024  # a larger git index is named in Report.unchecked
MAX_HIDDEN = 1_000  # hidden index paths named one by one; more are compared as one set
HIDDEN_NAMED_BYTES = 1024 * 1024  # and at most this many bytes of them
INDEX_PATH_BYTES = 128 * 1024 * 1024  # hidden paths examined in one index (a split one with its shared index)
MAX_GITDIRS = 256  # git directories in one snapshot: repositories, submodules, linked worktrees
MAX_INCLUDE_DEPTH = 10  # git's own limit
MAX_INCLUDES = 1024  # git config files read through include.path and includeIf.*.path in one snapshot
MAX_IMPORT_DEPTH = 5  # Claude Code's own limit for @imports
MAX_IMPORTS = 64  # @import targets followed from one agent instruction file
MAX_IMPORT_FILES = 4096  # instruction files read or named to follow @imports in one snapshot
MAX_SEARCH_UP = 64  # parent directories searched for the repository around a project

_DOMAIN = b"BABYLON60-CONFINE-PERSISTENCE/v1\x00"
_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_NOCTTY | _CLOEXEC
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | _CLOEXEC

# Git hook managers, read from a project directory: compared in every directory of a project.
HOOK_MANAGERS = (
    ".husky",
    ".pre-commit-config.yaml",
    "lefthook.yml",
    ".lefthook.yml",
    "lefthook-local.yml",
    ".lefthook-local.yml",
)
# Read from a project directory by direnv, a package or environment manager, an editor or a coding
# agent, from a copy often kept out of the repository: compared as code in every directory of a project.
PROJECT_FILES = (
    ".envrc",
    ".mcp.json",
    ".codex",
    ".vscode/tasks.json",
    ".vscode/settings.json",
    ".vscode/mcp.json",
    ".vscode/launch.json",
    ".devcontainer",
    ".devcontainer.json",
    ".idea/runConfigurations",
    ".zed/settings.json",
    ".zed/tasks.json",
    ".aider.conf.yml",  # aider: lint-cmd, test-cmd and the files it reads
    ".npmrc",
    ".yarnrc",
    ".yarnrc.yml",
    ".pnpmfile.cjs",
    ".pnpmfile.js",
    ".pnpmfile.mjs",
    "bunfig.toml",
    ".mise.toml",
    ".mise.local.toml",
    "mise.toml",
    "mise.local.toml",
    ".mise/config.toml",
    ".config/mise",
    ".config/mise.toml",
    ".config/mise.local.toml",
    ".tool-versions",
)
# Instructions coding agents read from a project directory, kept out of the repository as often as
# not: compared as instructions in every directory of a project.
PROJECT_INSTRUCTIONS = (
    "CLAUDE.local.md",
    ".cursorrules",
    ".windsurfrules",
    ".clinerules",
    ".roorules",
    ".roomodes",
    ".kilocodemodes",
    ".github/copilot-instructions.md",
    ".github/instructions",
)
# Directories of coding agents in a project, compared whole: as code, but for these entries
# (instructions; a trailing * matches any rest of the name, as in Roo Code's rules-<mode>).
AGENT_PROJECT_DIRS = {
    ".cursor": ("rules", "commands"),
    ".gemini": ("GEMINI.md",),
    ".windsurf": ("rules", "workflows"),
    ".continue": ("rules", "prompts"),
    ".roo": ("rules", "rules-*", "modes"),
    ".kilocode": ("rules", "rules-*", "modes", "workflows"),
    ".amazonq": ("rules", "rules-*", "modes"),
}
# Instruction files in a project whose @imports are followed (the files themselves are project content).
PROJECT_IMPORTERS = ("CLAUDE.md", "CLAUDE.local.md", ".claude/CLAUDE.md")
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
    ".config/zsh",
    ".config/fish",
    ".tmux.conf",
    ".config/tmux",
    ".direnvrc",
    ".config/direnv",
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
    ".config/mise",
    ".tool-versions",
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
    ".config/Code/User/mcp.json",
)
# The global files of other coding agents under a home: (path, category).
HOME_AGENT_FILES = (
    (".gemini/settings.json", CODE),
    (".gemini/commands", CODE),
    (".gemini/GEMINI.md", INSTRUCTIONS),
    (".cursor/mcp.json", CODE),
    (".cursor/hooks.json", CODE),
    (".codeium/windsurf/mcp_config.json", CODE),
    (".aider.conf.yml", CODE),
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
        "projects",  # per-session data, but for the auto-memory in projects/*/memory (instructions)
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
CODEX_HOME_CODE = frozenset({".env", "config.toml", "prompts", "rules", "skills"})
CODEX_INSTRUCTIONS = frozenset({"AGENTS.md", "AGENTS.override.md"})
# ~/.claude.json keys, at the top level and in each ``projects`` entry, that change what runs, what
# is allowed without asking or what CLAUDE.md may pull in. Everything else there (counters, tips,
# caches) is not compared.
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
        "hasClaudeMdExternalIncludesApproved",
        "hasClaudeMdExternalIncludesWarningShown",
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
# Git config keys whose value is a command: the programs it names by path are compared.
_GIT_COMMANDS = frozenset(
    {
        "core.alternaterefscommand",
        "core.askpass",
        "core.editor",
        "core.fsmonitor",
        "core.gitproxy",
        "core.pager",
        "core.sshcommand",
        "credential.helper",
        "diff.external",
        "gpg.program",
        "gpg.ssh.defaultkeycommand",
        "interactive.difffilter",
        "sendemail.cccmd",
        "sendemail.sendmailcmd",
        "sendemail.smtpserver",
        "sendemail.tocmd",
        "sequence.editor",
        "uploadpack.packobjectshook",
    }
)
_GIT_COMMAND_SUFFIXES = (".clean", ".smudge", ".process", ".driver", ".textconv", ".command", ".program", ".helper")
_GIT_TOOL_SECTIONS = ("mergetool", "difftool", "browser", "man")  # <section>.<tool>.cmd and .path
_GIT_BOOLEANS = frozenset({"", "true", "false", "yes", "no", "on", "off", "1", "0"})
# A command word naming one of these runs its first argument: ``sh tools/x.sh``.
_SHELLS = frozenset({"sh", "bash", "dash", "zsh", "ksh", "fish", "python", "python3", "node", "perl", "ruby"})
# Only these lines: what ``git init`` writes, which runs nothing.
_INIT_CONFIG_LINE = re.compile(
    rb"\s*(?:\[(?:core|extensions)\]|(?:repositoryformatversion|filemode|bare|logallrefupdates|ignorecase"
    rb"|precomposeunicode|symlinks|objectformat|refstorage)\s*=\s*(?:true|false|0|1|sha1|sha256|files|reftable))\s*",
    re.IGNORECASE,
)
_IMPORT = re.compile(rb"(?:^|\s)@((?:[^\s\\]|\\ )+)")  # Claude Code's @path, a backslash escaping a space
_INLINE_CODE = re.compile(rb"`[^`\n]*`")


@dataclass(frozen=True)
class _Root:
    path: bytes
    category: str
    # "all", "code", "home", "hooks", "config", "pointer", "commondir", "index", "index-sha256", "exclude",
    # "file", "site-packages", "idea-workspace", "claude-home", "codex-home", "claude-project",
    # "agent-project:<dir>", "claude-json"
    rule: str
    expect: bytes | None = None  # "pointer": the gitdir git itself would have it name
    rank: int = RANK_OTHER
    follow: bool = False  # symbolic links in it are followed once, so a target in a write grant is compared


@dataclass(frozen=True)
class Snapshot:
    # key: (category, label, digest, rank)
    entries: dict[bytes, tuple[str, str, str, int]] = field(default_factory=dict)
    unchecked: tuple[str, ...] = ()  # roots not compared in full, and why
    roots: tuple[_Root, ...] = ()  # where it looked, so a later snapshot looks there too


@dataclass(frozen=True)
class Report:
    code: tuple[str, ...]  # labels of code and configuration added, modified or removed
    instructions: tuple[str, ...]  # labels of agent instruction files added, modified or removed
    unchecked: tuple[str, ...]  # roots not compared in full in either snapshot
    # label: RANK_* (git hooks, git configs and the programs they name, settings, instructions, the rest)
    ranks: Mapping[str, int] = field(default_factory=dict, hash=False)


class _Stop(Exception):
    """A limit was reached below the current root."""


# (path relative to a project directory, category, rule, rank), compared in every directory of a project.
_PROJECT: tuple[tuple[bytes, str, str, int], ...] = (
    *((name.encode(), CODE, "all", RANK_HOOK) for name in HOOK_MANAGERS),
    *((name.encode(), CODE, "all", RANK_SETTINGS) for name in PROJECT_FILES),
    *((name.encode(), INSTRUCTIONS, "all", RANK_INSTRUCTIONS) for name in PROJECT_INSTRUCTIONS),
    (b".idea/workspace.xml", CODE, "idea-workspace", RANK_SETTINGS),
    (b".claude", CODE, "claude-project", RANK_SETTINGS),
    *((name.encode(), CODE, f"agent-project:{name}", RANK_SETTINGS) for name in AGENT_PROJECT_DIRS),
)
_PROJECT_BY_NAME: dict[bytes, list[tuple[bytes, str, str, int]]] = {}
for _entry in _PROJECT:
    _PROJECT_BY_NAME.setdefault(_entry[0].split(b"/", 1)[0], []).append(_entry)
_IMPORTERS = frozenset(name.encode() for name in PROJECT_IMPORTERS if "/" not in name)
_TREE_NAMES = frozenset(
    {*_PROJECT_BY_NAME, *_IMPORTERS, b".git", b"node_modules", b"site-packages", b"dist-packages", b"pyvenv.cfg"}
)
# Directories the project walk never lists, by the name of the directory holding them: agent data.
_TREE_PRUNED = {
    b".claude": frozenset(os.fsencode(name) for name in CLAUDE_HOME_DATA | CLAUDE_PROJECT_DATA),
    b".codex": frozenset(os.fsencode(name) for name in CODEX_HOME_DATA),
}
_NOTHING: frozenset[bytes] = frozenset()


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
            try:
                walker.walk(root)
            except Exception as exc:  # even MemoryError: one root never drops the rest of the report
                walker.unchecked.append(f"{walker.label(root.path)} ({type(exc).__name__}: not compared)")
    for root in walker.followed:
        walked.setdefault(root.path, root)
    return Snapshot(walker.entries, tuple(dict.fromkeys(walker.unchecked)), tuple(walked.values()))


def changes(before: Snapshot, after: Snapshot) -> Report:
    """Labels of what was added, modified or removed between two snapshots, by category."""
    code: set[str] = set()
    instructions: set[str] = set()
    ranks: dict[str, int] = {}
    for key in before.entries.keys() | after.entries.keys():
        old, new = before.entries.get(key), after.entries.get(key)
        if old is not None and new is not None and old[2] == new[2]:
            continue
        category, label, _, rank = new if new is not None else before.entries[key]
        (instructions if category == INSTRUCTIONS else code).add(label)
        ranks[label] = min(rank, ranks.get(label, rank))
    unchecked = tuple(dict.fromkeys([*before.unchecked, *after.unchecked]))
    return Report(tuple(sorted(code)), tuple(sorted(instructions)), unchecked, ranks)


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
        self.entries: dict[bytes, tuple[str, str, str, int]] = {}
        self.unchecked: list[str] = []
        self.walked: set[Identity] = set()  # directories compared, under the first name that reached them
        self.recorded: set[Identity] = set()  # other entries compared, likewise
        self.trees: set[Identity] = set()  # directories the project walk listed
        self.gitdirs: set[bytes] = set()  # git directories looked at
        self.gitdirs_full = False
        self.followed: list[_Root] = []  # targets of symbolic links compared as well
        self.total = 0
        self.read_bytes = 0
        self.limited = False
        self.discovered = 0  # bytes read to find what to compare (configs, pointers, instruction files)
        self.discovery_full = False
        self.includes = 0  # git config files read through an include
        self.imports = 0  # instruction files read or named to follow @imports

    # --- what to compare ------------------------------------------------------------------------

    def roots(self) -> Iterator[_Root]:
        projects = [self.workspace]
        for grant in self.policy.grants:
            if grant.access == "rw" and grant.is_dir and grant.origin == "user":
                projects.append(os.fsencode(grant.path))
        projects = list(dict.fromkeys(projects))
        global_config = _GitConfig(self)
        yield from self._guarded("the global git configs", self._global_roots(global_config))
        for project in projects:
            yield from self._guarded(self.label(project), self._project_roots(project, global_config))
        for home in self.homes:
            yield from self._guarded(self.label(home), self._home_roots(home))
        for project in projects:  # last: what the roots above name first keeps their rule
            yield from self._guarded(self.label(project), self._tree(project, global_config))

    def _guarded(self, what: str, roots: Iterator[_Root]) -> Iterator[_Root]:
        """``roots`` until finding them fails, whatever the reason (even want of memory): the failure is
        named in ``Report.unchecked`` and the snapshot goes on with the next part."""
        try:
            yield from roots
        except Exception as exc:  # one failing part never drops the rest of the report
            self.unchecked.append(f"{what} ({type(exc).__name__}: the rest of what it names not compared)")

    def _global_roots(self, global_config: _GitConfig) -> Iterator[_Root]:
        for path in _global_git_configs(self.home):
            global_config.load(path)
        yield from (_Root(path, CODE, "config", rank=RANK_GIT, follow=True) for path in global_config.files)

    def _project_roots(self, project: bytes, global_config: _GitConfig) -> Iterator[_Root]:
        repository = self._repository(project)
        if repository is not None:
            yield from self._git_roots(repository, global_config)
        for relative, category, rule, rank in _PROJECT:
            yield _Root(project + b"/" + relative, category, rule, rank=rank)

    def _home_roots(self, home: bytes) -> Iterator[_Root]:
        yield _Root(home + b"/.claude", CODE, "claude-home", rank=RANK_SETTINGS)
        yield _Root(home + b"/.claude.json", CODE, "claude-json", rank=RANK_SETTINGS)
        yield _Root(home + b"/.codex", CODE, "codex-home", rank=RANK_SETTINGS)
        for name in HOME_STARTUP:
            yield _Root(home + b"/" + name.encode(), CODE, "home", rank=RANK_SETTINGS, follow=True)
        for name, category in HOME_AGENT_FILES:
            yield _Root(home + b"/" + name.encode(), category, "all", rank=RANK_SETTINGS, follow=True)
        for version in self._listdir(home + b"/.local/lib"):  # user site-packages
            if version.startswith(b"python"):
                path = home + b"/.local/lib/" + version + b"/site-packages"
                yield _Root(path, CODE, "site-packages", rank=RANK_SETTINGS)
        for version in self._listdir(home + b"/Library/Python"):
            path = home + b"/Library/Python/" + version + b"/lib/python/site-packages"
            yield _Root(path, CODE, "site-packages", rank=RANK_SETTINGS)
        for path in (home + b"/.claude/CLAUDE.md", home + b"/.codex/AGENTS.md", home + b"/.codex/AGENTS.override.md"):
            yield _Root(path, INSTRUCTIONS, "file", rank=RANK_INSTRUCTIONS, follow=True)
            yield from self._imports(path, home)

    def _imports(self, start: bytes, home: bytes) -> Iterator[_Root]:
        """Files the agent instruction file ``start`` pulls in with ``@path``, and those they pull in.

        A relative path is taken from the importing file's directory (and from its target's, when it
        is a link), ``~`` from ``home``; ``MAX_IMPORT_DEPTH`` hops and ``MAX_IMPORTS`` files at most,
        and ``MAX_IMPORT_FILES`` files read or named per snapshot, for every start together.
        """
        pending: deque[tuple[bytes, int]] = deque([(start, 0)])
        seen = {start}
        while pending:
            path, depth = pending.popleft()
            if depth >= MAX_IMPORT_DEPTH:
                continue
            if not self._import_budget(start):
                return
            data = self.discover(path)  # the agent reads through a link
            if data is None:
                continue
            bases = [os.path.dirname(path)]
            if os.path.islink(path):
                bases.append(os.path.dirname(os.path.realpath(path)))
            for value in _import_paths(data):
                for base in bases:
                    target = _join(base, value, home)
                    if target in seen:
                        continue
                    if len(seen) > MAX_IMPORTS:
                        self.unchecked.append(
                            f"{self.label(start)} (more than {MAX_IMPORTS} @imports: the rest not compared)"
                        )
                        return
                    if not self._import_budget(start):
                        return
                    seen.add(target)
                    yield _Root(target, INSTRUCTIONS, "file", rank=RANK_INSTRUCTIONS, follow=True)
                    pending.append((target, depth + 1))

    def _import_budget(self, start: bytes) -> bool:
        """Whether one more file may be read or named to follow @imports (``MAX_IMPORT_FILES`` per snapshot);
        the first time not, ``start`` is named in ``Report.unchecked``."""
        self.imports += 1
        if self.imports <= MAX_IMPORT_FILES:
            return True
        if self.imports == MAX_IMPORT_FILES + 1:
            self.unchecked.append(
                f"{self.label(start)} and what follows it (more than {MAX_IMPORT_FILES} files followed for "
                "@imports: the rest not compared)"
            )
        return False

    def include(self, top: bytes) -> bool:
        """Whether one more included git config may be read (``MAX_INCLUDES`` per snapshot); the first
        time not, the config ``top`` that includes it is named in ``Report.unchecked``."""
        self.includes += 1
        if self.includes <= MAX_INCLUDES:
            return True
        if self.includes == MAX_INCLUDES + 1:
            self.unchecked.append(
                f"{self.label(top)} and what follows it (more than {MAX_INCLUDES} included git configs read: what "
                "the rest name is not compared)"
            )
        return False

    def _tree(self, project: bytes, global_config: _GitConfig) -> Iterator[_Root]:
        """The project rules in every directory below ``project``, breadth first and listed once.

        Directories are told apart by their entry type (``d_type``): an ordinary file is never
        ``stat``-ed. ``.git``, known gitdirs and agent data directories are not listed.
        """
        left = MAX_TREE_ENTRIES
        deep = False
        pending: deque[tuple[bytes, int]] = deque([(project, 0)])
        while pending:
            path, depth = pending.popleft()
            try:
                st = os.lstat(path)
            except OSError:
                continue
            ident = (st.st_dev, st.st_ino)
            if not stat.S_ISDIR(st.st_mode) or ident in self.trees:
                continue
            self.trees.add(ident)
            pruned = _TREE_PRUNED.get(os.path.basename(path), _NOTHING)
            found: list[tuple[bytes, bool]] = []
            full = False
            try:
                with os.scandir(path) as items:
                    for item in items:
                        left -= 1
                        if left < 0:
                            full = True
                            break
                        name = item.name
                        directory = item.is_dir(follow_symlinks=False)
                        if name in _TREE_NAMES or name.endswith(b".code-workspace"):
                            found.append((name, directory))
                        if directory and name != b".git" and name not in pruned and item.path not in self.gitdirs:
                            if depth < MAX_DEPTH:
                                pending.append((item.path, depth + 1))
                            else:
                                deep = True
            except OSError as exc:
                # A directory that cannot be listed (mode 0311) still lets a tool open a name in it:
                # those names are compared, and what lies deeper is named as not compared.
                self.unchecked.append(f"{self.label(path)} ({_errname(exc)}: nested configs below not compared)")
                found = [(b".git", True), *((name, False) for name in (*_PROJECT_BY_NAME, *_IMPORTERS))]
            yield from self._tree_found(path, found, depth, global_config)
            if full:
                self.unchecked.append(
                    f"{self.label(project)} (more than {MAX_TREE_ENTRIES} entries: nested configs beyond this point "
                    "not compared)"
                )
                return
        if deep:
            self.unchecked.append(
                f"{self.label(project)} (deeper than {MAX_DEPTH} levels: nested configs below not compared)"
            )

    def _tree_found(
        self, path: bytes, found: list[tuple[bytes, bool]], depth: int, global_config: _GitConfig
    ) -> Iterator[_Root]:
        for name, directory in found:
            # What a project's CLAUDE.md, CLAUDE.local.md or .claude/CLAUDE.md pulls in with @path, whatever
            # its depth: an import target kept out of the repository is in no diff.
            if name in _IMPORTERS and not directory:
                yield from self._imports(path + b"/" + name, self.home)
            elif name == b".claude":
                yield from self._imports(path + b"/.claude/CLAUDE.md", self.home)
            if name == b"CLAUDE.md":
                continue  # project content, compared in its own diff
            if name == b".git":
                if depth:  # the project's own repository was looked at first
                    yield from self._git_roots(path, global_config)
            elif name == b"node_modules":
                if directory:
                    yield _Root(path + b"/node_modules/.bin", CODE, "all")
            elif name in (b"site-packages", b"dist-packages"):
                if directory:
                    yield _Root(path + b"/" + name, CODE, "site-packages", rank=RANK_SETTINGS)
            elif name == b"pyvenv.cfg":  # a virtual environment: its launchers
                yield _Root(path + b"/pyvenv.cfg", CODE, "all", rank=RANK_SETTINGS)
                yield _Root(path + b"/bin", CODE, "all")
                yield _Root(path + b"/Scripts", CODE, "all")
            elif name.endswith(b".code-workspace"):
                yield _Root(path + b"/" + name, CODE, "all", rank=RANK_SETTINGS)
            elif depth:  # in the project's own directory, every project file was named already
                for relative, category, rule, rank in _PROJECT_BY_NAME[name]:
                    yield _Root(path + b"/" + relative, category, rule, rank=rank)

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
            yield _Root(dotgit, CODE, "all", rank=RANK_GIT)  # a gitdir pointer, or a link
        if stat.S_ISDIR(st.st_mode):
            gitdir: bytes | None = dotgit
        elif stat.S_ISLNK(st.st_mode) and os.path.isdir(dotgit):  # git follows a .git link to a directory
            gitdir = os.path.realpath(dotgit)
        else:
            gitdir = self._pointer(dotgit, worktree)
        if gitdir is None:
            return
        queue: deque[tuple[bytes, bytes | None]] = deque([(gitdir, worktree)])
        while queue:
            gitdir, tree = queue.popleft()
            if gitdir in self.gitdirs:
                continue
            if len(self.gitdirs) >= MAX_GITDIRS:
                if not self.gitdirs_full:
                    self.gitdirs_full = True
                    self.unchecked.append(
                        f"{self.label(dotgit)} (more than {MAX_GITDIRS} git directories: hooks and configs of the "
                        "rest not compared)"
                    )
                return
            self.gitdirs.add(gitdir)
            common = gitdir
            pointer = self.discover(gitdir + b"/commondir", limit=4096, follow=False)
            if pointer is not None:
                yield _Root(gitdir + b"/commondir", CODE, "commondir", rank=RANK_GIT)
                common = _join(gitdir, pointer.strip(), self.home)
            config = _GitConfig(self)
            config.load(common + b"/config")
            config.load(gitdir + b"/config.worktree")
            yield from (_Root(path, CODE, "config", rank=RANK_GIT, follow=True) for path in config.files)
            for value in config.values("core.worktree"):
                tree = _join(gitdir, value, self.home)
            sha256 = any(value.lower() == b"sha256" for value in config.values("extensions.objectformat"))
            yield _Root(gitdir + b"/index", CODE, "index-sha256" if sha256 else "index", rank=RANK_GIT)
            yield _Root(common + b"/info/exclude", CODE, "exclude", rank=RANK_GIT)
            yield _Root(common + b"/hooks", CODE, "hooks", rank=RANK_HOOK, follow=True)
            for source in (config, global_config):
                for value in source.values("core.hookspath"):
                    yield _Root(_join(tree or gitdir, value, self.home), CODE, "hooks", rank=RANK_HOOK, follow=True)
                for value in source.values("core.excludesfile"):
                    yield _Root(_join(tree or gitdir, value, self.home), CODE, "exclude", rank=RANK_GIT)
                for program in source.programs():
                    yield _Root(_join(tree or gitdir, program, self.home), CODE, "all", rank=RANK_GIT)
            # Submodule checkouts: a .git file naming the module's gitdir, or an old .git directory.
            if tree is not None:
                for name, path in self._submodules(tree):
                    checkout = _join(tree, path, self.home)
                    if os.path.isdir(checkout + b"/.git") and not os.path.islink(checkout + b"/.git"):
                        queue.append((checkout + b"/.git", checkout))
                        continue
                    module = common + b"/modules/" + name
                    yield _Root(checkout + b"/.git", CODE, "pointer", module, rank=RANK_GIT)
                    try:
                        declared = os.path.isdir(module)
                    except ValueError:  # a submodule name with a NUL byte
                        declared = False
                    if declared:  # before the scan below: modules it finds cannot push these past MAX_GITDIRS
                        queue.append((module, checkout))
            for module in self._module_gitdirs(common + b"/modules"):
                queue.append((module, None))
            if common == gitdir:  # linked worktrees: the admin directory and the .git file of the checkout
                for linked in self._listdir(common + b"/worktrees"):
                    entry = common + b"/worktrees/" + linked
                    target = self.discover(entry + b"/gitdir", limit=4096, follow=False)
                    linked_tree = None
                    if target is not None and target.strip():
                        linked_pointer = _join(entry, target.strip(), self.home)
                        yield _Root(linked_pointer, CODE, "pointer", entry, rank=RANK_GIT)
                        linked_tree = os.path.dirname(linked_pointer)
                    queue.append((entry, linked_tree))

    def _pointer(self, dotgit: bytes, worktree: bytes) -> bytes | None:
        data = self.discover(dotgit, limit=4096, follow=False)
        if data is None:
            return None
        line = data.split(b"\n", 1)[0].strip()
        if not line.startswith(b"gitdir:"):
            return None
        return _join(worktree, line[len(b"gitdir:") :].strip(), self.home)

    def _submodules(self, tree: bytes) -> list[tuple[bytes, bytes]]:
        """``(name, path)`` of the submodules ``.gitmodules`` declares in the working tree ``tree``."""
        config = _GitConfig(self, follow_includes=False)
        config.load(tree + b"/.gitmodules")
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
        if pending:
            limit = f"{MAX_GITDIRS} submodule gitdirs" if found >= MAX_GITDIRS else f"{MAX_ROOT_ENTRIES} entries"
            self.unchecked.append(f"{self.label(modules)} (more than {limit}: the rest not compared)")

    def _listdir(self, path: bytes) -> list[bytes]:
        """Names in the directory ``path`` (not a link to one), sorted; empty when it cannot be listed."""
        try:
            fd = os.open(path, _DIR_FLAGS)
        except (OSError, ValueError):
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

    def discover(self, path: bytes, *, limit: int = CONFIG_BYTES, follow: bool = True) -> bytes | None:
        """``read`` for discovery (git configs, pointers, instruction files): through a final link as
        git and the agents read them, within ``DISCOVERY_BYTES`` per snapshot; beyond it nothing more
        is read for discovery, and that is named once in ``Report.unchecked``."""
        if self.discovered > DISCOVERY_BYTES:
            if not self.discovery_full:
                self.discovery_full = True
                self.unchecked.append(
                    f"{self.label(path)} and what follows it (more than {DISCOVERY_BYTES} bytes of configs and "
                    "instruction files read: what they name is not compared)"
                )
            return None
        data = self.read(path, limit=limit)
        if data is None and follow and os.path.islink(path):
            data = self.read(os.path.realpath(path), limit=limit)
        self.discovered += len(data or b"")
        return data

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
        # Every root counts: the project walk yields one per file it finds, as many as a project holds.
        self.total += 1
        if self.total > MAX_ENTRIES or self.read_bytes > MAX_READ_BYTES:
            if not self.limited:
                self.limited = True
                self.unchecked.append(f"{label} and what follows it (snapshot limits reached)")
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
        if root.follow and stat.S_ISLNK(st.st_mode):
            self._follow(root.path, root.category, root.rule, root.rank)
        writable = bool(self.rw.intersection(chain))
        try:
            if not stat.S_ISDIR(st.st_mode):
                if writable and not self._standard(root):
                    self._file(None, root.path, root.path, st, root.category, root.rule, root.rank)
                return
            if root.rule == "file":
                return  # an instruction file is a file
            if not writable and chain[0] not in self.on_path:
                if root.follow:
                    self._follow_links(root)
                return  # nothing below it can change
            if chain[0] in self.walked:
                return  # the same directory under another name
            self.walked.add(chain[0])
            fd = os.open(root.path, _DIR_FLAGS)
            try:
                if _identity(os.fstat(fd)) != chain[0]:
                    raise _Stop("changed while it was being compared")
                self._directory(
                    fd, root.path, root.rule, root.category, writable, 0, [MAX_ROOT_ENTRIES], root.rank, root.follow
                )
            finally:
                os.close(fd)
        except _Stop as stop:
            self.unchecked.append(f"{label} ({stop})")
        except OSError as exc:
            self.unchecked.append(f"{label} ({_errname(exc)})")

    def _follow(self, link: bytes, category: str, rule: str, rank: int) -> None:
        """Compare what the symbolic link ``link`` resolves to as well, where a write grant reaches it.

        Followed once: links found in the target are compared as links. A directory reached twice
        is compared once (``walked``), so a cycle ends.
        """
        try:
            target = os.path.realpath(link)
        except (OSError, ValueError):
            return
        if target == link:
            return
        root = _Root(target, category, rule, rank=rank)
        self.followed.append(root)
        self.walk(root)

    def _follow_links(self, root: _Root) -> None:
        """Targets of the symbolic links directly in ``root``, a directory that no write grant reaches."""
        links: list[bytes] = []
        try:
            with os.scandir(root.path) as items:
                for count, item in enumerate(items):
                    if count >= MAX_ROOT_ENTRIES:
                        break
                    if item.is_symlink():
                        links.append(item.path)
        except OSError:
            return
        for link in links:
            child = _child_rule(root.rule, os.path.basename(link))
            if child is not None:
                self._follow(link, child[1] or root.category, child[0], root.rank)

    def _standard(self, root: _Root) -> bool:
        """Whether ``root`` holds what git itself writes there (``git init``, ``git worktree add``,
        ``git submodule add``).

        A config with only what ``git init`` writes; ``commondir`` of a linked worktree, ``../..``;
        the ``.git`` file of a linked worktree or submodule checkout, naming the gitdir git made for
        it. Those run nothing and are not recorded, so making a repository, a worktree or a
        submodule is not reported; any other content is compared.
        """
        if root.rule == "config":
            data = self.read(root.path, limit=4097)
            return data is not None and len(data) <= 4096 and _init_config(data)
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
        self,
        fd: int,
        path: bytes,
        rule: str,
        category: str,
        writable: bool,
        depth: int,
        budget: list[int],
        rank: int,
        follow: bool,
    ) -> None:
        names: list[bytes] = []
        if rule == "claude-project-slug":  # only its memory: never list the sessions
            names.append(b"memory")
        else:
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
                    self._record(child_path, child_category, f"error:{_errname(exc)}", rank=rank)
                continue
            ident = _identity(st)
            child_writable = writable or ident in self.rw
            if not stat.S_ISDIR(st.st_mode):
                if child_writable:
                    self._file(fd, name, child_path, st, child_category, child_rule, rank)
                if follow and stat.S_ISLNK(st.st_mode):
                    self._follow(child_path, child_category, child_rule, rank)
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
                    self._record(child_path, child_category, f"error:{_errname(exc)}", rank=rank)
                continue
            try:
                if _identity(os.fstat(sub)) != ident:
                    raise _Stop("changed while it was being compared")
                self._directory(
                    sub, child_path, child_rule, child_category, child_writable, depth + 1, budget, rank, follow
                )
            finally:
                os.close(sub)

    def _file(
        self, dir_fd: int | None, name: bytes, path: bytes, st: os.stat_result, category: str, rule: str, rank: int
    ) -> None:
        """Compare one entry that is not a directory, once per identity: a file reachable under
        another name (through a linked worktree's ``commondir``, or a hard link) keeps the key of
        the first name that reached it."""
        if _identity(st) in self.recorded:
            return
        if rule == "claude-project-slug" or (rule == "memory" and not name.lower().endswith(b".md")):
            return  # session data: ~/.claude/projects holds a directory per project, its memory in markdown
        regular = stat.S_ISREG(st.st_mode)
        if rule == "claude-json":
            self.recorded.add(_identity(st))
            self._claude_json(path, st, category, rank)
            return
        if regular and rule in ("index", "index-sha256"):
            self.recorded.add(_identity(st))
            self._index(path, st, 32 if rule == "index-sha256" else 20, rank)
            return
        if regular and rule in ("exclude", "idea-workspace"):
            data = self.read(path, limit=CONFIG_BYTES + 1)
            if data is not None and len(data) <= CONFIG_BYTES:
                self.read_bytes += len(data)
                self.recorded.add(_identity(st))
                parts = _exclude_patterns(data) if rule == "exclude" else _idea_run_configs(data)
                if parts:  # nothing that hides or runs: not recorded
                    hasher = blake3(_DOMAIN + rule.encode() + b"\x00")
                    for part in parts:
                        hasher.update(part + b"\x00")
                    self._record(path, category, hasher.hexdigest(), rank=rank)
                return
            # larger than what is parsed, or raced: compared whole below
        try:
            digest, head = self._digest(dir_fd, name, st)
        except OSError as exc:
            digest, head = f"error:{_errname(exc)}", b""
        if rule == "code" and not _looks_like_code(name, st, head):
            return
        self.recorded.add(_identity(st))
        self._record(path, category, digest, rank=rank)

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

    def _claude_json(self, path: bytes, st: os.stat_result, category: str, rank: int) -> None:
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
            self._record(path, category, digest, rank=rank)
            return
        label = self.label(path)
        for name, value in selected.items():
            key = path + b"#" + name.encode("utf-8", "surrogatepass")
            self._record(key, category, value, f"{label}: {printable(name)}", rank)

    def _index(self, path: bytes, st: os.stat_result, hash_size: int, rank: int) -> None:
        """The paths a git index hides from ``git status`` and ``git diff``: one entry each, keyed
        beside the index (``.git/index: skip-worktree Makefile``); more than ``MAX_HIDDEN`` (or
        ``HIDDEN_NAMED_BYTES``), one set. An index that cannot be read in full is named, never fatal."""
        label = self.label(path)
        if st.st_size > INDEX_BYTES:
            self.unchecked.append(f"{label} (larger than {INDEX_BYTES} bytes: hidden paths not compared)")
            return
        data = self.read(path, limit=INDEX_BYTES)
        if data is None:
            return
        self.read_bytes += len(data)
        try:
            hidden = self._hidden(path, data, hash_size)
        except Exception as exc:  # malformed, beyond INDEX_PATH_BYTES, or even more than memory holds
            self.unchecked.append(f"{label} ({str(exc) or type(exc).__name__}: hidden paths not compared)")
            return
        if hidden.named is None:
            digest = hidden.hasher.hexdigest()
            self._record(path + b"\x00hidden", CODE, digest, f"{label}: {hidden.count} hidden paths", rank)
            return
        for flag, name in hidden.named:
            key = path + b"\x00" + flag.encode() + b"\x00" + name
            self._record(key, CODE, "hidden", f"{label}: {flag} {printable(name)}", rank)

    def _hidden(self, path: bytes, data: bytes, hash_size: int) -> _Hidden:
        """What the index at ``path`` (read as ``data``) hides, as git reads it: a split index with its
        shared index, its deleted entries left out and its replacements applied."""
        index = _IndexFile(data, hash_size)
        hidden = _Hidden()
        pathless = bytearray()
        for _, bits, name in index.scan([INDEX_PATH_BYTES], pathless):
            hidden.add(bits, name)
        hidden.flush()
        if index.link is None:
            if pathless:
                raise ValueError("entries without a path")
            return hidden
        # A split index: most entries live in the shared index beside it. Both list their entries in
        # git's order (by path), so merging the two keeps it, and each path's entries come together.
        shared_hash, at, stop = index.link
        shared_path = os.path.dirname(path) + b"/sharedindex." + shared_hash.hex().encode()
        shared_data = self.read(shared_path, limit=INDEX_BYTES)
        if shared_data is None:
            raise ValueError("split index without its shared index")
        self.read_bytes += len(shared_data)
        shared = _IndexFile(shared_data, hash_size)
        deleted: Iterator[int] = iter(())
        replaced: Iterator[int] = iter(())
        if at < stop:  # the delete bitmap, then the replace bitmap, both by position in the shared index
            deleted, at = _ewah(data, at, stop)
            replaced, at = _ewah(data, at, stop)
        overrides = heapq.merge(
            ((position, 0, 0) for position in deleted),
            ((position, 1, bits) for position, bits in zip(replaced, pathless)),
        )
        budget = [INDEX_PATH_BYTES]
        hidden = _Hidden()
        own = index.scan(budget, bytearray())  # entries the split index adds (its pathless ones counted above)
        for _, bits, name in heapq.merge(own, shared.scan(budget, None, overrides), key=_entry_path):
            hidden.add(bits, name)
        hidden.flush()
        if shared.link is not None:
            raise ValueError("not a shared index")
        if shared.applied != len(pathless):
            raise ValueError("split index replaces entries its shared index or its bitmap lacks")
        return hidden

    def _record(
        self, path: bytes, category: str, digest: str, label: str | None = None, rank: int = RANK_OTHER
    ) -> None:
        if category == INSTRUCTIONS:
            rank = RANK_INSTRUCTIONS
        elif rank == RANK_SETTINGS and path.lower().endswith(b".md"):
            rank = RANK_OTHER  # bulk command and skill markdown after the settings themselves
        self.entries[path] = (category, label or self.label(path), digest, rank)

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
        self.files: dict[bytes, None] = {}  # every config file named, read or not, in order

    def load(self, path: bytes) -> None:
        """The entries of ``path`` and of the files it includes, each file read once.

        git follows every include up to ``MAX_INCLUDE_DEPTH`` (a file that includes itself makes it fail
        there); reading a file again finds nothing new, so here a file reached twice, by any name, is
        read once, which ends loops. Included files read count for ``MAX_INCLUDES`` per snapshot.
        """
        self._load(path, 0, set(), path)

    def _load(self, path: bytes, depth: int, seen: set[Identity], top: bytes) -> None:
        self.files.setdefault(path)  # compared even when not read
        try:
            ident = _identity(os.stat(path))  # git reads a config through a link
        except (OSError, ValueError):
            ident = None
        if ident is not None and ident in seen:
            return
        if depth and not self.walker.include(top):
            return
        if ident is not None:
            seen.add(ident)
        data = self.walker.discover(path)
        if data is None:
            return
        for name, value in parse_git_config(data):
            self.entries.append((name, value))
            if not self.follow or depth >= MAX_INCLUDE_DEPTH or not name.endswith(".path"):
                continue
            if name == "include.path" or name.startswith("includeif."):
                included = _join(os.path.dirname(path), os.fsencode(value), self.walker.home)
                self._load(included, depth + 1, seen, top)

    def values(self, name: str) -> list[bytes]:
        return [os.fsencode(value) for key, value in self.entries if key == name and value]

    def programs(self) -> Iterable[bytes]:
        """Programs named by path in command keys (``core.fsmonitor``, filters, ``!`` aliases, ...)."""
        for name, value in self.entries:
            if _is_command(name, value):
                yield from (os.fsencode(path) for path in _command_paths(value))


def parse_git_config(data: bytes) -> list[tuple[str, str]]:
    """``(name, value)`` pairs of a git config file, as git reads them, closely enough for discovery.

    Names are ``section.key`` or ``section.subsection.key``, section and key lowercased; a key
    without ``=`` is ``"true"``. Quotes, escapes, comments and continuation lines are handled.
    Malformed lines are skipped.
    """
    return [(name, value) for _, name, value in parse_git_config_lines(data)]


def parse_git_config_lines(data: bytes) -> list[tuple[int, str, str]]:
    """``(line, name, value)``: the entries of ``parse_git_config`` and the line, from 1, their key is on."""
    text = data.decode("utf-8", "surrogateescape")
    entries: list[tuple[int, str, str]] = []
    section: str | None = None
    pos, end = 0, len(text)
    line, counted = 1, 0  # newlines are counted up to ``counted``, once
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
                line += text.count("\n", counted, start)
                counted = start
                entries.append((line, f"{section}.{key}", value))
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
    if section in _GIT_TOOL_SECTIONS:
        return name.endswith((".cmd", ".path"))
    if section in ("filter", "merge", "diff", "gpg", "credential", "pager", "remote"):
        return (
            name.endswith(_GIT_COMMAND_SUFFIXES) or section == "pager" or name.endswith((".receivepack", ".uploadpack"))
        )
    return False


def _command_paths(value: str) -> list[str]:
    """Paths a git command value runs: every shell word holding a slash, and the first argument of
    a shell or an interpreter (``!sh tools/x.sh``, ``bash x.sh``), as a shell would split it."""
    text = value[1:] if value.startswith("!") else value
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        words = list(lexer)
    except ValueError:  # unbalanced quotes: the plain words
        words = text.split()
    found = [word for word in words if "/" in word]
    for index, word in enumerate(words):
        if os.path.basename(word) not in _SHELLS:
            continue
        for argument in words[index + 1 :]:
            if argument[:1] in ("-", "+"):
                continue
            if argument[:1] not in tuple("();<>|&"):
                found.append(argument)
            break
    return list(dict.fromkeys(found))


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
    if rule in ("all", "code", "home"):
        return ("git", None) if name == b".git" else (rule, None)
    if rule == "hooks":  # git never runs a hook named *.sample
        return None if name.endswith(b".sample") else ("hooks", None)
    if rule == "git":  # a .git directory found inside a compared tree: its config and hooks only
        if name in (b"config", b"config.worktree", b"commondir"):
            return "all", None
        return ("hooks", None) if name == b"hooks" else None
    if rule == "site-packages":  # what the interpreter runs at startup; packages are only imported
        lowered = name.lower()
        startup = lowered.endswith(b".pth") or lowered in (b"sitecustomize.py", b"usercustomize.py")
        return ("all", None) if startup else None
    if rule == "memory":
        return "memory", None
    if rule == "claude-projects":
        return "claude-project-slug", None
    if rule == "claude-project-slug":
        return ("memory", None) if name == b"memory" else None
    text = os.fsdecode(name)
    if rule == "claude-home":
        if text == "projects":  # session data, but for the auto-memory below it
            return "claude-projects", INSTRUCTIONS
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
    if rule.startswith("agent-project:"):
        names = AGENT_PROJECT_DIRS.get(rule[len("agent-project:") :], ())
        instruction = any(text == n or (n.endswith("*") and text.startswith(n[:-1])) for n in names)
        return "all", (INSTRUCTIONS if instruction else None)
    return None


def _looks_like_code(name: bytes, st: os.stat_result, head: bytes) -> bool:
    if stat.S_ISLNK(st.st_mode):
        return True
    return bool(st.st_mode & 0o111) or head.startswith(b"#!") or name.lower().endswith(CODE_SUFFIXES)


def _init_config(data: bytes) -> bool:
    """Whether a git config holds nothing but what ``git init`` writes, line by line (so a line
    this parser would read differently from git is never taken for one)."""
    return all(
        not line.strip() or line.lstrip()[:1] in (b"#", b";") or _INIT_CONFIG_LINE.fullmatch(line)
        for line in data.split(b"\n")
    )


def _exclude_patterns(data: bytes) -> list[bytes]:
    """The patterns of a git exclude file; blank lines and comments hide nothing."""
    return [line.rstrip(b"\r") for line in data.split(b"\n") if line.strip() and not line.startswith(b"#")]


def _idea_run_configs(data: bytes) -> list[bytes]:
    """The run configurations of an IntelliJ ``workspace.xml``: its ``RunManager`` and startup task
    components. The rest of the file (layout, history) changes whenever the IDE is used."""
    parts: list[bytes] = []
    pos = 0
    while True:
        start = data.find(b"<component", pos)
        if start < 0:
            return parts
        tag_end = data.find(b">", start)
        if tag_end < 0:
            return parts
        tag = data[start : tag_end + 1]
        pos = tag_end + 1
        name_at = tag.find(b'name="')
        name = tag[name_at + 6 : tag.find(b'"', name_at + 6)] if name_at >= 0 else b""
        if name != b"RunManager" and b"startup" not in name.lower():
            continue
        if tag.endswith(b"/>"):
            parts.append(tag)
            continue
        close = data.find(b"</component>", pos)
        stop = len(data) if close < 0 else close + len(b"</component>")
        parts.append(data[start:stop])
        pos = stop


def _import_paths(data: bytes) -> list[bytes]:
    """``@path`` imports of an agent instruction file, outside fenced and inline code, as Claude Code
    reads them; also without trailing punctuation (``see @RULES.md.``)."""
    found: list[bytes] = []
    fence: bytes | None = None
    for line in data.split(b"\n"):
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith((b"```", b"~~~")):
            fence = stripped[:3]
            continue
        for match in _IMPORT.finditer(_INLINE_CODE.sub(b" ", line)):
            path = match.group(1).replace(b"\\ ", b" ")
            found.append(path)
            trimmed = path.rstrip(b".,;:!?)]}'\"")
            if trimmed and trimmed != path:
                found.append(trimmed)
    return list(dict.fromkeys(found))


# Hiding bits of an index entry: 1 assume-unchanged, 2 skip-worktree; the flags each value names.
_HIDING: tuple[tuple[str, ...], ...] = (
    (),
    ("assume-unchanged",),
    ("skip-worktree",),
    ("assume-unchanged", "skip-worktree"),
)
_entry_path = operator.itemgetter(2)


class IndexLimit(ValueError):
    """The hidden paths of a git index add up to more than ``INDEX_PATH_BYTES``."""


@dataclass(frozen=True)
class GitIndex:
    """What ``parse_index`` reads from one git index file."""

    hidden: list[tuple[int, str, bytes]]  # (position, "assume-unchanged" or "skip-worktree", path), the first ones
    replaced: list[tuple[str, ...]]  # split index: the hiding flags of each entry without a path, in order
    link: tuple[bytes, list[int]] | None  # split index: the shared index's hash, the positions replaced
    more: int = 0  # hiding flags of entries beyond MAX_HIDDEN, not in ``hidden``


def parse_index(data: bytes, hash_size: int = 20) -> GitIndex:
    """The entries of one git index file that hide worktree changes from ``git status`` and ``git diff``.

    Versions 2 to 4 (4 compresses each path against the previous one). An entry hides changes when
    its flags have assume-unchanged (``0x8000``) or its extended flags skip-worktree (``0x4000``).
    In a split index the entries without a path replace, in order, the shared index entries that
    the ``link`` extension's replace bitmap (EWAH) marks. ``hash_size`` is 32 in a SHA-256
    repository. Memory stays bounded: ``MAX_HIDDEN`` entries are kept, ``more`` counts the rest, and
    their paths may add up to ``INDEX_PATH_BYTES`` (``IndexLimit`` beyond). Raises ``ValueError`` (or
    ``IndexError``) on anything else.
    """
    index = _IndexFile(data, hash_size)
    pathless = bytearray()
    hidden: list[tuple[int, str, bytes]] = []
    more = 0
    for position, bits, name in index.scan([INDEX_PATH_BYTES], pathless):
        for flag in _HIDING[bits]:
            if len(hidden) < MAX_HIDDEN:
                hidden.append((position, flag, name))
            else:
                more += 1
    replaced = [_HIDING[bits] for bits in pathless]
    if index.link is None:
        if replaced:
            raise ValueError("entries without a path")
        return GitIndex(hidden, replaced, None, more)
    shared_hash, at, stop = index.link
    positions: list[int] = []
    if at < stop:
        _, at = _ewah(data, at, stop)  # the delete bitmap
        replace, _ = _ewah(data, at, stop)
        positions = list(itertools.islice(replace, len(replaced)))
    if len(positions) < len(replaced):
        raise ValueError("split index replaces more entries than its bitmap marks")
    return GitIndex(hidden, replaced, (shared_hash, positions), more)


class _IndexFile:
    """One git index file, read in place: its entries in order, then its extensions."""

    def __init__(self, data: bytes, hash_size: int) -> None:
        self.end = len(data) - hash_size
        if self.end < 12 or data[:4] != b"DIRC":
            raise ValueError("not a git index")
        self.version, self.count = struct.unpack_from(">II", data, 4)
        if self.version not in (2, 3, 4):
            raise ValueError(f"index version {self.version}")
        self.data, self.hash_size = data, hash_size
        self.link: tuple[bytes, int, int] | None = None  # split index: the shared index's hash, its bitmaps' span
        self.applied = 0  # replacements given to entries, read as a shared index

    def scan(
        self, budget: list[int], pathless: bytearray | None, overrides: Iterator[tuple[int, int, int]] | None = None
    ) -> Iterator[tuple[int, int, bytes]]:
        """``(position, hiding bits, path)`` of every entry that hides changes, in the index's order.

        Bit 1 is assume-unchanged, bit 2 skip-worktree. Each path yielded costs its length from
        ``budget`` (``IndexLimit`` beyond it): version 4 rebuilds each path from the one before it, in
        place, and only a path yielded is copied. The bits of an entry without a path are appended to
        ``pathless`` (a split index's replacements); without ``pathless`` such an entry is an error (a
        shared index has none). ``overrides``, ascending ``(position, kind, bits)``, apply a split index
        to its shared index: kind 0 deletes the entry at ``position``, kind 1 gives it ``bits``. The
        extensions are read once the entries are (``link``).
        """
        data, end, version = self.data, self.end, self.version
        fixed = 40 + self.hash_size  # ctime, mtime, dev, ino, mode, uid, gid, size, object id
        pos = 12
        previous = bytearray()  # version 4: the path so far, edited in place (linear in the index size)
        pending = overrides if overrides is not None else iter(())
        upcoming = next(pending, None)
        for position in range(self.count):
            at = pos + fixed
            if at + 2 > end:
                raise ValueError("truncated index")
            flags = data[at] << 8 | data[at + 1]
            start = at + 2
            bits = flags >> 15  # assume-unchanged
            if flags & 0x4000:
                if version < 3:
                    raise ValueError("extended flags in a version 2 index")
                if start + 2 > end:
                    raise ValueError("truncated index")
                bits |= data[start] >> 5 & 2  # skip-worktree: 0x4000 of the extended flags
                start += 2
            if version == 4:
                strip, start = _varint(data, start)
                stop = data.find(b"\x00", start, end)
                if stop < 0 or strip > len(previous):
                    raise ValueError("bad path in index")
                del previous[len(previous) - strip :]
                previous += data[start:stop]
                if len(previous) > MAX_PATH_BYTES:
                    raise ValueError("path too long in index")
                pos = stop + 1
                size = len(previous)
            else:
                length = flags & 0x0FFF
                stop = (
                    start + length if length < 0x0FFF else data.find(b"\x00", start, min(end, start + MAX_PATH_BYTES))
                )
                if stop < 0 or stop >= end or data[stop] != 0:
                    raise ValueError("bad path in index")
                pos += (stop - pos + 8) & ~7  # NUL-padded to a multiple of eight bytes
                size = stop - start
            if not size:  # no path: a split index's replacement
                if pathless is None:
                    raise ValueError("not a shared index")
                pathless.append(bits)
                continue
            if upcoming is not None and upcoming[0] <= position:
                kept = True
                while upcoming is not None and upcoming[0] <= position:
                    if upcoming[0] == position:
                        if upcoming[1]:
                            bits = upcoming[2]
                            self.applied += 1
                        else:
                            kept = False
                    upcoming = next(pending, None)
                if not kept:
                    continue
            if bits:
                budget[0] -= size
                if budget[0] < 0:
                    raise IndexLimit(f"more than {INDEX_PATH_BYTES} bytes of hidden paths")
                yield position, bits, (bytes(previous) if version == 4 else data[start:stop])
        self._extensions(pos)

    def _extensions(self, pos: int) -> None:
        data, end = self.data, self.end
        while pos + 8 <= end:
            signature = data[pos : pos + 4]
            size = int.from_bytes(data[pos + 4 : pos + 8], "big")
            body = pos + 8
            if body + size > len(data):
                raise ValueError("truncated index extension")
            if signature == b"link":
                if size < self.hash_size:
                    raise ValueError("truncated link extension")
                self.link = (data[body : body + self.hash_size], body + self.hash_size, body + size)
            pos = body + size


class _Hidden:
    """The ``(flag, path)`` pairs an index hides, taken in its order with bounded memory: the first
    ``MAX_HIDDEN`` (``HIDDEN_NAMED_BYTES`` of paths) by name, all of them in a count and a digest. A
    path's entries (merge stages, or both halves of a split index once merged) come together in git's
    order, so each pair counts once."""

    def __init__(self) -> None:
        self.count = 0
        self.hasher = blake3(_DOMAIN + b"hidden\x00")
        self.named: list[tuple[str, bytes]] | None = []  # None once there are too many to name one by one
        self.named_bytes = 0
        self.path = b""
        self.bits = 0

    def add(self, bits: int, path: bytes) -> None:
        if path != self.path:
            self.flush()
            self.path = path
        self.bits |= bits

    def flush(self) -> None:
        for flag in _HIDING[self.bits]:
            self.count += 1
            self.hasher.update(flag.encode() + b"\x00" + self.path + b"\x00")
            if self.named is not None:
                if len(self.named) < MAX_HIDDEN and self.named_bytes + len(self.path) <= HIDDEN_NAMED_BYTES:
                    self.named.append((flag, self.path))
                    self.named_bytes += len(self.path)
                else:
                    self.named = None
        self.bits = 0


def _varint(data: bytes, pos: int) -> tuple[int, int]:
    """git's varint (each continuation byte adds one before the shift), and the offset after it."""
    byte = data[pos]
    value = byte & 0x7F
    pos += 1
    for _ in range(9):
        if not byte & 0x80:
            return value, pos
        byte = data[pos]
        pos += 1
        value = ((value + 1) << 7) | (byte & 0x7F)
    if byte & 0x80:
        raise ValueError("varint too long")
    return value, pos


def _ewah(data: bytes, pos: int, stop: int) -> tuple[Iterator[int], int]:
    """git's EWAH bitmap at ``pos``, ending by ``stop``: its set bits, ascending and read lazily, and the
    offset after it. Bit count and word count (32 bits each), the 64-bit words, the position of the
    last run-length word. Each run-length word holds a run bit, a run length in 64-bit words (32 bits)
    and how many literal words follow it (31 bits)."""
    if pos + 8 > stop:
        raise ValueError("truncated bitmap")
    _, words = struct.unpack_from(">II", data, pos)
    after = pos + 8 + 8 * words + 4
    if after > stop:
        raise ValueError("truncated bitmap")
    return _ewah_bits(data, pos + 8, words), after


def _ewah_bits(data: bytes, start: int, words: int) -> Iterator[int]:
    bit = index = 0
    while index < words:
        word = int.from_bytes(data[start + 8 * index : start + 8 * index + 8], "big")
        index += 1
        run = (word >> 1) & 0xFFFFFFFF
        if word & 1:
            yield from range(bit, bit + run * 64)
        bit += run * 64
        for _ in range(min(word >> 33, words - index)):
            literal = int.from_bytes(data[start + 8 * index : start + 8 * index + 8], "big")
            index += 1
            while literal:
                low = literal & -literal
                yield bit + low.bit_length() - 1
                literal ^= low
            bit += 64


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


def denied_identities(protected: Iterable[str]) -> set[Identity]:
    """Identities of ``/proc``, ``/sys`` and the ``protected`` paths that exist: never read below them."""
    found: set[Identity] = set()
    for path in ("/proc", "/sys", *protected):
        try:
            st = os.stat(path)
        except OSError:
            continue
        found.add((st.st_dev, st.st_ino))
    return found


def read_regular(
    path: bytes, denied: Collection[Identity], *, limit: int = CONFIG_BYTES, expect: Identity | None = None
) -> bytes | None:
    """Up to ``limit`` bytes of the regular file ``path``; None when it is not one (or not ``expect``).

    The parent path resolves as in any lookup; the file itself is never a link, and nothing
    below a directory whose identity is in ``denied`` is read.
    """
    parent, name = os.path.split(path)
    if not name or b"\x00" in path:
        return None
    try:
        dir_fd = os.open(parent or b"/", os.O_RDONLY | os.O_DIRECTORY | _CLOEXEC)
    except OSError:
        return None
    try:
        if any(identity in denied for identity in _fd_chain(dir_fd, parent or b"/")):
            return None
        st = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        if not stat.S_ISREG(st.st_mode) or expect not in (None, _identity(st)):
            return None
        fd = os.open(name, _FILE_FLAGS, dir_fd=dir_fd)
        try:
            if _identity(os.fstat(fd)) != _identity(st):
                return None
            return _read(fd, limit)
        finally:
            os.close(fd)
    except OSError:
        return None
    finally:
        os.close(dir_fd)


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
