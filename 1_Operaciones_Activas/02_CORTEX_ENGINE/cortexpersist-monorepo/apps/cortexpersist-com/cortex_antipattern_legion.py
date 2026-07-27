#!/usr/bin/env python3
import os
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    ".astro",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "build",
    "out",
    ".vercel",
}

# Anti-pattern regular expressions
PATTERNS = {
    "BARE_EXCEPT": (
        re.compile(r"except\s*:"),
        "Bare except clause (swallows all exceptions, including KeyboardInterrupt)",
    ),
    "EXCEPT_PASS": (
        re.compile(r"except\s+Exception\s*(?:as\s+\w+)?\s*:\s*(?:pass|continue)"),
        "Except Exception block with pass or continue (silently swallowing errors)",
    ),
    "UNPROTECTED_OPEN": (
        re.compile(r"\b\w+\s*=\s*open\("),
        "Resource leakage risk: File open without with context manager",
    ),
    "SHELL_TRUE": (
        re.compile(r"shell\s*=\s*True"),
        "Security vulnerability: shell=True in subprocess call (shell injection risk)",
    ),
    "EVAL_EXEC": (
        re.compile(r"\b(eval|exec)\s*\("),
        "Security vulnerability: Use of eval() or exec() (arbitrary code execution)",
    ),
    "HARDCODED_SECRET": (
        re.compile(
            r'(?:key|secret|token|password|passwd|api_key)\s*=\s*["\'][a-zA-Z0-9_\-]{8,}["\']',
            re.IGNORECASE,
        ),
        "Security risk: Possible hardcoded secret/credentials",
    ),
    "MUTABLE_DEFAULT": (
        re.compile(r"def\s+\w+\s*\(.*=\s*(\[\]|\{\})\s*.*\)"),
        "Python anti-pattern: Mutable default argument in function definition",
    ),
    "ASSERT_STATEMENT": (
        re.compile(r"\bassert\b\s+[^,\n]+"),
        "Assertion in production logic (optimized away under python -O)",
    ),
}


def scan_file(file_path, workspace_root):
    findings = []
    ext = os.path.splitext(file_path)[1]
    is_python = ext == ".py"
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                # Skip comments and blank lines to avoid false positives
                stripped = line.strip()
                if (
                    not stripped
                    or stripped.startswith("#")
                    or stripped.startswith("//")
                    or stripped.startswith("<!--")
                    or "# nosec" in line
                ):
                    continue

                for key, (pattern, desc) in PATTERNS.items():
                    # Limit Python-specific patterns to Python files
                    if (
                        key
                        in {
                            "BARE_EXCEPT",
                            "EXCEPT_PASS",
                            "UNPROTECTED_OPEN",
                            "MUTABLE_DEFAULT",
                            "ASSERT_STATEMENT",
                        }
                        and not is_python
                    ):
                        continue

                    # Limit EVAL_EXEC containing .exec( in non-python files
                    if key == "EVAL_EXEC" and not is_python and ".exec(" in stripped:
                        continue

                    if pattern.search(stripped):
                        findings.append(
                            {
                                "file": os.path.relpath(file_path, workspace_root),
                                "line": line_num,
                                "type": key,
                                "description": desc,
                                "snippet": stripped[:100],
                            }
                        )
    except Exception:
        # Silently fail for unreadable/binary files
        pass
    return findings


def main():
    start_time = time.time()
    workspace_root = os.path.abspath(".")
    files_to_scan = []

    # Gather files
    for root, dirs, files in os.walk(workspace_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for file in files:
            if file == "cortex_antipattern_legion.py":
                continue
            ext = os.path.splitext(file)[1]
            if ext in {".py", ".ts", ".tsx", ".html", ".js", ".mjs", ".astro"}:
                files_to_scan.append(os.path.join(root, file))

    all_findings = []
    total_files = len(files_to_scan)

    print(f"[C5-REAL] Spawning 1000 agents in parallel to scan {total_files} files...")

    # Spawn 1000 workers in the thread pool
    with ThreadPoolExecutor(max_workers=1000) as executor:
        futures = {
            executor.submit(scan_file, f, workspace_root): f for f in files_to_scan
        }
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_findings.extend(res)

    duration = time.time() - start_time

    # Save findings to JSON ledger
    output_path = os.path.join(workspace_root, "cortex_antipatterns.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_files_scanned": total_files,
                "total_findings": len(all_findings),
                "scan_duration_seconds": duration,
                "findings": all_findings,
            },
            f,
            indent=2,
        )

    print(
        f"[C5-REAL] Scan complete. Found {len(all_findings)} anti-patterns across {total_files} files in {duration:.4f} seconds."
    )
    print(f"Results serialized to {output_path}")

    # Output a high-density summary
    summary_by_type = {}
    for f in all_findings:
        summary_by_type[f["type"]] = summary_by_type.get(f["type"], 0) + 1

    print("\nSummary of Anti-patterns Found:")
    print("-" * 60)
    for k, v in summary_by_type.items():
        print(f" - {k:<25}: {v} occurrences")
    print("-" * 60)


if __name__ == "__main__":
    main()
