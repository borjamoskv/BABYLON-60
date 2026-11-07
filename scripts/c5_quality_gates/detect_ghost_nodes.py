#!/usr/bin/env python3
"""Check local code references and retain reviewed documentary reference contexts.

The context registry distinguishes external APIs, literals, documentary contracts,
archived terminology and illustrative designs from claims about local symbols.
An unclassified missing identifier still fails; stale registry entries also fail.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from collections.abc import Iterator

EXCLUDE_DIRS = {
    ".git",
    "target",
    "dist",
    "scratch",
    ".lake",
    ".jj",
    ".hypothesis",
    ".audit",
    "site",
    "assets",
    ".venv",
    "__pycache__",
    "node_modules",
}
CODE_EXTS = (".rs", ".py", ".ts", ".swift", ".lean", ".c", ".h", ".cpp", ".hpp")
DOC_EXTS = (".md",)
CONTEXT_FILE = Path("scripts/c5_quality_gates/documented_reference_contexts.json")
CONTEXT_KINDS = {"external", "literal", "document_contract", "historical", "proposal"}
IDENTIFIER = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]+\b")
INLINE_REFERENCE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]+)`")


@dataclass(frozen=True)
class ReferenceContext:
    kind: str
    reason: str
    evidence: str


def _files(root_dir: str | Path, extensions: tuple[str, ...]) -> Iterator[Path]:
    for directory, dirs, files in os.walk(root_dir):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS)
        for name in sorted(files):
            if name.endswith(extensions):
                yield Path(directory) / name


def build_symbol_table(root_dir: str | Path) -> set[str]:
    """Index identifiers in source files; read failures are reported, not ignored."""
    symbols: set[str] = set()
    for path in _files(root_dir, CODE_EXTS):
        symbols.update(IDENTIFIER.findall(path.read_text(encoding="utf-8")))
    return symbols


def _load_contexts(root: Path) -> dict[tuple[str, str], ReferenceContext]:
    registry = root / CONTEXT_FILE
    if not registry.exists():
        return {}
    raw: object = json.loads(registry.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError(f"{registry}: expected reference registry schema 1")
    references = raw.get("references")
    if not isinstance(references, list):
        raise ValueError(f"{registry}: references must be a list")
    result: dict[tuple[str, str], ReferenceContext] = {}
    for entry in references:
        if not isinstance(entry, dict):
            raise ValueError(f"{registry}: invalid reference entry")
        fields = [entry.get(name) for name in ("path", "symbol", "kind", "reason", "evidence")]
        if any(not isinstance(value, str) or not value.strip() for value in fields):
            raise ValueError(f"{registry}: every entry requires nonempty string fields")
        path, symbol, kind, reason, evidence = (str(value) for value in fields)
        if kind not in CONTEXT_KINDS:
            raise ValueError(f"{registry}: unknown reference kind {kind!r}")
        relative = Path(path)
        if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".md":
            raise ValueError(f"{registry}: invalid document path {path!r}")
        if not IDENTIFIER.fullmatch(symbol):
            raise ValueError(f"{registry}: invalid reference symbol {symbol!r}")
        key = (relative.as_posix(), symbol)
        if key in result:
            raise ValueError(f"{registry}: duplicate reference context {key!r}")
        document = root / relative
        if not document.is_file() or f"`{symbol}`" not in document.read_text(encoding="utf-8"):
            raise ValueError(f"{registry}: stale reference context {key!r}")
        current_context = "\n".join(
            line.strip() for line in document.read_text(encoding="utf-8").splitlines() if f"`{symbol}`" in line
        )
        expected_hash = entry.get("context_sha256")
        if expected_hash != hashlib.sha256(current_context.encode("utf-8")).hexdigest():
            raise ValueError(f"{registry}: documentary context changed and needs review: {key!r}")
        result[key] = ReferenceContext(kind, reason, evidence)
    return result


def audit_ghost_nodes(root_dir: str | Path, symbol_table: set[str]) -> set[tuple[str, str]]:
    """Reject missing local identifiers unless their exact document context was reviewed."""
    root = Path(root_dir).absolute()
    contexts = _load_contexts(root)
    ghosts: set[tuple[str, str]] = set()
    for path in _files(root, DOC_EXTS):
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        for symbol in INLINE_REFERENCE.findall(content):
            if symbol in symbol_table or len(symbol) <= 4:
                continue
            if f"[OBSOLETO: {symbol}]" in content:
                continue
            if (relative, symbol) in contexts:
                continue
            ghosts.add((str(path), symbol))
    return ghosts


def main() -> int:
    root = Path(__file__).absolute().parents[2]
    try:
        symbols = build_symbol_table(root)
        ghosts = audit_ghost_nodes(root, symbols)
        contexts = _load_contexts(root)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL: reference scan: {error}", file=sys.stderr)
        return 1
    print(f"Indexed {len(symbols)} source identifiers; {len(contexts)} reviewed documentary contexts.")
    if ghosts:
        print(f"FAIL: {len(ghosts)} unresolved local code references.")
        for path, symbol in sorted(ghosts):
            print(f"  {symbol}: {Path(path).relative_to(root)}")
        return 1
    print("PASS: zero unresolved local code references; all context records remain linked to documents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
