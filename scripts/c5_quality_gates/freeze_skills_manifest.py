#!/usr/bin/env python3
"""Create or verify a SHA-256 inventory of active skills, including linked resources.

Records identity, not semantic safety. Archives and generated caches are explicitly
excluded. Relative paths allow verification against a different destination root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import TypedDict

EXCLUDED = frozenset({"_archive", "archive", ".git", "node_modules", "__pycache__"})


class InventoryEntry(TypedDict, total=False):
    mode: int
    kind: str
    target: str
    cycle: bool
    bytes: int
    sha256: str


class Manifest(TypedDict):
    version: int
    algorithm: str
    excluded_names: list[str]
    entries: dict[str, InventoryEntry]


def inventory(root: Path, top_levels: set[str] | None = None) -> Manifest:
    entries: dict[str, InventoryEntry] = {}

    def visit(path: Path, ancestors: frozenset[tuple[int, int]]) -> None:
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        entry: InventoryEntry = {"mode": stat.S_IMODE(info.st_mode)}
        if path.is_symlink():
            entry.update({"kind": "symlink", "target": str(path.readlink())})
            if not path.exists():
                raise OSError(f"Broken reference: {path}")
            info = path.stat()
        elif path.is_dir():
            entry["kind"] = "directory"
        else:
            entry["kind"] = "file"
        entries[relative] = entry
        if stat.S_ISDIR(info.st_mode):
            identity = (info.st_dev, info.st_ino)
            if identity in ancestors:
                entry["cycle"] = True
                return
            for child in sorted(path.iterdir()):
                if child.name not in EXCLUDED and (path != root or top_levels is None or child.name in top_levels):
                    visit(child, ancestors | {identity})
        elif stat.S_ISREG(info.st_mode):
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            entry.update({"bytes": info.st_size, "sha256": digest.hexdigest()})
        else:
            raise OSError(f"Unsupported resource type: {path}")

    if not root.is_dir():
        raise OSError(f"Missing skills root: {root}")
    visit(root, frozenset())
    if len(entries) <= 1:
        raise OSError(f"Empty active skills tree: {root}")
    return {"version": 1, "algorithm": "sha256", "excluded_names": sorted(EXCLUDED), "entries": entries}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--output", type=Path)
    action.add_argument("--verify", type=Path)
    parser.add_argument(
        "--subset",
        action="store_true",
        help="Verify exact imported top-level entries while allowing pre-existing siblings",
    )
    args = parser.parse_args()
    if args.subset and not args.verify:
        parser.error("--subset requires --verify")
    try:
        if args.verify:
            expected = json.loads(args.verify.read_text(encoding="utf-8"))
            if args.subset:
                if not isinstance(expected, dict) or not isinstance(expected.get("entries"), dict):
                    raise ValueError("Invalid manifest entries")
                entries = expected["entries"]
                if "." not in entries or len(entries) <= 1:
                    raise ValueError("Empty manifest scope")
                top_levels = {name.split("/")[0] for name in entries if name != "."}
                current = inventory(args.root.absolute(), top_levels=top_levels)
                # The destination container is pre-existing and is not part of the port.
                current["entries"]["."] = entries["."]
            else:
                current = inventory(args.root.absolute())
            if expected != current:
                print("FAIL: skills tree differs from manifest", file=sys.stderr)
                return 1
            print("PASS: active tree content, modes and symbolic references match manifest")
        else:
            current = inventory(args.root.absolute())
            output = args.output.absolute()
            # Refuse any output beneath the logical or physical loading tree.
            if output.is_relative_to(args.root.absolute()) or Path(os.path.realpath(output)).is_relative_to(
                Path(os.path.realpath(args.root))
            ):
                raise OSError("Manifest must live outside the active skills tree")
            with output.open("x", encoding="utf-8") as stream:
                json.dump(current, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
            print(f"Manifest: {output}")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"NO_VERIFICADO: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
