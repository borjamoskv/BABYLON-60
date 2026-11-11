"""The git configuration a preset grants read-only, and what keeps a file out of it.

git exits with "unknown error occurred while reading the configuration files"
when a configuration file it finds is unreadable (Landlock lets ``access(2)``
through and then denies the open), so with a ``~/.gitconfig`` present every
git command inside ``babylon60 run`` used to fail (``UNREADABLE``: what git does
for each kind of file). Every preset now grants, read-only and file by file,
the global files git reads and the files they include:

* ``~/.gitconfig`` and, under ``$XDG_CONFIG_HOME/git`` (default
  ``~/.config/git``), ``config``, ``ignore`` and ``attributes``, with ``~``
  taken from the ``HOME`` the agent receives, as git takes it;
* every ``include.path`` and ``includeIf.*.path`` of a config file, whatever its
  condition, followed breadth first up to git's own depth (``MAX_INCLUDE_DEPTH``)
  and to ``MAX_FILES`` files: ``~/`` from that ``HOME`` and relative paths from
  the including file's directory (``persistence._join``, as git joins them).

Each file goes through ``build_policy``'s guards first, as any other grant:
the home and its ancestors, the protected set and its aliases by inode
identity (hardlinks too) are refused, and a final symbolic link or anything
but a regular file is skipped with its reason. Only then is it read, through
``persistence.read_regular`` (up to ``CONFIG_BYTES``, never below ``/proc``,
``/sys`` or a protected path), and parsed with ``persistence``'s git config
parser. A file whose content looks like a credential (``credential_findings``)
is not granted: a warning names the file, the line and the key, never the
value. ``--allow-read`` grants it anyway.

A file another grant already makes readable gets no grant of its own and no
check; a file the agent can write (inside a read-write grant) gets its
includes ignored, so a session cannot name what the next one is granted.

Not covered: other files the configuration names (``core.excludesFile``,
``core.attributesFile``, ``commit.template``...), ``GIT_CONFIG_GLOBAL`` and the
system configuration's includes. The credential check is a heuristic: a
credential in another form is granted with its file.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable, Mapping
import os
import re
import stat
from typing import Protocol

from babylon60.confine.persistence import (
    CONFIG_BYTES,
    MAX_INCLUDE_DEPTH,
    _join,
    denied_identities,
    parse_git_config_lines,
    printable,
    read_regular,
)
from babylon60.confine.policy import Grant, Identity, ancestry

GLOBAL_NAMES = ("config", "ignore", "attributes")  # under $XDG_CONFIG_HOME/git, or ~/.config/git
# What git 2.43 does when it cannot read one of them (measured confined, uid 65534).
UNREADABLE = {
    "config": "git inside will fail to read its configuration",
    "ignore": "git status inside will fail (it cannot use it as an exclude file)",
    "attributes": "git inside will warn on every command and ignore those attributes",
}
MAX_FILES = 64  # files examined, includes included
SHOWN_FINDINGS = 8
CREDENTIAL_WORDS = ("pass", "token", "secret", "oauth")  # in a section or key name
# A URL and its user information, up to the "@" that ends it. The scheme starts after a character
# that cannot be part of one and the user information never backtracks: linear on any line.
_URL = re.compile(r"(?<![A-Za-z0-9+.-])([A-Za-z][A-Za-z0-9+.-]*)://([^/?#@\s\"']*+)@")

Accept = Callable[[str, os.stat_result, list[Identity]], bool]


class AddGrant(Protocol):
    """``build_policy``'s ``add``: the guards, then ``accept``; True when the path was granted."""

    def __call__(self, path: str, access: str, origin: str, *, strict: bool, accept: Accept | None = None) -> bool: ...


def global_paths(environ: Mapping[str, str]) -> list[tuple[str, str]]:
    """``(path, kind)`` of the global files git reads with ``environ`` (``HOME``, ``XDG_CONFIG_HOME``).

    ``kind`` is ``config``, ``ignore`` or ``attributes``; only config files name includes.
    """
    home = environ.get("HOME") or ""
    xdg = environ.get("XDG_CONFIG_HOME") or ""
    paths: list[tuple[str, str]] = []
    if os.path.isabs(home):
        paths.append((os.path.join(home, ".gitconfig"), "config"))
    base = os.path.join(xdg, "git") if xdg else (os.path.join(home, ".config", "git") if home else "")
    if os.path.isabs(base):
        paths.extend((os.path.join(base, name), name) for name in GLOBAL_NAMES)
    return paths


def credential_findings(data: bytes) -> list[tuple[int, str]]:
    """``(line, key)`` for what looks like a credential in a git config file; values are never returned.

    An entry is suspect when its section or key name contains ``pass``, ``token``,
    ``secret`` or ``oauth``; for ``http.*.extraheader``, ``url.*.insteadOf`` and
    ``url.*.pushInsteadOf``; for a ``credential.*.helper`` holding a literal
    ``password=`` or ``token=``; and when its name or value holds a URL with a
    password, or an http(s) URL with a user name (a token in place of the user).
    Any line holding such a URL is suspect too: comments and section headers
    included. Keys are shown as ``section.key``, ``section.*.key`` with a subsection.
    """
    found: dict[int, str] = {}
    for line, name, value in parse_git_config_lines(data):
        if _suspect(name, value):
            found.setdefault(line, _shown(name))
    for number, text in enumerate(data.decode("utf-8", "surrogateescape").split("\n"), start=1):
        if number not in found and _url_credential(text):
            found[number] = "a URL with credentials"
    return sorted(found.items())


