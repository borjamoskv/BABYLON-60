from __future__ import annotations

from pathlib import Path

FORBIDDEN_PREFIXES = ('/private/var/db', '/System', '/Mobile Documents', '/colima')

def is_safe_path(path: str | Path) -> bool:
    try:
        resolved = str(Path(path).resolve())
        for forbidden in FORBIDDEN_PREFIXES:
            if resolved.startswith(forbidden):
                return False
        return True
    except (ValueError, TypeError, OSError):
        return False