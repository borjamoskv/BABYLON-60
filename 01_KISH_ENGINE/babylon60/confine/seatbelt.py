"""macOS Seatbelt rendering of a confinement policy.

The profile keeps ``(allow default)`` for processes, Mach services and IP
networking, and narrows the rest:

* reads: every home directory (the account home from ``pwd``, ``$HOME`` and any
  synthetic demo home) and ``/Users`` are denied, the grants are re-allowed and
  the protected set is denied again, last;
* writes: denied everywhere, then allowed only on read-write grants, on the
  session's own terminals (grants of origin ``tty``) and on ``/dev/null``,
  ``/dev/zero``, ``/dev/dtracehelper``, ``/dev/tty`` and ``/dev/fd`` (re-opening a
  descriptor the process already holds). Nothing on ``PATH`` outside the grants,
  such as ``/opt/homebrew/bin`` or ``/usr/local/bin``, stays writable;
* hard links and clones: denied unless their source is a grant (clone: any
  grant; link: read-write grants only, since a link would let writes through to
  its source). Apple's own version-1 profiles deny ``file-link`` and
  ``file-clone`` explicitly because ``default`` does not cover them. Ancestors
  of the protected set can be neither cloned nor renamed, so a protected path
  created inside a grant after the policy was built cannot be carried away;
* ``F_MAKECOMPRESSED`` and ``F_TRANSFEREXTENTS``, which change a file through a
  read-only descriptor, are denied;
* other terminals (``/dev/ttysN``) are denied unless the policy allows ptys,
  which also makes ``/dev/ptmx`` and the ttys writable;
* ``connect`` to pathname Unix sockets is denied except mDNSResponder (DNS) and
  syslog, unless the launch allows Unix sockets;
* reads are also denied in shared places outside the homes (``/private/tmp``,
  ``/private/var/tmp``, ``/Volumes`` and the user's ``/private/var/folders``
  directory), where the grants (the private TMPDIR) are re-allowed;
* what would run code outside the sandbox is denied: LaunchServices opens
  (``lsopen``), Apple Events and launchd job creation; so are signals, process
  information (``KERN_PROCARGS2`` included) and task ports (debugging) for any process
  outside the sandbox, preference writes through cfprefsd, and the pasteboard (unless
  ``clipboard``), Kerberos (GSSCred), CoreSimulator, DiskArbitration, window server,
  Apple Event, accessibility and text input services. Signals, process information
  and task ports are allowed back for the sandbox's own processes (the agent and its
  children).

Precedence: among rules that carry a filter the last match wins; an unfiltered
rule is only the operation's fallback, and a rule naming an operation outright
outranks one that reaches it through a wildcard. Every override below is both
later and at least as specific, so it holds under either reading.

Seatbelt matches resolved vnode paths (``/var`` is ``/private/var``), so every
path rule is emitted for the logical path, its real path and, below a firmlink
of the data volume (``/Users``, ``/private``, ``/opt``, ``/usr/local``, ...), the
same path through ``/System/Volumes/Data``. Deny rules also get a regex that
matches any ASCII letter case, for case-insensitive volumes; allow rules stay
exact, so a case-sensitive volume never gains a sibling grant. This is rule
rendering, not a root decision: the grants were already checked by inode
identity in ``policy.py``.

Seatbelt's runtime behaviour described here is NO_VERIFICADO until the macOS CI
job runs ``tests/test_confine_seatbelt.py``.
"""

from __future__ import annotations

from collections.abc import Iterable
import os
import sys

from babylon60.confine.policy import Policy
from babylon60.kernel.mcp_sandbox_validator import SANDBOX_EXEC, _literal

__all__ = ["SANDBOX_EXEC", "render_profile", "rule_refusal", "available"]

