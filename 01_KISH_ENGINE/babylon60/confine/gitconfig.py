"""The git configuration a preset grants read-only, and what keeps a path out of it.

git exits with "unknown error occurred while reading the configuration files"
when a configuration file it finds is unreadable (Landlock lets ``access(2)``
through and then denies the open), so with a ``~/.gitconfig`` present every
git command inside ``babylon60 run`` used to fail (``UNREADABLE``: what git does
for each kind of path). Every preset now grants, read-only and one by one:

* ``~/.gitconfig`` and, under ``$XDG_CONFIG_HOME/git`` (default
  ``~/.config/git``), ``config``, ``ignore`` and ``attributes``;
* every ``include.path`` and ``includeIf.<condition>.path`` of a config file,
  whatever the condition (git never includes an ``includeIf`` without one),
  followed breadth first up to git's own depth (``MAX_INCLUDE_DEPTH``);
* the files a config file names with ``core.excludesFile``,
  ``core.attributesFile`` and ``commit.template``, and the directory it names
  with ``core.hooksPath``, whose hooks git runs inside the sandbox;

up to ``MAX_FILES`` paths in all. Paths are expanded as git's
``interpolate_path`` expands them: ``~`` and ``~/`` from the ``HOME`` the agent
receives, ``~user/`` from the account database; a relative include from the
including file's directory (``persistence._join``), and a relative named path
not at all (git resolves it from the repository it runs in).

Symbolic links on the way, the path's own name included, are followed as the
kernel follows them, but only while the directory holding each link is outside
every write grant: otherwise the agent could choose what the next session is
granted. The links followed stay readable (``Policy.links``: Seatbelt checks
following a link as a read of the link), and for a link below the ``HOME`` a
warning names the target. Each path then goes through ``build_policy``'s
guards, as any other grant: the home and its ancestors, the protected set and
its aliases by inode identity (hardlinks too) are refused, and so is a path
through a directory named like a protected path (``.ssh``, ``.config/gh``...) of
a home the policy does not protect. Only then is a file read, through
``persistence.read_regular`` (up to ``CONFIG_BYTES``, never below ``/proc``,
``/sys`` or a protected path), and checked (``credential_findings``): config
files with ``persistence``'s git config parser, ignore, attributes and template
files only for URLs with credentials. A file that looks like it carries a
credential is not granted, and neither is a hooks directory that holds one: a
warning names the file, the line and the key, never the value, and
``--allow-read`` grants it anyway. On macOS a path Seatbelt cannot name in a
rule (a control character, or longer than its string literals) is skipped.

A file another grant already makes readable gets no grant of its own and no
check; a file the agent can write (inside a read-write grant) gets its includes
and named paths ignored, so a session cannot name what the next one is granted.

Not covered: other paths the configuration names (``init.templateDir``,
``blame.ignoreRevsFile``, ``gpg.ssh.allowedSignersFile``, programs under a
home...), ``GIT_CONFIG_GLOBAL`` and the system configuration's includes. The
credential check is a heuristic: a credential in another form is granted with
its file.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
import os
import pwd
import re
import stat
import sys
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
from babylon60.confine.policy import PROTECTED_RELATIVE, Grant, Identity, ancestry

GLOBAL_NAMES = ("config", "ignore", "attributes")  # under $XDG_CONFIG_HOME/git, or ~/.config/git
# Settings of a config file that name one more path git reads, and the kind of that path.
NAMED = {
    "core.excludesfile": "ignore",
    "core.attributesfile": "attributes",
    "commit.template": "template",
    "core.hookspath": "hooks",
}
# git dies reading a config file with one of these it cannot expand (an includeIf path is expanded only
# when its condition holds, commit.template only by git commit).
DIES_UNEXPANDED = frozenset({"include.path", "core.excludesfile", "core.attributesfile", "core.hookspath"})
# What git 2.43 does when it cannot read a path of each kind (measured confined, uid 65534).
UNREADABLE = {
    "config": "git inside will fail to read its configuration",
    "ignore": "git add, commit and status inside will fail (it cannot use it as an exclude file)",
    "attributes": "git inside will warn on every command and ignore those attributes",
    "template": "git commit inside will fail unless it is given a message (it cannot read the template)",
    "hooks": "git inside cannot run the hooks there (git commit fails when a pre-commit hook must run)",
}
GRANTED, READABLE, ABSENT = "granted read-only", "readable through another grant", "absent"  # outcomes
MAX_FILES = 64  # paths examined: includes, named files and hooks directories included
MAX_LINKS = 40  # symbolic links followed for one path, as the kernel follows them
SHOWN_FINDINGS = 8
CREDENTIAL_WORDS = ("pass", "token", "secret", "oauth")  # in a section or key name
HELPER_WORDS = ("password", "token")  # a credential.helper that prints <word>=... holds the credential
# A URL and its user information, up to the "@" that ends it. The scheme starts after a character
# that cannot be part of one and the user information never backtracks: linear on any line.
_URL = re.compile(r"(?<![A-Za-z0-9+.-])([A-Za-z][A-Za-z0-9+.-]*)://([^/?#@\s\"']*+)@")
# Seatbelt renders the grants on macOS (seatbelt.py); a path it cannot name in a rule is skipped there.
SEATBELT = sys.platform == "darwin"

Accept = Callable[[str, os.stat_result, list[Identity]], bool]


class AddGrant(Protocol):
    """``build_policy``'s ``add``: the guards, then ``accept``; True when the path was granted."""

    def __call__(self, path: str, access: str, origin: str, *, strict: bool, accept: Accept | None = None) -> bool: ...


