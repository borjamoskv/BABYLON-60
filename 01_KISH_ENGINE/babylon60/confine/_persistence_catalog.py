"""Static path catalogs, categories and snapshot data structures for confine.persistence."""
# ruff: noqa: F401

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import os
import re

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