# Firmlinks from the system volume into the data volume (/usr/share/firmlinks).
DATA_VOLUME = "/System/Volumes/Data"
FIRMLINKS = (
    "/AppleInternal",
    "/Applications",
    "/Library",
    "/System/Library/Caches",
    "/System/Library/Assets",
    "/System/Library/PreinstalledAssets",
    "/System/Library/AssetsV2",
    "/System/Library/PreinstalledAssetsV2",
    "/System/Library/CoreServices/CoreTypes.bundle/Contents/Library",
    "/System/Library/Speech",
    "/Users",
    "/Volumes",
    "/cores",
    "/opt",
    "/private",
    "/usr/local",
    "/usr/libexec/cups",
    "/usr/share/snmp",
)
DEVICE_WRITES = ("/dev/null", "/dev/zero", "/dev/dtracehelper", "/dev/tty")
DESCRIPTOR_DIR = "/dev/fd"
PTY_MASTER = "/dev/ptmx"
TERMINALS = "^/dev/ttys[0-9]+$"
TERMINAL_ORIGINS = ("tty", "ptys")
UNIX_SOCKET_EXCEPTIONS = ("/private/var/run/mDNSResponder", "/private/var/run/syslog")
MUTATING_FCNTLS = (80, 110)  # F_MAKECOMPRESSED, F_TRANSFEREXTENTS (sys/fcntl.h)
# Services that start code outside the sandbox on the caller's behalf: LaunchServices (`open`),
# Apple Events (osascript to Terminal, iTerm2, Finder, System Events) and launchd jobs (launchctl).
OUTSIDE_OPERATIONS = ("lsopen", "appleevent-send", "job-creation")
# Synthetic keyboard and mouse events into other apps (INV_C5_COMPUTER_USE_TRUST_GATEWAY, agent_contracts.md).
GUI_INJECTION_OPERATIONS = ("hid-control",)
# XNU lets a user mount over any directory they own (/opt/homebrew/bin, ~/.ssh): not a file-write* operation.
MOUNT_OPERATIONS = ("file-mount", "file-unmount")
# Other processes of the user: signals, process information (which includes the argv and
# environment area KERN_PROCARGS2, `ps -E`, returns) and task ports (task_for_pid: lldb, which then
# runs code inside the target). Each is denied for every target and allowed back for the sandbox
# itself, so that the agent can still debug its own builds. Never "(target others)" alone: with it, a
# confined probe still read the environment of a process in its own process group (macos-15, CI of d594608).
PROCESS_RULES = (
    "(deny signal)",
    "(allow signal (target self) (target same-sandbox))",
    "(deny process-info*)",
    "(allow process-info* (target self) (target same-sandbox))",
    '(deny sysctl-read (sysctl-name-prefix "kern.procargs"))',
    "(when (defined? 'mach-priv-task-port) (deny mach-priv-task-port))",
    "(when (defined? 'mach-priv-task-port) (allow mach-priv-task-port (target same-sandbox)))",
)
# cfprefsd writes ~/Library/Preferences for the caller: a write outside the grants (Terminal's Shell key).
PREFERENCE_RULES = ("(deny user-preference-write)",)
# Setuid and setgid modes, as the seccomp filter refuses them on Linux: filtered and emitted after the
# grants, so it also wins over their file-write* allow under either precedence reading.
SETID_RULE = '(when (defined? \'file-write-setugid) (deny file-write-setugid (subpath "/")))'
CLIPBOARD_SERVICE = "com.apple.pasteboard.1"
# `run --allow-clipboard` opens both directions of the pasteboard.
CLIPBOARD_WARNING = (
    "allow_clipboard: the agent can read whatever you copy, a password from your password manager included, "
    "and replace it, so what you paste next, into another terminal too, can be a command it wrote"
)
DENIED_SERVICES = (
    "com.apple.GSSCred",  # Kerberos credential caches (API: and KCM:), the macOS twin of kernel keyrings
    "com.apple.CoreSimulator.CoreSimulatorService",  # simctl spawn starts processes outside this sandbox
    "com.apple.DiskArbitration.diskarbitrationd",  # mounts images over directories the user owns
    # INV_C5_COMPUTER_USE_TRUST_GATEWAY (docs/03_guides/agent_contracts.md): no view of or input into other apps.
    "com.apple.windowserver.active",  # the window server: screen capture, windows, synthetic events
    "com.apple.accessibility.AXServer",  # drives other apps' UI
    "com.apple.coreservices.appleevents",  # Apple Event delivery, besides (deny appleevent-send)
    "com.apple.tsm.portname",  # text input into other apps
)
# Read-denied outside the homes: shared temporary directories, the user's per-user directory under
# /private/var/folders (other apps' T, C and 0, other sessions' private TMPDIRs), mounted volumes
# (external disks, network shares, Time Machine backups) and Homebrew's service data (databases).
SHARED_READ_ROOTS = ("/private/tmp", "/private/var/tmp", "/Volumes", "/opt/homebrew/var", "/usr/local/var")
CS_DARWIN_USER_DIR = 65536  # confstr(_CS_DARWIN_USER_DIR): /private/var/folders/xx/yyy/0/
# sandbox-exec rejects a string literal longer than 1025 bytes and then the whole profile.
MAX_STRING_BYTES = 1000
_REGEX_SPECIAL = frozenset(".^$*+?()[]{}|\\")


