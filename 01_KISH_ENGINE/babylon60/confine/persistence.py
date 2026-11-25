"""Files an agent can leave behind that run, or steer an agent, outside the sandbox later."""
# ruff: noqa: F401

from __future__ import annotations

from collections import deque
from collections.abc import Collection, Iterable, Iterator, Mapping
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
from babylon60.confine._persistence_catalog import (  # noqa: F401
    AGENT_PROJECT_DIRS as AGENT_PROJECT_DIRS,
    CHUNK_BYTES as CHUNK_BYTES,
    CLAUDE_HOME_CODE as CLAUDE_HOME_CODE,
    CLAUDE_HOME_DATA as CLAUDE_HOME_DATA,
    CLAUDE_INSTRUCTIONS as CLAUDE_INSTRUCTIONS,
    CLAUDE_JSON_BYTES as CLAUDE_JSON_BYTES,
    CLAUDE_JSON_KEYS as CLAUDE_JSON_KEYS,
    CLAUDE_JSON_PATTERNS as CLAUDE_JSON_PATTERNS,
    CLAUDE_PROJECT_DATA as CLAUDE_PROJECT_DATA,
    CODE as CODE,
    CODEX_HOME_CODE as CODEX_HOME_CODE,
    CODEX_HOME_DATA as CODEX_HOME_DATA,
    CODEX_INSTRUCTIONS as CODEX_INSTRUCTIONS,
    CODE_SUFFIXES as CODE_SUFFIXES,
    CONFIG_BYTES as CONFIG_BYTES,
    DISCOVERY_BYTES as DISCOVERY_BYTES,
    FULL_HASH_BYTES as FULL_HASH_BYTES,
    HIDDEN_NAMED_BYTES as HIDDEN_NAMED_BYTES,
    HOME_AGENT_FILES as HOME_AGENT_FILES,
    HOME_STARTUP as HOME_STARTUP,
    HOOK_MANAGERS as HOOK_MANAGERS,
    INDEX_BYTES as INDEX_BYTES,
    INDEX_PATH_BYTES as INDEX_PATH_BYTES,
    INSTRUCTIONS as INSTRUCTIONS,
    MAX_DEPTH as MAX_DEPTH,
    MAX_ENTRIES as MAX_ENTRIES,
    MAX_GITDIRS as MAX_GITDIRS,
    MAX_HIDDEN as MAX_HIDDEN,
    MAX_IMPORTS as MAX_IMPORTS,
    MAX_IMPORT_DEPTH as MAX_IMPORT_DEPTH,
    MAX_IMPORT_FILES as MAX_IMPORT_FILES,
    MAX_INCLUDES as MAX_INCLUDES,
    MAX_INCLUDE_DEPTH as MAX_INCLUDE_DEPTH,
    MAX_PATH_BYTES as MAX_PATH_BYTES,
    MAX_READ_BYTES as MAX_READ_BYTES,
    MAX_ROOT_ENTRIES as MAX_ROOT_ENTRIES,
    MAX_SEARCH_UP as MAX_SEARCH_UP,
    MAX_TREE_ENTRIES as MAX_TREE_ENTRIES,
    PROJECT_FILES as PROJECT_FILES,
    PROJECT_IMPORTERS as PROJECT_IMPORTERS,
    PROJECT_INSTRUCTIONS as PROJECT_INSTRUCTIONS,
    RANK_GIT as RANK_GIT,
    RANK_HOOK as RANK_HOOK,
    RANK_INSTRUCTIONS as RANK_INSTRUCTIONS,
    RANK_OTHER as RANK_OTHER,
    RANK_SETTINGS as RANK_SETTINGS,
    Report as Report,
    Snapshot as Snapshot,
    _CLOEXEC as _CLOEXEC,
    _DIR_FLAGS as _DIR_FLAGS,
    _DOMAIN as _DOMAIN,
    _FILE_FLAGS as _FILE_FLAGS,
    _GIT_BOOLEANS as _GIT_BOOLEANS,
    _GIT_COMMANDS as _GIT_COMMANDS,
    _GIT_COMMAND_SUFFIXES as _GIT_COMMAND_SUFFIXES,
    _GIT_TOOL_SECTIONS as _GIT_TOOL_SECTIONS,
    _IMPORT as _IMPORT,
    _IMPORTERS as _IMPORTERS,
    _INIT_CONFIG_LINE as _INIT_CONFIG_LINE,
    _INLINE_CODE as _INLINE_CODE,
    _NOTHING as _NOTHING,
    _PROJECT as _PROJECT,
    _PROJECT_BY_NAME as _PROJECT_BY_NAME,
    _Root as _Root,
    _SHELLS as _SHELLS,
    _Stop as _Stop,
    _TREE_NAMES as _TREE_NAMES,
    _TREE_PRUNED as _TREE_PRUNED,
    changes as changes,
    printable as printable,
)
from babylon60.confine._persistence_parsers import (  # noqa: F401
    GitIndex as GitIndex,
    IndexLimit as IndexLimit,
    _GitConfig as _GitConfig,
    _HIDING as _HIDING,
    _Hidden as _Hidden,
    _IndexFile as _IndexFile,
    _chain as _chain,
    _child_rule as _child_rule,
    _claude_json_entries as _claude_json_entries,
    _command_paths as _command_paths,
    _entry_path as _entry_path,
    _errname as _errname,
    _ewah as _ewah,
    _ewah_bits as _ewah_bits,
    _exclude_patterns as _exclude_patterns,
    _fd_chain as _fd_chain,
    _global_git_configs as _global_git_configs,
    _idea_run_configs as _idea_run_configs,
    _identity as _identity,
    _import_paths as _import_paths,
    _init_config as _init_config,
    _is_command as _is_command,
    _join as _join,
    _json_digest as _json_digest,
    _line_end as _line_end,
    _looks_like_code as _looks_like_code,
    _physical_chain as _physical_chain,
    _read as _read,
    _relevant as _relevant,
    _section as _section,
    _value as _value,
    _varint as _varint,
    denied_identities as denied_identities,
    parse_git_config as parse_git_config,
    parse_git_config_lines as parse_git_config_lines,
    parse_index as parse_index,
    read_regular as read_regular,
)


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

    def _scan_tree_dir(
        self, path: bytes, depth: int, left: int, pending: deque[tuple[bytes, int]]
    ) -> tuple[list[tuple[bytes, bool]], int, bool, bool]:
        pruned = _TREE_PRUNED.get(os.path.basename(path), _NOTHING)
        found: list[tuple[bytes, bool]] = []
        full = False
        deep = False
        try:
            with os.scandir(path) as items:
                for item in items:
                    left -= 1
                    if left < 0:
                        return found, left, True, deep
                    name = item.name
                    directory = item.is_dir(follow_symlinks=False)
                    if name in _TREE_NAMES or name.endswith(b".code-workspace"):
                        found.append((name, directory))
                    if not (directory and name != b".git" and name not in pruned and item.path not in self.gitdirs):
                        continue
                    if depth < MAX_DEPTH:
                        pending.append((item.path, depth + 1))
                    else:
                        deep = True
        except OSError as exc:
            # A directory that cannot be listed (mode 0311) still lets a tool open a name in it:
            # those names are compared, and what lies deeper is named as not compared.
            self.unchecked.append(f"{self.label(path)} ({_errname(exc)}: nested configs below not compared)")
            found = [(b".git", True), *((name, False) for name in (*_PROJECT_BY_NAME, *_IMPORTERS))]
        return found, left, full, deep

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
            found, left, full, hit_deep = self._scan_tree_dir(path, depth, left, pending)
            deep = deep or hit_deep
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
