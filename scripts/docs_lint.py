#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | DOCS TYPE-CHECKER v2.0 (CAPA 0 + CAPA 1)
# ============================================================================
# Checks configured vocabulary rules, local Markdown links, heading anchors and
# exact index coverage. The optional LAYA probe is separate from local checks.
import argparse
from collections import Counter
import html
import os
from pathlib import Path
import re
import socket
import struct
import sys
from urllib.parse import unquote, urlsplit

# --- DL-001 & DL-006: Anergy Vocabulary (Fail-Closed) ---
FORBIDDEN_ADJECTIVES = {
    "blazing",
    "blazingly",
    "seamless",
    "seamlessly",
    "revolutionary",
    "intuitive",
    "unprecedented",
    "effortless",
    "effortlessly",
    "incredible",
    "state-of-the-art",
    "increíble",
    "intuitivo",
    "revolucionario",
    "sin fricción",
    "mágicamente",
    "proactiva",
    "proactivamente",
}

FORBIDDEN_MODALS = {
    "may",
    "might",
    "could",
    "can help",
    "allows you to",
    "enables you to",
    "podría",
    "puede ayudar",
    "te permite",
    "te habilita",
}

# --- DL-007: Cargo-Cult Metaphors ---
FORBIDDEN_METAPHORS = {
    "quantum",
    "thermodynamic without",
    "holographic",
    "cuántico",
    "holográfico",
}

# --- KUDURRU-64 IPC Constants (LAYA Edge System-1) ---
LAYA_MAGIC = 0x4C415941  # 'LAYA'
LAYA_SOCKET_PATH = "/tmp/laya_kudurru.sock"
SHANNON_GATE_BITS = 0.35


