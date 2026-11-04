"""The documentation gate preserves reviewed context and still rejects missing local code."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest
from scripts.c5_quality_gates.detect_ghost_nodes import (
    CONTEXT_FILE,
    audit_ghost_nodes,
    build_symbol_table,
)


def _registry(root: Path, **changes: object) -> None:
    entry: dict[str, object] = {
        "path": "guide.md",
        "symbol": "ForeignClient",
        "kind": "external",
        "reason": "Name attributed to an external SDK by this document.",
        "evidence": "guide.md describes this as an external client.",
    }
    document = root / "guide.md"
    context = "\n".join(line.strip() for line in document.read_text().splitlines() if "`ForeignClient`" in line)
    entry["context_sha256"] = hashlib.sha256(context.encode()).hexdigest()
    entry.update(changes)
    path = root / CONTEXT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "references": [entry]}))


def test_known_and_missing_local_identifiers(tmp_path: Path) -> None:
    (tmp_path / "local.py").write_text("class LocalVerifier: pass\n")
    (tmp_path / "guide.md").write_text("`LocalVerifier` and `MissingVerifier`")
    assert audit_ghost_nodes(tmp_path, build_symbol_table(tmp_path)) == {
        (str(tmp_path / "guide.md"), "MissingVerifier")
    }


def test_context_is_scoped_to_exact_document_and_symbol(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("External SDK: `ForeignClient`; local claim: `MissingVerifier`.")
    (tmp_path / "other.md").write_text("Local implementation: `ForeignClient`.")
    _registry(tmp_path)
    assert audit_ghost_nodes(tmp_path, set()) == {
        (str(tmp_path / "guide.md"), "MissingVerifier"),
        (str(tmp_path / "other.md"), "ForeignClient"),
    }


@pytest.mark.parametrize(
    "change",
    [
        {"path": "../outside.md"},
        {"kind": "ignore"},
        {"reason": ""},
        {"symbol": "NoLongerMentioned"},
    ],
)
def test_invalid_or_stale_context_is_rejected(tmp_path: Path, change: dict[str, object]) -> None:
    (tmp_path / "guide.md").write_text("`ForeignClient`")
    _registry(tmp_path, **change)
    with pytest.raises(ValueError):
        audit_ghost_nodes(tmp_path, set())


def test_warmup_and_repeated_scan_keeps_local_failure_visible(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("`ForeignClient` and `MissingVerifier`.")
    _registry(tmp_path)
    expected = {(str(tmp_path / "guide.md"), "MissingVerifier")}
    for _ in range(16):
        assert audit_ghost_nodes(tmp_path, set()) == expected
    for _ in range(256):
        assert audit_ghost_nodes(tmp_path, set()) == expected


def test_context_change_requires_new_review(tmp_path: Path) -> None:
    document = tmp_path / "guide.md"
    document.write_text("External SDK: `ForeignClient`.")
    _registry(tmp_path)
    assert audit_ghost_nodes(tmp_path, set()) == set()
    document.write_text("The local runtime implements `ForeignClient`.")
    with pytest.raises(ValueError, match="context changed"):
        audit_ghost_nodes(tmp_path, set())
