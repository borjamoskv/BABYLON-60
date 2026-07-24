# [C5-REAL] Exergy-Maximized
"""Path Guard System (C5-REAL Security)."""

from __future__ import annotations

from pathlib import Path

FORBIDDEN_PREFIXES = (
    "/private/var/db",
    "/System",
    "/Mobile Documents",
    "/colima",
)


def is_safe_path(path: str | Path) -> bool:
    """Validate if a path is safe to operate on, preserving R5 system boundaries."""
    try:
        resolved = str(Path(path).resolve())
        for forbidden in FORBIDDEN_PREFIXES:
            if resolved.startswith(forbidden):
                return False
        return True
    except (ValueError, TypeError, OSError):
        return False