@dataclass
class _Session:
    """What one ``grant_global_config`` call knows and reports."""

    add: AddGrant
    home: bytes  # the HOME git receives, for ~ and ~/
    home_id: Identity | None  # links below it are named in the warnings (not /var -> /private/var)
    readable: set[Identity]  # granted before: a path below one of these gets no grant and no check
    writable: set[Identity]
    denied: set[Identity]  # never read below these
    origin: str
    skipped: list[str]
    warnings: list[str]
    links: list[str]  # symbolic links followed to a granted or readable path
    withheld: list[list[Identity]] = field(default_factory=list)  # ancestry of files kept out as credentials
    users: dict[bytes, bytes | None] = field(default_factory=dict)  # ~user -> home directory, or None
    unexpanded: int = 0  # paths git cannot expand, named in skipped
    # Resolved path -> (what it names, parsed once: (name, value) of its includes and named paths, or
    # None when they are not followed; GRANTED, READABLE, ABSENT, or None when it is kept out).
    done: dict[str, tuple[list[tuple[str, str]] | None, str | None]] = field(default_factory=dict)


def global_paths(environ: Mapping[str, str]) -> list[tuple[str, str]]:
    """``(path, kind)`` of the global files git reads with ``environ`` (``HOME``, ``XDG_CONFIG_HOME``).

    ``kind`` is ``config``, ``ignore`` or ``attributes``; only config files name other paths.
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


def credential_findings(data: bytes, kind: str = "config") -> list[tuple[int, str]]:
    """``(line, key)`` for what looks like a credential in a git file of ``kind``; values are never returned.

    Every kind: a line holding a URL with a password, or an http(s) URL with a user
    name (a token in place of the user), comments and section headers included.
    Config files are also parsed as git parses them (a leading UTF-8 byte order mark
    skipped): an entry is suspect when its section or key name contains ``pass``,
    ``token``, ``secret`` or ``oauth``, for ``http.*.extraheader``, for a
    ``credential.*.helper`` holding a literal ``password=`` or ``token=``, and when
    its name or value holds such a URL. Keys are shown as ``section.key``, or
    ``section.*.key`` with a subsection. Ignore, attributes and template files are
    not git config (``[Bb]in/`` is a pattern, not a section): only URLs count there.
    """
    found: dict[int, str] = {}
    if kind == "config":
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
    links: list[str] | None = None,
) -> None:
    """Grant the global git configuration of ``environ`` read-only through ``add`` (see the module).

    Config files come first, breadth first through their includes, then the files they
    name and last the hooks directories: a file reached both ways gets the config
    check, and a hooks directory is kept out when it holds a file kept out. The
    symbolic links followed to a granted or readable path are appended to ``links``;
    a warning names those below the ``HOME`` git receives and the target granted.
    """
    current = list(grants)
    home = environ.get("HOME") or ""
    try:
        home_st = os.stat(home) if os.path.isabs(home) else None
    except OSError:
        home_st = None
    session = _Session(
        add=add,
        home=os.fsencode(home),
        home_id=(home_st.st_dev, home_st.st_ino) if home_st else None,
        readable={(g.dev, g.ino) for g in current if g.access in ("ro", "rw")},
        writable={(g.dev, g.ino) for g in current if g.access == "rw"},
        denied=denied_identities(protected),
        origin=origin,
        skipped=skipped,
        warnings=warnings,
        links=links if links is not None else [],
    )
    queued: set[tuple[bytes, str]] = set()  # paths as git spells them: a relative include resolves from there
    overflow = False

    def enqueue(path: bytes, kind: str) -> bool:
        nonlocal overflow
        if (path, kind) in queued or overflow:
            return False
        if len(queued) >= MAX_FILES:
            overflow = True
            return False
        queued.add((path, kind))
        return True

    configs: deque[tuple[bytes, int]] = deque()
    named: list[tuple[bytes, str]] = []
    for text, kind in global_paths(environ):
        path = os.fsencode(text)
        if enqueue(path, kind):
            if kind == "config":
                configs.append((path, 0))
            else:
                named.append((path, kind))
    while configs:
        path, depth = configs.popleft()
        for name, value in _grant_file(session, os.fsdecode(path), "config") or ():
            include = _includes(name)
            expanded = _expand(session, value, os.path.dirname(path) if include else None)
            if isinstance(expanded, str):
                if session.unexpanded < MAX_FILES:  # named once each, up to the bound
                    session.unexpanded += 1
                    session.skipped.append(f"{printable(value)}: {expanded}")
                if name in DIES_UNEXPANDED:  # git dies reading this file: nothing after it counts
                    break
                continue
            if expanded is None:
                continue
            if include:
                if depth < MAX_INCLUDE_DEPTH and enqueue(expanded, "config"):  # git dies including an 11th
                    configs.append((expanded, depth + 1))
            elif enqueue(expanded, NAMED[name]):
                named.append((expanded, NAMED[name]))
    for path, kind in sorted(named, key=lambda item: item[1] == "hooks"):
        if kind == "hooks":
            _grant_hooks(session, os.fsdecode(path))
        else:
            _grant_file(session, os.fsdecode(path), kind)
    if overflow:
        warnings.append(
            f"git configuration: more than {MAX_FILES} paths named through includes; the rest is not granted"
        )


def _includes(name: str) -> bool:
    """``include.path``, or ``includeIf.<condition>.path``: git never includes an ``includeIf`` without one."""
    if name == "include.path":
        return True
    return name.startswith("includeif.") and name.endswith(".path") and len(name) > len("includeif..path")


def _expand(session: _Session, value: str, base: bytes | None) -> bytes | str | None:
    """``value`` as git's ``interpolate_path`` expands it, then relative to ``base``.

    None when nothing is to be granted (a relative path without ``base``, or a ``~user``
    beyond ``MAX_FILES`` distinct names); a reason when git cannot expand it either (an
    unknown ``~user``, ``~`` without a ``HOME``).
    """
    raw = os.fsencode(value).split(b"\x00", 1)[0]  # git reads values as C strings
    if raw.startswith(b"~"):
        user, slash, rest = raw[1:].partition(b"/")
        if not user:
            if not session.home:
                return "git cannot expand ~ without a HOME either"
            raw = session.home + slash + rest
        else:
            if user not in session.users:
                if len(session.users) >= MAX_FILES:
                    return None
                try:
                    session.users[user] = os.fsencode(pwd.getpwnam(os.fsdecode(user)).pw_dir)
                except (KeyError, ValueError, OSError):
                    session.users[user] = None
            directory = session.users[user]
            if directory is None:
                return f"no user {printable(user)} in the account database, so git cannot expand it either"
            raw = directory + slash + rest
    if raw.startswith(b"/"):
        return raw
    return None if base is None else _join(base, raw, session.home)


def _resolve(session: _Session, path: str) -> tuple[str, list[str], bool] | None:
    """``(path as the kernel resolves it, the symbolic links on its way, whether one is below the HOME)``,
    or None (the reason goes to ``skipped``) when a link sits inside a write grant or there are more
    than ``MAX_LINKS``.

    A missing component ends the walk: the rest is kept as written, and the path is skipped as absent.
    """
    links: list[str] = []
    in_home = False
    current = ""  # resolved so far, links resolved; "" is "/"
    pending = [part for part in reversed(path.split("/")) if part not in ("", ".")]
    while pending:
        part = pending.pop()
        if part == "..":
            current = current.rsplit("/", 1)[0]
            continue
        candidate = f"{current}/{part}"
        try:
            st = os.lstat(candidate)
        except OSError:
            rest = "/".join(reversed(pending))
            return (f"{candidate}/{rest}" if rest else candidate), links, in_home
        if not stat.S_ISLNK(st.st_mode):
            current = candidate
            continue
        target = ""
        reason = None
        if len(links) >= MAX_LINKS:
            reason = f"more than {MAX_LINKS} symbolic links on its way"
        else:
            try:
                chain = ancestry(current or "/")
                if not session.writable.isdisjoint(chain):
                    reason = f"the symbolic link {printable(candidate)} is inside a write grant, so it is not followed"
                in_home = in_home or session.home_id in chain
                target = os.readlink(candidate)
            except OSError as exc:
                reason = f"the symbolic link {printable(candidate)} cannot be followed ({exc.strerror})"
        if reason:
            session.skipped.append(
                f"{printable(path)}: {reason}; git inside reads it only if its target is granted (--allow-read its target)"
            )
            return None
        links.append(candidate)
        if target.startswith("/"):
            current = ""
        pending.extend(part for part in reversed(target.split("/")) if part not in ("", "."))
    return current or "/", links, in_home


def _grant_file(session: _Session, path: str, kind: str) -> list[tuple[str, str]] | None:
    """Grant one file of ``kind``; what it names (``_names``), unless the agent can write it."""
    resolved = _resolve(session, path)
    if resolved is None:
        return None
    target, links, in_home = resolved
    if target not in session.done:  # another spelling of a file already seen is not read or parsed again
        session.done[target] = _check_file(session, target, links, kind)
    names, outcome = session.done[target]
    if outcome in (GRANTED, READABLE):
        _followed(session, path, target, links, in_home, outcome)
    elif outcome is None and links:
        _not_followed(session, path, target)
    return names


def _names(data: bytes | None, kind: str) -> list[tuple[str, str]] | None:
    """``(name, value)`` of the includes and named paths of a config file, in order; None for other kinds."""
    if data is None or kind != "config":
        return None
    return [
        (name, value) for _, name, value in parse_git_config_lines(data) if value and (_includes(name) or name in NAMED)
    ]


def _check_file(
    session: _Session, target: str, links: list[str], kind: str
) -> tuple[list[tuple[str, str]] | None, str | None]:
    """``(what it names, outcome)`` for the regular file ``target``, granted through ``add``.

    The outcome is ``GRANTED``, ``READABLE``, ``ABSENT``, or None when the file is kept out.
    """
    shown = printable(target)
    try:
        st = os.lstat(target)
        chain = ancestry(target) if stat.S_ISREG(st.st_mode) else []
    except (FileNotFoundError, NotADirectoryError):
        session.skipped.append(shown)  # absent, as any other preset path: git reads nothing there either
        return None, ABSENT
    except OSError as exc:
        session.skipped.append(f"{shown}: {exc.strerror}")
        return None, None
    if not chain:
        session.skipped.append(f"{shown}: not a regular file")
        return None, None
    unnamed = _seatbelt_refusal(target, links)
    if unnamed:
        session.skipped.append(f"{shown}: {unnamed}")
        return None, None
    if session.readable.intersection(chain):  # already readable through another grant: no grant, no check
        if session.writable.intersection(chain):
            return None, READABLE
        return _names(read_regular(os.fsencode(target), session.denied, expect=chain[0]), kind), READABLE
    content: list[bytes] = []

    def accept(granted: str, _st: os.stat_result, checked: list[Identity]) -> bool:
        if _foreign_protected(session, granted):
            return False
        data = read_regular(os.fsencode(granted), session.denied, limit=CONFIG_BYTES + 1, expect=checked[0])
        if data is None or len(data) > CONFIG_BYTES:
            session.skipped.append(f"{shown}: not read whole (unreadable or over {CONFIG_BYTES} bytes), so not checked")
            return False
        findings = credential_findings(data, kind)
        if findings:
            session.skipped.append(shown)  # the warning says why
            session.warnings.append(_credential_warning(shown, findings, kind))
            session.withheld.append(checked)
            return False
        content.append(data)
        return True

    if not session.add(target, "ro", session.origin, strict=False, accept=accept):
        return None, None
    return _names(content[0], kind), GRANTED


def _grant_hooks(session: _Session, path: str) -> None:
    """Grant the ``core.hooksPath`` directory read-only, and so runnable, after the same guards."""
    effect = UNREADABLE["hooks"]
    resolved = _resolve(session, path)
    if resolved is None:
        session.warnings.append(f"git configuration: core.hooksPath {printable(path)} is not granted; {effect}")
        return
    target, links, in_home = resolved
    shown = printable(target)
    try:
        if not stat.S_ISDIR(os.lstat(target).st_mode):
            session.skipped.append(f"{shown}: not a directory")  # git finds no hooks there either
            return
        chain = ancestry(target)
    except (FileNotFoundError, NotADirectoryError):
        session.skipped.append(shown)  # git finds no hooks there either
        return
    except OSError as exc:
        session.skipped.append(f"{shown}: {exc.strerror}")
        return
    unnamed = _seatbelt_refusal(target, links)
    if unnamed:
        session.skipped.append(f"{shown}: {unnamed}")
        return
    if session.readable.intersection(chain):
        _followed(session, path, target, links, in_home, READABLE)
        return

    def accept(granted: str, _st: os.stat_result, checked: list[Identity]) -> bool:
        if _foreign_protected(session, granted):
            return False
        if any(checked[0] in withheld[1:] for withheld in session.withheld):
            session.skipped.append(f"{shown}: holds a git configuration file kept out as a credential")
            return False
        return True

    before = len(session.skipped)
    if session.add(target, "ro", session.origin, strict=False, accept=accept):
        _followed(session, path, target, links, in_home, GRANTED)
        return
    if links:
        _not_followed(session, path, target)
    # A refusal by the guards (or of another home's protected path) holds for --allow-read too.
    refused = any(entry.startswith(f"{target}: Refusing") for entry in session.skipped[before:])
    hint = "" if refused else f"; --allow-read {shown} grants it"
    session.warnings.append(f"git configuration: core.hooksPath {shown} is not granted; {effect}{hint}")


def _followed(session: _Session, path: str, target: str, links: list[str], in_home: bool, outcome: str) -> None:
    """Keep the links to ``target`` readable and, for links below the HOME, say once that they were followed."""
    session.links.extend(link for link in links if link not in session.links)
    if not in_home:
        return
    message = f"git configuration: {printable(path)} is {_link_kind(path)}, followed: git reads {printable(target)}, {outcome}"
    if message not in session.warnings:
        session.warnings.append(message)


def _not_followed(session: _Session, path: str, target: str) -> None:
    message = (
        f"{printable(path)}: {_link_kind(path)} to {printable(target)}, which is not granted; "
        "git inside reads it only if its target is granted"
    )
    if message not in session.skipped:
        session.skipped.append(message)


def _link_kind(path: str) -> str:
    try:
        own = stat.S_ISLNK(os.lstat(path).st_mode)
    except OSError:
        own = False
    return "a symbolic link" if own else "below a symbolic link"


def _foreign_protected(session: _Session, path: str) -> bool:
    """Refuse a path through a directory named like a protected path (``.ssh``...): the guards protect
    those of the policy's homes by identity, and ``~user/`` or an absolute path can name another's."""
    probe = path.rstrip("/") + "/"
    name = next((rel for rel in PROTECTED_RELATIVE if f"/{rel}/" in probe), None)
    if name is None:
        return False
    session.skipped.append(f"{path}: Refusing a path named like protected ~/{name}, of a home not protected here")
    return True


def _seatbelt_refusal(target: str, links: list[str]) -> str | None:
    """Why Seatbelt could not name ``target`` or a link to it in a rule, on macOS (``render_profile`` would raise)."""
    if not SEATBELT:
        return None
    from babylon60.confine import seatbelt

    for path in (target, *links):
        reason = seatbelt.rule_refusal(path)
        if reason:
            what = "it" if path == target else f"the symbolic link {printable(path)}"
            return f"Seatbelt cannot name {what} in a rule ({reason}), so it is not granted"
    return None


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
    if (section, key) == ("http", "extraheader"):
        return True
    if section == "credential" and key == "helper" and any(f"{word}=" in value.lower() for word in HELPER_WORDS):
        return True
    # A subsection on its own: in the name, "url." would end a scheme. So a url.<base>.insteadOf rewrite
    # is suspect only with a credential in its base or in its value.
    subsection = name[len(section) + 1 : -len(key) - 1] if name.count(".") > 1 else ""
    return _url_credential(subsection) or _url_credential(value)


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