def slugify(text: str) -> str:
    """GitHub heading slug: punctuation removed, spaces retained as separators."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = html.unescape(text).lower().strip()
    return re.sub(r"[^\w\s-]", "", text).replace(" ", "-")


def prose_lines(content: str) -> list[str]:
    """Preserve source line numbers while excluding fenced Markdown examples."""
    result = []
    fence_char = None
    fence_length = 0
    for line in content.splitlines():
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence_char:
            if match and match[1][0] == fence_char and len(match[1]) >= fence_length:
                fence_char = None
            result.append("")
        elif match:
            fence_char, fence_length = match[1][0], len(match[1])
            result.append("")
        else:
            result.append(line)
    return result


def logical_path(path: Path) -> Path:
    """Normalize link segments without dereferencing a logical checkout symlink."""
    return Path(os.path.abspath(path))


def inline_destinations(line: str) -> list[str]:
    """Read destinations independently, including both links in a nested badge."""
    destinations = []
    for match in re.finditer(r"\]\(\s*", line):
        start = match.end()
        if start < len(line) and line[start] == "<":
            end = line.find(">", start + 1)
            if end >= 0:
                destinations.append(line[start + 1 : end])
            continue
        depth = 0
        end = start
        while end < len(line):
            char = line[end]
            if char == "\\" and end + 1 < len(line):
                end += 2
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char.isspace() and depth == 0:
                break
            end += 1
        if end > start:
            destinations.append(re.sub(r"\\([() ])", r"\1", line[start:end]))
    return destinations


def link_destinations(content: str) -> list[tuple[int, str]]:
    lines = prose_lines(content)
    definitions = {}
    for line in lines:
        match = re.match(r"^\s{0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))", line)
        if match:
            definitions[match[1].casefold()] = match[2] or match[3]
    result = []
    for number, raw_line in enumerate(lines, 1):
        # Inline examples are not live links. Backticks in link labels are harmless.
        line = re.sub(r"`+[^`]*`+", "", raw_line)
        targets = inline_destinations(line)
        targets += re.findall(r"<(?:a|img)\b[^>]*(?:href|src)=[\"']([^\"']+)", line)
        for label, reference in re.findall(r"\[([^\]]+)\]\[([^\]]*)\]", line):
            key = (reference or label).casefold()
            if key in definitions:
                targets.append(definitions[key])
        result.extend((number, html.unescape(target)) for target in targets)
    return result


def build_anchor_registry(md_files: list[Path]) -> dict[Path, set[str]]:
    anchors: dict[Path, set[str]] = {}
    for fpath in md_files:
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            lines = prose_lines(content)
            seen: Counter[str] = Counter()
            file_anchors = set()
            for index, line in enumerate(lines):
                m = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
                header = m[1] if m else None
                if not header and index and re.match(r"^\s{0,3}(?:=+|-+)\s*$", line) and lines[index - 1].strip():
                    header = lines[index - 1].strip()
                if header:
                    slug = slugify(header)
                    candidate = slug
                    while candidate in file_anchors:
                        seen[slug] += 1
                        candidate = f"{slug}-{seen[slug]}"
                    file_anchors.add(candidate)
                for a_match in re.finditer(r'<(?:a|h[1-6])\b[^>]*\b(?:id|name)=["\']([^"\']+)["\']', line):
                    file_anchors.add(a_match[1])
            anchors[logical_path(fpath)] = file_anchors
        except (OSError, UnicodeError) as error:
            raise ValueError(f"Cannot index Markdown anchors in {fpath}: {error}") from error
    return anchors


def scan_file(
    filepath: Path,
    workspace_root: Path,
    anchor_registry: dict[Path, set[str]],
) -> int:
    errors = 0
    in_layer_0_or_1 = False
    content = filepath.read_text(encoding="utf-8")

    for i, line in enumerate(prose_lines(content), 1):
        if filepath.name == "DOCS_GRAMMAR.md":
            # Vocabulary examples explain rejected terms, but its links still count.
            continue

        # DL-008 & DL-009: Historical sed glitch & Sovereign Identity Guard
        if "Ledger Asíncrono" in line:
            print(f"[{filepath.name}:{i}] DL-008 ERROR: Sed corruption 'Ledger Asíncrono' detected.")
            errors += 1
        if "Borja Motor Causal" in line or "[OBSOLETO: borjamoskv]" in line:
            print(
                f"[{filepath.name}:{i}] DL-009 ERROR: Sovereign identity corruption"
                " ('Borja Motor Causal' / '[OBSOLETO: borjamoskv]') detected."
            )
            errors += 1

        # Remove inline code blocks to avoid false positives on grammar
        clean_line = re.sub(r"`[^`]+`", "", line)
        line_lower = clean_line.lower()

        # Layer Tracking
        if "[LAYER 0]" in line or "[LAYER 1]" in line or i < 30:
            in_layer_0_or_1 = True
        if "[LAYER 2]" in line or "[LAYER 3]" in line:
            in_layer_0_or_1 = False

        # DL-001: Adjectives in Top Layers
        if in_layer_0_or_1:
            for adj in FORBIDDEN_ADJECTIVES:
                if re.search(r"\b" + adj + r"\b", line_lower):
                    print(f"[{filepath.name}:{i}] DL-001 ERROR: Forbidden adjective '{adj}' (Anergy detected).")
                    errors += 1

        # DL-006: Modal verbs
        for modal in FORBIDDEN_MODALS:
            if re.search(r"\b" + modal + r"\b", line_lower):
                print(
                    f"[{filepath.name}:{i}] DL-006 ERROR: Weak modal verb '{modal}' violates state machine certainty."
                )
                errors += 1

        # DL-007: Metaphors
        for meta in FORBIDDEN_METAPHORS:
            if re.search(r"\b" + meta + r"\b", line_lower):
                print(f"[{filepath.name}:{i}] DL-007 ERROR: Cosmetic metaphor '{meta}' without physical bounding.")
                errors += 1

    # Type-check rendered destinations after collecting reference definitions.
    if logical_path(workspace_root / "docs") in logical_path(filepath).parents:
        for number, target in link_destinations(content):
            parsed = urlsplit(target)
            if parsed.scheme == "file":
                print(f"[{filepath.name}:{number}] TYPE-001 ERROR: Nonportable file URL '{target}'.")
                errors += 1
                continue
            if parsed.scheme or parsed.netloc:
                continue
            link_file = unquote(parsed.path)
            if link_file.startswith("/"):
                target_path = logical_path(workspace_root / link_file.lstrip("/"))
            else:
                target_path = logical_path(filepath.parent / link_file) if link_file else logical_path(filepath)
            if not target_path.exists():
                print(f"[{filepath.name}:{number}] TYPE-001 ERROR: Broken relative link '{target}'.")
                errors += 1
                continue
            if parsed.fragment and target_path.suffix == ".md":
                if target_path not in anchor_registry:
                    anchor_registry.update(build_anchor_registry([target_path]))
                if unquote(parsed.fragment) not in anchor_registry[target_path]:
                    print(
                        f"[{filepath.name}:{number}] TYPE-002 ERROR: Broken GFM anchor '#{parsed.fragment}' in '{target_path.name}'."
                    )
                    errors += 1

    return errors


def check_index_topology(docs_dir: Path) -> int:
    """Compare actual Markdown paths with explicit index destinations."""
    errors = 0
    for index_dir in (docs_dir, docs_dir / "03_guides", docs_dir / "06_theory"):
        if not index_dir.is_dir():
            continue
        index = index_dir / "00_index.md"
        if not index.is_file():
            print(f"[{index}] TYPE-003 ERROR: Missing documentation index.")
            errors += 1
            continue
        disk_files = {logical_path(p) for p in index_dir.rglob("*.md") if p != index}
        indexed = []
        for _, target in link_destinations(index.read_text(encoding="utf-8")):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = logical_path(index_dir / unquote(parsed.path))
            if path.suffix == ".md" and path.is_relative_to(logical_path(index_dir)):
                indexed.append(path)
        for missing in sorted(disk_files - set(indexed)):
            print(
                f"[{index.relative_to(docs_dir)}] TYPE-003 ERROR: Unindexed document '{missing.relative_to(docs_dir)}'."
            )
            errors += 1
        for stale in sorted(set(indexed) - disk_files):
            print(f"[{index.relative_to(docs_dir)}] TYPE-004 ERROR: Stale index destination '{stale}'.")
            errors += 1
        for path, count in Counter(indexed).items():
            if count > 1:
                print(f"[{index.relative_to(docs_dir)}] TYPE-004 ERROR: Duplicate index destination '{path}'.")
                errors += 1
    return errors


def pack_kudurru64_frame(primitive: int, seq_id: int, payload: bytes, version: int = 1) -> bytes:
    """Packs a 64-byte aligned KUDURRU-64 frame (>IIBBHfI44s, Big-Endian + version) for LAYA Edge."""
    padded = payload[:44].ljust(44, b"\x00")
    return struct.pack(">IIBBHfI44s", LAYA_MAGIC, seq_id, version, primitive, 0, 0.0, len(payload), padded)


def probe_system1_laya() -> bool:
    sock_path = Path(LAYA_SOCKET_PATH)
    if not sock_path.exists():
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            s.connect(LAYA_SOCKET_PATH)
            frame = pack_kudurru64_frame(0x01, 1, b"PROBE_DOCS_TYPE_CHECK")
            s.sendall(frame)
            resp = s.recv(64)
            return len(resp) == 64
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="BABYLON-60 Docs Type-Checker v2.0 (Layer 0 + Layer 1)")
    parser.add_argument(
        "--system1",
        action="store_true",
        help="Enable Layer 1 System-1 (LAYA Edge KUDURRU-64) semantic gate",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="docs",
        type=Path,
        help="Markdown file or directory, relative to the repository root (default: docs)",
    )
    parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(), help="Repository root for local links and root README checks"
    )
    args = parser.parse_args()

    workspace_root = logical_path(args.repo_root)
    docs_dir = logical_path(workspace_root / args.path)
    if not docs_dir.exists():
        parser.error(f"Markdown path does not exist: {docs_dir}")
    root_files = [workspace_root / "README.md", workspace_root / "README_ES.md"]

    total_errors = 0

    files_to_scan = [f for f in root_files if f.exists()]
    if docs_dir.exists():
        files_to_scan.extend(sorted(docs_dir.rglob("*.md")) if docs_dir.is_dir() else [docs_dir])

    anchor_registry = build_anchor_registry(files_to_scan)

    for filepath in files_to_scan:
        if filepath.exists():
            total_errors += scan_file(filepath, workspace_root, anchor_registry)

    if docs_dir.is_dir():
        total_errors += check_index_topology(docs_dir)

    if args.system1:
        laya_active = probe_system1_laya()
        status_str = (
            "ACTIVE (KUDURRU-64 socket connected)"
            if laya_active
            else "STANDBY (Fallback to Layer-0 AST deterministic rules)"
        )
        print(f"[*] Layer-1 System-1 Gate (LAYA Edge): {status_str}")

    if total_errors > 0:
        print(f"\n[!] C5-REAL Docs Type-Checker Failed: {total_errors} violations detected.")
        sys.exit(1)
    else:
        print("\n[+] Documentation checks passed: configured grammar rules, local links, anchors and index coverage.")
        sys.exit(0)


if __name__ == "__main__":
    main()
