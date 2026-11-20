#!/usr/bin/env python3
"""Check local code references and retain reviewed documentary reference contexts.

The context registry distinguishes external APIs, literals, documentary contracts,
archived terminology and illustrative designs from claims about local symbols.
An unclassified missing identifier still fails; stale registry entries also fail.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from collections.abc import Iterator

EXCLUDE_DIRS = {
    ".git",
    "target",
    "dist",
    "scratch",
    "build",
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
EXCLUDE_REL_DIRS = {"tools/skill_library/codex_overrides"}
CODE_EXTS = (".rs", ".py", ".ts", ".swift", ".lean", ".c", ".h", ".cpp", ".hpp")
DOC_EXTS = (".md",)
CONTEXT_FILE = Path("scripts/c5_quality_gates/documented_reference_contexts.json")
CONTEXT_KINDS = {"external", "literal", "document_contract", "historical", "proposal"}
SKILL_LIBRARY_PREFIX = "tools/skill_library/"
DOCS_PREFIX = "docs/"
DOCUMENT_SCOPES = ("core", "docs", "skill_library")
SCOPE_GROUPS: dict[str, tuple[str, ...]] = {
    "core": ("core",),
    "docs": ("docs",),
    "product": ("core", "docs"),
    "skill-library": ("skill_library",),
    "all": DOCUMENT_SCOPES,
}
IDENTIFIER = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]+\b")
INLINE_REFERENCE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]+)`")


@dataclass(frozen=True)
class ReferenceContext:
    kind: str
    reason: str
    evidence: str


def _is_excluded_rel_path(rel_path: PurePosixPath) -> bool:
    if any(part in EXCLUDE_DIRS for part in rel_path.parts):
        return True
    posix = rel_path.as_posix()
    return any(posix == excluded or posix.startswith(excluded + "/") for excluded in EXCLUDE_REL_DIRS)


def _files(root_dir: str | Path, extensions: tuple[str, ...]) -> Iterator[Path]:
    root = Path(root_dir).absolute()
    if (root / ".git").exists():
        listed = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
        for raw_entry in sorted(listed.split(b"\x00")):
            if not raw_entry:
                continue
            rel = PurePosixPath(raw_entry.decode("utf-8"))
            if _is_excluded_rel_path(rel) or not rel.name.endswith(extensions):
                continue
            candidate = root / rel
            if candidate.is_file():
                yield candidate
        return
    for directory, dirs, files in os.walk(root):
        rel_dir = Path(directory).relative_to(root)
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS and (rel_dir / d).as_posix() not in EXCLUDE_REL_DIRS)
        for name in sorted(files):
            if name.endswith(extensions):
                yield Path(directory) / name


def _is_hex_hash(symbol: str) -> bool:
    """Return True for hex digests and commit SHAs, preserving words and error codes."""
    if len(symbol) < 7 or not any(ch.isdigit() for ch in symbol):
        return False
    return all(ch in "0123456789abcdef" for ch in symbol) or all(ch in "0123456789ABCDEF" for ch in symbol)


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


def classify_document_scope(relative_path: str | Path) -> str:
    """Classify a repository-relative Markdown path into core, docs, or skill_library."""
    normalized = Path(relative_path).as_posix().lstrip("./")
    if normalized == "tools/skill_library" or normalized.startswith(SKILL_LIBRARY_PREFIX):
        return "skill_library"
    if normalized == "docs" or normalized.startswith(DOCS_PREFIX):
        return "docs"
    return "core"


def partition_ghost_nodes(
    root_dir: str | Path,
    ghosts: set[tuple[str, str]],
) -> dict[str, set[tuple[str, str]]]:
    """Group unresolved references into core, docs, and skill_library strata."""
    root = Path(root_dir).absolute()
    buckets: dict[str, set[tuple[str, str]]] = {scope: set() for scope in DOCUMENT_SCOPES}
    for path_str, symbol in ghosts:
        relative = Path(path_str).absolute().relative_to(root).as_posix()
        buckets[classify_document_scope(relative)].add((path_str, symbol))
    return buckets


def audit_ghost_nodes(
    root_dir: str | Path,
    symbol_table: set[str],
    *,
    scopes: set[str] | frozenset[str] | tuple[str, ...] | None = None,
) -> set[tuple[str, str]]:
    """Reject missing local identifiers unless their exact document context was reviewed."""
    root = Path(root_dir).absolute()
    contexts = _load_contexts(root)
    allowed_scopes = set(DOCUMENT_SCOPES) if scopes is None else set(scopes)
    unknown_scopes = allowed_scopes - set(DOCUMENT_SCOPES)
    if unknown_scopes:
        raise ValueError(f"Unknown document scope(s): {sorted(unknown_scopes)}")
    ghosts: set[tuple[str, str]] = set()
    for path in _files(root, DOC_EXTS):
        relative = path.relative_to(root).as_posix()
        if classify_document_scope(relative) not in allowed_scopes:
            continue
        content = path.read_text(encoding="utf-8")
        for symbol in INLINE_REFERENCE.findall(content):
            if symbol in symbol_table or len(symbol) <= 4 or _is_hex_hash(symbol):
                continue
            if f"[OBSOLETO: {symbol}]" in content:
                continue
            if (relative, symbol) in contexts:
                continue
            ghosts.add((str(path), symbol))
    return ghosts


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit unresolved documentary code references separated by stratum.")
    parser.add_argument(
        "--scope",
        choices=tuple(SCOPE_GROUPS),
        default="all",
        help="Stratum enforced for exit code while reporting all counts (default: all).",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print scope counts without listing every unresolved reference.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).absolute().parents[2] if root is None else root
    try:
        symbols = build_symbol_table(repo_root)
        all_ghosts = audit_ghost_nodes(repo_root, symbols)
        contexts = _load_contexts(repo_root)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL: reference scan: {error}", file=sys.stderr)
        return 1

    buckets = partition_ghost_nodes(repo_root, all_ghosts)
    enforced_scopes = SCOPE_GROUPS[args.scope]
    selected: set[tuple[str, str]] = set().union(*(buckets[scope] for scope in enforced_scopes))

    print(f"Indexed {len(symbols)} source identifiers; {len(contexts)} reviewed documentary contexts.")
    print(
        "Scope breakdown: "
        f"core={len(buckets['core'])}, "
        f"docs={len(buckets['docs'])}, "
        f"tools/skill_library={len(buckets['skill_library'])}, "
        f"total={len(all_ghosts)}."
    )
    if selected:
        print(f"FAIL ({args.scope}): {len(selected)} unresolved local code references.")
        if not args.summary_only:
            for scope in enforced_scopes:
                if not buckets[scope]:
                    continue
                print(f"[{scope}] ({len(buckets[scope])})")
                for path, symbol in sorted(buckets[scope]):
                    print(f"  {symbol}: {Path(path).relative_to(repo_root)}")
        return 1
    print(f"PASS ({args.scope}): zero unresolved local code references in selected scope.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
