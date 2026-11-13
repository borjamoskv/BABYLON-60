"""Shared state locations for the CLI, MCP transport and client integration."""

from __future__ import annotations

import os
from pathlib import Path


def state_home() -> Path:
    value = os.environ.get("BABYLON_HOME", str(Path.home() / ".babylon60"))
    if not value.strip():
        raise ValueError("BABYLON_HOME must name a state directory")
    return Path(value).expanduser().absolute()


def legacy_causal_gate_path() -> Path:
    """The former checkout/install-relative location; never migrate a live WAL."""
    return Path(__file__).absolute().parents[2] / ".cortex" / "causal_gate.db"


def causal_gate_path(explicit: str | Path | None = None) -> Path:
    """Resolve one gate, refusing an implicit switch away from legacy state.

    An explicit argument or BABYLON_CAUSAL_GATE_DB selects the authoritative
    database. Otherwise every entry point uses BABYLON_HOME (or ~/.babylon60).
    Existing legacy SQLite state requires an explicit choice, not an automatic
    copy or merge of approvals and revocations.
    """
    selected = explicit if explicit is not None else os.environ.get("BABYLON_CAUSAL_GATE_DB")
    if selected is not None:
        if not str(selected).strip():
            raise ValueError("BABYLON_CAUSAL_GATE_DB must name the authoritative database")
        if str(selected) == ":memory:":
            return Path(":memory:")
        return Path(selected).expanduser().absolute()
    canonical = state_home() / "causal_gate.db"
    legacy = legacy_causal_gate_path()
    legacy_files = (legacy, Path(f"{legacy}-wal"), Path(f"{legacy}-shm"))
    if legacy != canonical and any(p.exists() or p.is_symlink() for p in legacy_files):
        raise ValueError(
            f"Legacy authorization state exists at {legacy}. No database was selected or migrated. "
            "Set BABYLON_CAUSAL_GATE_DB (or --db/--causal-gate) explicitly to the authoritative database "
            "for both CLI and MCP before approving or revoking requests."
        )
    return canonical
