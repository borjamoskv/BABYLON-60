"""macOS Seatbelt rendering of a confinement policy.

Seatbelt starts from ``(allow default)`` so agents keep network and process
access; the filesystem rules then deny every home directory (the account home
from ``pwd``, ``$HOME`` and any synthetic demo home), re-allow the granted
paths and finally deny the protected set again. In SBPL a later matching rule
overrides an earlier one; that precedence is exercised by the macOS CI job and
stays NO_VERIFICADO until it runs there.

Seatbelt matches resolved vnode paths (``/var`` is ``/private/var``), so every
rule is emitted for the logical path and, when it differs, for its real path.
This is rule rendering, not a root decision: the grants themselves were already
checked by inode identity in ``policy.py``.
"""

from __future__ import annotations

from collections.abc import Iterable
import os

from babylon60.confine.policy import Policy
from babylon60.kernel.mcp_sandbox_validator import SANDBOX_EXEC, _literal

__all__ = ["SANDBOX_EXEC", "render_profile", "available"]


def available() -> bool:
    return os.path.isfile(SANDBOX_EXEC)


def _forms(path: str) -> list[str]:
    forms = [os.path.abspath(path)]
    real = os.path.realpath(path)
    if real not in forms:
        forms.append(real)
    return forms


def _filters(kind: str, paths: Iterable[str]) -> str:
    seen: list[str] = []
    for path in paths:
        for form in _forms(path):
            if form not in seen:
                seen.append(form)
    return " ".join(f"({kind} {_literal(p)})" for p in seen)


def _ancestors(path: str) -> list[str]:
    result: list[str] = []
    current = os.path.dirname(os.path.abspath(path))
    while current and current != "/":
        result.append(current)
        current = os.path.dirname(current)
    return result


def render_profile(policy: Policy, *, unix_sockets: bool = False) -> str:
    deny_roots = ["/Users", *policy.homes]
    granted = [g for g in policy.grants if g.origin != "system"]
    rw = [g.path for g in granted if g.access == "rw"]
    ro = [g.path for g in granted if g.access == "ro"]
    lines = ["(version 1)", "(allow default)"]
    lines.append(f"(deny file-read* file-write* {_filters('subpath', deny_roots)})")
    metadata = sorted({a for g in granted for a in _ancestors(g.path)})
    if metadata:
        lines.append(f"(allow file-read-metadata {_filters('literal', metadata)})")
    for grant in granted:
        kind = "subpath" if grant.is_dir else "literal"
        operations = "file-read* file-write*" if grant.path in rw else "file-read*"
        if grant.path in rw or grant.path in ro:
            lines.append(f"(allow {operations} {_filters(kind, [grant.path])})")
    if policy.protected:
        lines.append(f"(deny file-read* file-write* {_filters('subpath', policy.protected)})")
    return "\n".join(lines) + "\n"