def available() -> bool:
    return os.path.isfile(SANDBOX_EXEC)


def shared_read_roots() -> list[str]:
    """Shared places outside the homes that hold other programs' files; on macOS also the per-user directory."""
    roots = list(SHARED_READ_ROOTS)
    if sys.platform == "darwin":
        try:
            user_dir = os.confstr(CS_DARWIN_USER_DIR)
        except (ValueError, OSError):
            user_dir = None
        if user_dir:
            roots.append(os.path.dirname(os.path.realpath(user_dir.rstrip("/"))))
    return roots


def _quote(text: str) -> str:
    quoted = _literal(text)
    if len(quoted.encode("utf-8")) > MAX_STRING_BYTES:
        raise ValueError(f"Path too long for a Seatbelt string literal ({len(quoted.encode('utf-8'))} bytes)")
    return quoted


def _under(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def _data_volume_twin(path: str) -> str | None:
    """The same path through the other side of a firmlink, if it crosses one."""
    if _under(path, DATA_VOLUME):
        rest = path[len(DATA_VOLUME) :]
        return rest if any(_under(rest, root) for root in FIRMLINKS) else None
    return DATA_VOLUME + path if any(_under(path, root) for root in FIRMLINKS) else None


def _forms(path: str) -> list[str]:
    """Logical path, real path and their data-volume twins, in that order and without repeats."""
    forms: list[str] = []
    for base in (os.path.abspath(path), os.path.realpath(path)):
        for form in (base, _data_volume_twin(base)):
            if form is not None and form not in forms:
                forms.append(form)
    return forms


def _expand(paths: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(form for path in paths for form in _forms(path)))


def _filters(kind: str, paths: Iterable[str]) -> list[str]:
    return [f"({kind} {_quote(form)})" for form in _expand(paths)]


def rule_refusal(path: str) -> str | None:
    """Why a rule naming ``path`` cannot be rendered (``render_profile`` would raise ``ValueError``), or None.

    A control character, or a form of the path (``_forms``) longer than a string literal may be.
    """
    try:
        _filters("literal", [path])
    except ValueError as exc:
        return str(exc)
    return None


def _rule(action: str, operations: str, filters: Iterable[str]) -> str:
    return f"({action} {operations} {' '.join(filters)})"


def _fold(text: str) -> str:
    return "".join(char.lower() if char.isascii() else char for char in text)


def _any_case(text: str) -> str:
    """Regex for ``text`` with ASCII letters in either case and metacharacters escaped."""
    parts: list[str] = []
    for char in text:
        if char.isascii() and char.isalpha():
            parts.append(f"[{char.upper()}{char.lower()}]")
        elif char in _REGEX_SPECIAL:
            parts.append("\\" + char)
        else:
            parts.append(char)
    return "".join(parts)


def _outermost(paths: Iterable[str]) -> list[str]:
    """Drop paths already inside another path of the list, compared in any ASCII case."""
    unique = list(dict.fromkeys(paths))
    folded = [_fold(path) for path in unique]
    return [
        path
        for path, own in zip(unique, folded)
        if not any(other != own and own.startswith(other.rstrip("/") + "/") for other in folded)
    ]


def _any_case_filters(paths: Iterable[str]) -> list[str]:
    """Regex filters for each path and its subtree in any ASCII letter case.

    Siblings share one regex per parent directory, split so that no string
    literal exceeds ``MAX_STRING_BYTES``.
    """
    groups: dict[str, dict[str, None]] = {}
    for path in _outermost(paths):
        parent, name = os.path.split(path)
        if name:
            groups.setdefault(parent, {})[_any_case(name)] = None
    filters: list[str] = []
    for parent, names in groups.items():
        head, tail = "^" + _any_case(parent.rstrip("/")) + "/(", ")(/.*)?$"
        chunk: list[str] = []
        for name in names:
            candidate = head + "|".join([*chunk, name]) + tail
            if chunk and len(_literal(candidate).encode("utf-8")) > MAX_STRING_BYTES:
                filters.append(f"(regex {_quote(head + '|'.join(chunk) + tail)})")
                chunk = []
            chunk.append(name)
        filters.append(f"(regex {_quote(head + '|'.join(chunk) + tail)})")
    return filters


def _ancestors(path: str) -> list[str]:
    result: list[str] = []
    current = os.path.dirname(os.path.abspath(path))
    while current and current != "/":
        result.append(current)
        current = os.path.dirname(current)
    return result


def render_profile(
    policy: Policy,
    *,
    unix_sockets: bool = False,
    clipboard: bool = False,
    shared_roots: Iterable[str] = (),
) -> str:
    """``shared_roots``: read-denied places outside the homes; the launcher passes ``shared_read_roots()``."""
    deny_roots = ["/Users", *policy.homes, *shared_roots]
    terminals = [g for g in policy.grants if g.origin in TERMINAL_ORIGINS]
    granted = [
        g
        for g in policy.grants
        if g.origin != "system" and g.origin not in TERMINAL_ORIGINS and g.access in ("rw", "ro")
    ]
    lines = ["(version 1)", "(allow default)"]
    lines.append(
        _rule(
            "deny",
            "file-read* file-write*",
            [*_filters("subpath", deny_roots), *_any_case_filters(_expand(deny_roots))],
        )
    )
    # Writes, hard links and clones become an allow-list; unfiltered rules are only fallbacks.
    lines.append("(deny file-write*)")
    lines.append("(deny file-link file-clone)")
    fcntls = " ".join(str(command) for command in MUTATING_FCNTLS)
    lines.append(f"(when (defined? 'system-fcntl) (deny system-fcntl (fcntl-command {fcntls})))")
    devices = [f"(literal {_quote(path)})" for path in DEVICE_WRITES]
    lines.append(_rule("allow", "file-write*", [*devices, f"(subpath {_quote(DESCRIPTOR_DIR)})"]))
    metadata = sorted(
        {a for g in granted for a in _ancestors(g.path)} | {a for link in policy.links for a in _ancestors(link)}
    )
    if metadata:
        lines.append(_rule("allow", "file-read-metadata", _filters("literal", metadata)))
    for grant in granted:
        kind = "subpath" if grant.is_dir else "literal"
        if grant.access == "rw":
            operations = "file-read* file-write* file-link file-clone"
        else:
            operations = "file-read* file-clone"
        lines.append(_rule("allow", operations, _filters(kind, [grant.path])))
    if policy.links:
        # Following a symbolic link reads the link: allow exactly the links to the command.
        lines.append(_rule("allow", "file-read*", _filters("literal", list(policy.links))))
    if policy.allow_ptys:
        lines.append(
            _rule(
                "allow", "file-read* file-write*", [f"(literal {_quote(PTY_MASTER)})", f"(regex {_quote(TERMINALS)})"]
            )
        )
    else:
        lines.append(_rule("deny", "file-read* file-write*", [f"(regex {_quote(TERMINALS)})"]))
    if terminals:
        own = [
            *_filters("literal", [g.path for g in terminals if not g.is_dir]),
            *_filters("subpath", [g.path for g in terminals if g.is_dir]),
        ]
        lines.append(_rule("allow", "file-read* file-write*", own))
    if not unix_sockets:
        lines.append("(deny network-outbound (remote unix-socket))")
        exceptions = [f"(remote unix-socket (path-literal {_quote(path)}))" for path in UNIX_SOCKET_EXCEPTIONS]
        lines.append(_rule("allow", "network-outbound", exceptions))
    # Operations no file rule reaches: each names its operation outright, so it outranks (allow default).
    lines.extend(
        f"(deny {operation})" for operation in (*OUTSIDE_OPERATIONS, *GUI_INJECTION_OPERATIONS, *MOUNT_OPERATIONS)
    )
    lines.extend(PROCESS_RULES)
    lines.extend(PREFERENCE_RULES)
    lines.append(SETID_RULE)
    services = [*DENIED_SERVICES, *(() if clipboard else (CLIPBOARD_SERVICE,))]
    lines.append(_rule("deny", "mach-lookup", [f"(global-name {_quote(name)})" for name in services]))
    if policy.protected:
        protected = _expand(policy.protected)
        # A protected path created after the policy was built can sit inside a grant; renaming
        # or cloning one of its ancestors would carry it past the path rules below.
        ancestors = sorted({a for path in protected for a in _ancestors(path)})
        lines.append(_rule("deny", "file-write-unlink file-clone", [f"(literal {_quote(a)})" for a in ancestors]))
        lines.append(
            _rule(
                "deny",
                "file-read* file-write* file-link file-clone",
                [*_filters("subpath", policy.protected), *_any_case_filters(protected)],
            )
        )
    return "\n".join(lines) + "\n"