def grant_global_config(
    add: AddGrant,
    environ: Mapping[str, str],
    grants: Iterable[Grant],
    *,
    protected: Iterable[str],
    origin: str,
    skipped: list[str],
    warnings: list[str],
) -> None:
    """Grant the global git configuration of ``environ`` read-only through ``add`` (see the module)."""
    current = list(grants)
    readable = {(g.dev, g.ino) for g in current if g.access in ("ro", "rw")}
    writable = {(g.dev, g.ino) for g in current if g.access == "rw"}
    denied = denied_identities(protected)
    home = os.fsencode(environ.get("HOME") or "")
    queue = deque((os.fsencode(path), kind, 0) for path, kind in global_paths(environ))
    seen: set[bytes] = set()  # paths as git spells them: a relative include resolves from their directory
    done: dict[str, bytes | None] = {}  # the same file under another spelling is granted and checked once
    while queue:
        path, kind, depth = queue.popleft()
        if path in seen:
            continue
        if len(seen) >= MAX_FILES:
            warnings.append(
                f"git configuration: more than {MAX_FILES} files named through includes; the rest is not granted"
            )
            return
        seen.add(path)
        text = os.fsdecode(path)
        if "\x00" in text or not os.path.isabs(text):
            continue
        # The directories resolve as the kernel resolves them for git; the file itself is never followed.
        resolved = os.path.join(os.path.realpath(os.path.dirname(text)), os.path.basename(text))
        if resolved not in done:
            done[resolved] = _grant_one(add, resolved, kind, readable, writable, denied, origin, skipped, warnings)
        data = done[resolved]
        if data is None or kind != "config" or depth >= MAX_INCLUDE_DEPTH:
            continue
        for _, name, value in parse_git_config_lines(data):
            if not value or not name.endswith(".path") or (value.startswith("~") and not home):
                continue
            if name == "include.path" or name.startswith("includeif."):
                queue.append((_join(os.path.dirname(path), os.fsencode(value), home), "config", depth + 1))


def _grant_one(
    add: AddGrant,
    path: str,
    kind: str,
    readable: set[Identity],
    writable: set[Identity],
    denied: set[Identity],
    origin: str,
    skipped: list[str],
    warnings: list[str],
) -> bytes | None:
    """Grant one file; its content, to follow its includes, unless the agent can write it."""
    shown = printable(path)
    try:
        st = os.lstat(path)
        chain = ancestry(path) if stat.S_ISREG(st.st_mode) else []
    except (FileNotFoundError, NotADirectoryError):
        skipped.append(shown)  # absent, as any other preset path
        return None
    except OSError as exc:
        skipped.append(f"{shown}: {exc.strerror}")
        return None
    if stat.S_ISLNK(st.st_mode):
        skipped.append(f"{shown}: a symbolic link, not followed; git inside cannot read it (--allow-read its target)")
        return None
    if not chain:
        skipped.append(f"{shown}: not a regular file")
        return None
    if readable.intersection(chain):  # already readable through another grant: no grant, no check
        data = read_regular(os.fsencode(path), denied, expect=chain[0])
        return None if writable.intersection(chain) else data
    content: list[bytes] = []

    def accept(granted: str, _st: os.stat_result, checked: list[Identity]) -> bool:
        data = read_regular(os.fsencode(granted), denied, limit=CONFIG_BYTES + 1, expect=checked[0])
        if data is None or len(data) > CONFIG_BYTES:
            skipped.append(f"{shown}: not read whole (unreadable or over {CONFIG_BYTES} bytes), so not checked")
            return False
        content.append(data)
        findings = credential_findings(data)
        if findings:
            skipped.append(shown)  # the warning says why
            warnings.append(_credential_warning(shown, findings, kind))
            return False
        return True

    add(path, "ro", origin, strict=False, accept=accept)
    return content[0] if content else None


def _credential_warning(path: str, findings: list[tuple[int, str]], kind: str) -> str:
    lines = ", ".join(f"line {line} ({key})" for line, key in findings[:SHOWN_FINDINGS])
    more = f" and {len(findings) - SHOWN_FINDINGS} more" if len(findings) > SHOWN_FINDINGS else ""
    return (
        f"git configuration not granted, it looks like it carries a credential (values never shown): "
        f"{path} {lines}{more}; {UNREADABLE[kind]}; --allow-read {path} grants it anyway"
    )


def _suspect(name: str, value: str) -> bool:
    section, key = name.split(".", 1)[0], name.rsplit(".", 1)[-1]
    if any(word in section or word in key for word in CREDENTIAL_WORDS):
        return True
    if (section, key) in (("http", "extraheader"), ("url", "insteadof"), ("url", "pushinsteadof")):
        return True
    if section == "credential" and key == "helper" and ("password=" in value.lower() or "token=" in value.lower()):
        return True
    return _url_credential(name) or _url_credential(value)


def _url_credential(text: str) -> bool:
    """Whether ``text`` holds a URL with a password, or an http(s) URL with a user name."""
    for match in _URL.finditer(text):
        user, colon, password = match.group(2).partition(":")
        if (colon and password) or (user and match.group(1).lower() in ("http", "https")):
            return True
    return False


def _shown(name: str) -> str:
    """``section.key``, with ``*`` in place of a subsection (it may hold a URL with credentials)."""
    section, key = name.split(".", 1)[0], name.rsplit(".", 1)[-1]
    return f"{section}.*.{key}" if name.count(".") > 1 else f"{section}.{key}"
