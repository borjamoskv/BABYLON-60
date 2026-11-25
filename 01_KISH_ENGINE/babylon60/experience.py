"""Packaged guidance shared by onboarding, CLI and MCP transports."""

from __future__ import annotations

from importlib.resources import files

PRESENTATION_URI = "babylon://presentation/guide"
MAX_SESSION_PROFILE_BYTES = 2_000


def load_session_profile() -> str:
    """Return the small, self-contained preferences installed in Codex."""
    profile = files("babylon60").joinpath("session_profile.md").read_text(encoding="utf-8")
    if not profile.strip() or len(profile.encode("utf-8")) > MAX_SESSION_PROFILE_BYTES:
        raise ValueError("The Babylon session profile must contain 1 to 2000 UTF-8 bytes.")
    return profile


def load_mcp_instructions() -> str:
    """Return server guidance; broader response preferences belong to the host."""
    return files("babylon60").joinpath("mcp_instructions.md").read_text(encoding="utf-8")


def load_presentation_guide() -> str:
    """Keep the complete portable contract available independently of onboarding."""
    return files("babylon60").joinpath("presentation.md").read_text(encoding="utf-8")
