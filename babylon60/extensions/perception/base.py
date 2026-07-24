# [C5-REAL] Exergy-Maximized
"""
Perception Base & Models.

Foundational types and classification logic used by the Perception Engine.
Optimized for high-frequency file event processing and project inference.
Provides the data schema for user behavioral state tracking (Industrial Noir).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

__all__ = [
    "BehavioralSnapshot",
    "FileEvent",
    "classify_file",
    "infer_project_from_path",
    "should_ignore",
]


DEBOUNCE_SECONDS: Final[float] = 2.0
INFERENCE_WINDOW_SECONDS: Final[int] = 300  # 5 minutes
RECORD_COOLDOWN_SECONDS: Final[int] = 300  # 1 episode per 5min per project
MIN_EVENTS_FOR_INFERENCE: Final[int] = 3  # need at least 3 events to infer

_EXT_ROLES: Final[dict[str, str]] = {
    ".py": "source",
    ".ts": "source",
    ".tsx": "source",
    ".js": "source",
    ".jsx": "source",
    ".swift": "source",
    ".rs": "source",
    ".go": "source",
    ".css": "source",
    ".html": "source",
    ".c": "source",
    ".cpp": "source",
    ".json": "config",
    ".toml": "config",
    ".yaml": "config",
    ".yml": "config",
    ".ini": "config",
    ".env": "config",
    "Makefile": "config",
    "Dockerfile": "config",
    ".md": "docs",
    ".txt": "docs",
    ".rst": "docs",
    ".pdf": "docs",
    ".png": "asset",
    ".jpg": "asset",
    ".jpeg": "asset",
    ".svg": "asset",
    ".webp": "asset",
    ".gif": "asset",
    ".ico": "asset",
    ".mp3": "asset",
    ".mp4": "asset",
    ".woff": "asset",
    ".woff2": "asset",
    ".ttf": "asset",
}

_ROLE_PATTERNS: Final[list[tuple[str, re.Pattern]]] = [
    ("test", re.compile(r"(test_|_test\.|spec\.|\.test\.)", re.IGNORECASE)),
]

_IGNORE_PATTERNS: Final[re.Pattern] = re.compile(
    r"(\.git/|__pycache__/|\.pyc$|node_modules/|\.DS_Store|\.venv/|\.pytest_cache/|dist/|build/|\.next/|\.turbo/)"
)


@dataclass()
class FileEvent:
    """A single file system event after debouncing."""

    path: str
    event_type: str  # created, modified, deleted, moved
    role: str  # test, config, docs, asset, source, unknown
    project: str | None
    timestamp: float

    @property
    def basename(self) -> str:
        """Name of the file without directory path."""
        return Path(self.path).name


@dataclass()
class BehavioralSnapshot:
    """Inferred user behavior from a window of file events."""

    intent: str
    emotion: str  # frustrated, flow, curious, cautious, confident, neutral
    confidence: str  # C1-C5
    project: str | None
    event_count: int
    window_seconds: float
    top_files: list[str]
    summary: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable representation."""
        return {
            "intent": self.intent,
            "emotion": self.emotion,
            "confidence": self.confidence,
            "project": self.project,
            "event_count": self.event_count,
            "window_seconds": round(self.window_seconds, 1),
            "top_files": self.top_files[:10],  # Increased visibility
            "summary": self.summary,
            "timestamp": self.timestamp,
        }




def classify_file(path: str) -> str:
    """
    Classify a file path into a role category.
    Uses O(1) extension mapping first, then regex for complex roles like tests.
    """
    p = Path(path)

    for role, pattern in _ROLE_PATTERNS:
        if pattern.search(path):
            return role

    ext = p.suffix.lower()
    if ext in _EXT_ROLES:
        return _EXT_ROLES[ext]

    if p.name.startswith(".env"):
        return "config"

    if p.name in _EXT_ROLES:
        return _EXT_ROLES[p.name]

    return "unknown"


def infer_project_from_path(path: str, workspace_root: str | None = None) -> str | None:
    """
    Infer project name from file path with support for monorepo structures.
    Recognizes 'packages/', 'apps/', and 'services/' sub-layouts.
    """
    p = Path(path)

    if workspace_root:
        project = _infer_from_workspace(p, Path(workspace_root))
        if project:
            return project

    return _infer_from_parents(p)


def _infer_from_workspace(p: Path, root: Path) -> str | None:
    """Extract project name relative to workspace root."""
    try:
        rel = p.relative_to(root)
        parts = rel.parts
        if not parts:
            return root.name

        monorepo_dirs = ("packages", "apps", "services", "src")
        if len(parts) >= 2 and parts[0] in monorepo_dirs:
            return parts[1]

        return parts[0] if parts[0] else root.name  # type: ignore[reportGeneralTypeIssues]
    except ValueError:
        return None


def _infer_from_parents(p: Path) -> str | None:
    """Fallback: scan up parents until we find a common project marker. (Complexity Crushed O(1))"""
    ignore_dirs = {"src", "lib", "internal", "pkg", "docs", "tests", ".", "/"}
    return next((parent.name for parent in p.parents if parent.name not in ignore_dirs), None)


def should_ignore(path: str) -> bool:
    """Check if a path should be ignored (git, node_modules, build artifacts)."""
    return bool(_IGNORE_PATTERNS.search(path))
