"""Git config, git index (v2-v4, split/EWAH) and low-level regular-file parsers for confine.persistence."""
# ruff: noqa: F401

from __future__ import annotations

from collections.abc import Collection, Iterable, Iterator
from dataclasses import dataclass
import errno
import itertools
import json
import operator
import os
import shlex
import stat
import struct
from typing import TYPE_CHECKING

from blake3 import blake3

from babylon60.confine._persistence_catalog import (  # noqa: F401
    AGENT_PROJECT_DIRS,
    CHUNK_BYTES,
    CLAUDE_HOME_CODE,
    CLAUDE_HOME_DATA,
    CLAUDE_INSTRUCTIONS,
    CLAUDE_JSON_BYTES,
    CLAUDE_JSON_KEYS,
    CLAUDE_JSON_PATTERNS,
    CLAUDE_PROJECT_DATA,
    CODE,
    CODEX_HOME_CODE,
    CODEX_HOME_DATA,
    CODEX_INSTRUCTIONS,
    CODE_SUFFIXES,
    CONFIG_BYTES,
    DISCOVERY_BYTES,
    FULL_HASH_BYTES,
    HIDDEN_NAMED_BYTES,
    HOME_AGENT_FILES,
    HOME_STARTUP,
    HOOK_MANAGERS,
    INDEX_BYTES,
    INDEX_PATH_BYTES,
    INSTRUCTIONS,
    MAX_DEPTH,
    MAX_ENTRIES,
    MAX_GITDIRS,
    MAX_HIDDEN,
    MAX_IMPORTS,
    MAX_IMPORT_DEPTH,
    MAX_IMPORT_FILES,
    MAX_INCLUDES,
    MAX_INCLUDE_DEPTH,
    MAX_PATH_BYTES,
    MAX_READ_BYTES,
    MAX_ROOT_ENTRIES,
    MAX_SEARCH_UP,
    MAX_TREE_ENTRIES,
    PROJECT_FILES,
    PROJECT_IMPORTERS,
    PROJECT_INSTRUCTIONS,
    RANK_GIT,
    RANK_HOOK,
    RANK_INSTRUCTIONS,
    RANK_OTHER,
    RANK_SETTINGS,
    Report,
    Snapshot,
    _CLOEXEC,
    _DIR_FLAGS,
    _DOMAIN,
    _FILE_FLAGS,
    _GIT_BOOLEANS,
    _GIT_COMMANDS,
    _GIT_COMMAND_SUFFIXES,
    _GIT_TOOL_SECTIONS,
    _IMPORT,
    _IMPORTERS,
    _INIT_CONFIG_LINE,
    _INLINE_CODE,
    _NOTHING,
    _PROJECT,
    _PROJECT_BY_NAME,
    _Root,
    _SHELLS,
    _Stop,
    _TREE_NAMES,
    _TREE_PRUNED,
    changes,
    printable,
)
from babylon60.confine.policy import Identity, ancestry

if TYPE_CHECKING:
    from babylon60.confine.persistence import _Walker


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
    pos, end = (1 if text.startswith("\ufeff") else 0), len(text)  # git skips one UTF-8 byte order mark
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
    while pos < len(data):
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
    return parts


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

    def _apply_overrides(
        self,
        position: int,
        bits: int,
        upcoming: tuple[int, int, int] | None,
        pending: Iterator[tuple[int, int, int]],
    ) -> tuple[int, bool, tuple[int, int, int] | None]:
        kept = True
        while upcoming is not None and upcoming[0] <= position:
            if upcoming[0] == position:
                if upcoming[1]:
                    bits = upcoming[2]
                    self.applied += 1
                else:
                    kept = False
            upcoming = next(pending, None)
        return bits, kept, upcoming

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
                bits, kept, upcoming = self._apply_overrides(position, bits, upcoming, pending)
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
