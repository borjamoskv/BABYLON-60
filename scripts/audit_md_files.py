#!/usr/bin/env python3
import re
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path("/Users/borjafernandezangulo/30_BABYLON-60").resolve()

EXCLUDE_DIRS = {
    "node_modules",
    ".venv",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "forge-std",
    "fable-library-js.5.8.0",
    "fable-compiler",
}


def find_md_files(root: Path) -> List[Path]:
    md_files = []
    for path in root.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        md_files.append(path)
    return sorted(md_files)


def audit_file(file_path: Path) -> Dict[str, Any]:
    rel_path = file_path.relative_to(REPO_ROOT)
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    size_bytes = file_path.stat().st_size

    h1_count = len([line for line in lines if line.startswith("# ")])

    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    broken_links = []
    links_found = 0
    for match in link_pattern.finditer(content):
        links_found += 1
        link_target = match.group(2).strip()
        if (
            link_target.startswith("http://")
            or link_target.startswith("https://")
            or link_target.startswith("mailto:")
            or link_target.startswith("#")
        ):
            continue
        clean_target = link_target.split("#")[0]
        if not clean_target:
            continue
        if clean_target.startswith("file://"):
            target_path = Path(clean_target[7:]).resolve()
        else:
            target_path = (file_path.parent / clean_target).resolve()

        if not target_path.exists():
            broken_links.append((link_target, clean_target))

    has_c5 = "C5-REAL" in content or "C5" in content
    has_cortex_taint = "CORTEX-TAINT" in content
    has_inv = "INV_" in content or "Ω" in content

    word_count = len(re.findall(r"\w+", content))
    code_block_count = len(re.findall(r"```", content)) // 2

    status = "OK"
    issues = []
    if size_bytes == 0:
        status = "EMPTY"
        issues.append("File is empty (0 bytes).")
    if h1_count == 0:
        issues.append("Missing top-level H1 header.")
    if broken_links:
        status = "WARN" if status == "OK" else status
        issues.append(f"Contains {len(broken_links)} broken link(s): {[b[0] for b in broken_links[:3]]}")

    return {
        "path": str(rel_path),
        "size_bytes": size_bytes,
        "lines": len(lines),
        "words": word_count,
        "h1_count": h1_count,
        "links_count": links_found,
        "broken_links": broken_links,
        "code_blocks": code_block_count,
        "has_c5": has_c5,
        "has_cortex_taint": has_cortex_taint,
        "has_invariants": has_inv,
        "status": status,
        "issues": issues,
    }


def main() -> None:
    md_files = find_md_files(REPO_ROOT)
    results = [audit_file(f) for f in md_files]

    total_files = len(results)
    total_bytes = sum(r["size_bytes"] for r in results)
    total_lines = sum(r["lines"] for r in results)
    total_words = sum(r["words"] for r in results)
    empty_files = [r for r in results if r["status"] == "EMPTY"]
    warn_files = [r for r in results if len(r["issues"]) > 0]

    print("=== MOSKV-1 APEX MD AUDIT SUMMARY ===")
    print(f"Total Markdown Files: {total_files}")
    print(f"Total Disk Volume: {total_bytes / 1024:.2f} KB ({total_lines} lines, {total_words} words)")
    print(f"Files with Issues/Warnings: {len(warn_files)}")
    print(f"Empty Files: {len(empty_files)}")
    print("-" * 50)

    for r in results:
        flag = "🔴" if r["status"] == "EMPTY" else ("🟡" if r["issues"] else "🟢")
        print(f"{flag} {r['path']} ({r['lines']} lines, {r['words']} words, {r['size_bytes']} bytes)")
        for issue in r["issues"]:
            print(f"   └── {issue}")


if __name__ == "__main__":
    main()
