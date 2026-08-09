# ============================================================================
# BABYLON-60 Sovereign Security Guard
# █ PATH_GUARD | Real-Time Path Validation & Traversal Prevention
# ============================================================================

from __future__ import annotations

from pathlib import Path

__all__ = ["is_safe_path"]


def is_safe_path(path: str | Path, base_dir: str | Path | None = None) -> bool:
    """
    Validates if a given path is safe and stays within allowable boundaries,
    preventing directory traversal (../) and unauthorized system access.
    """
    try:
        resolved_path = Path(path).resolve()
        if base_dir:
            base_resolved = Path(base_dir).resolve()
            return base_resolved in resolved_path.parents or resolved_path == base_resolved
        
        # Default safety check: block system root sensitive paths
        forbidden_prefixes = [Path("/etc"), Path("/proc"), Path("/sys"), Path("/dev")]
        for forbidden in forbidden_prefixes:
            if forbidden in resolved_path.parents or resolved_path == forbidden:
                return False
        return True
    except Exception:
        return False
