#!/usr/bin/env python3
"""Conservative workspace artifact cleanup; SQLite and global sessions are preserved."""

import argparse
import fnmatch
import importlib.util
import os
import stat
import sys
from pathlib import Path
from typing import Any

CANONICAL_PRESERVED_FILES = {
    "wild_mitxu_b2b_siglo.mp4", "mitxudiario-11-ceuton-4min.mp4",
    "mitxudiario-11-ceuton-cinematica-4min.mp4", "mitxu_wild_swarm_1080p.mp4",
    "mitx_wild_medina_special_1080p.mp4", "mitxudiario_10_master.mp4",
    "mitxuwild_rap_intro_15s_master.mp4", "itera_100", "diction_verification",
    "voice_tests", "sintonia", "qc_audio_report.json", "qc_report.json",
    "prosody_analysis_report.json", "alain_whatsapp_corpus_analysis.json",
    "mitxu_whatsapp_corpus_analysis.json",
}
CANONICAL_PROTECTED_DIRS = [
    "babylon-web", "apps/web", "apps/babylon60-ide", "remotion",
    "ley_menores_remotion", "sota_documentary_remotion", "strike-rs/.venv",
    ".uv_python", "youtube-research-remotion", "cortex-persist",
    "02_CORTEX_ENGINE/cortex", "data/cortex_memory.db", "artifact_bundle_v3",
]
SQLITE_HEADERS = (
    b"SQLite format 3\0", b"\x37\x7f\x06\x82", b"\x37\x7f\x06\x83",
    b"\xd9\xd5\x05\xf9\x20\xa1\x63\xd7",
)


def format_bytes(bytes_count: int) -> str:
    if bytes_count < 1024:
        return f"{bytes_count} B"
    if bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    if bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


def _protected(parts: tuple[str, ...]) -> bool:
    if any(part in {".git", ".venv", "node_modules"} | CANONICAL_PRESERVED_FILES for part in parts):
        return True
    if any(part.endswith(("_master.mp4", "_siglo.mp4")) for part in parts):
        return True
    for entry in CANONICAL_PROTECTED_DIRS:
        pattern = Path(entry).parts
        if any(parts[i:i + len(pattern)] == pattern for i in range(len(parts))):
            return True
    return False


def _sqlite_name(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith((".db", ".sqlite", ".sqlite3", "-wal", "-shm", "-journal")) or "-mj" in lowered


def _category(parts: tuple[str, ...]) -> tuple[str, str] | None:
    name = parts[-1]
    if _sqlite_name(name) or _protected(parts):
        return None
    if name.endswith(".pyc"):
        return "pyc_files", "pycache_bytes"
    if parts[0].startswith("scratch_") or (len(parts) == 1 and fnmatch.fnmatch(name, "public_studio_*_thumb.*")):
        return "scratch_files", "scratch_bytes"
    if parts[0] == "out" and len(parts) > 1:
        return "out_ephemeral_files", "out_ephemeral_bytes"
    if name == ".DS_Store" or name.endswith((".tmp", ".bak", "~")):
        return "os_meta_files", "os_meta_bytes"
    if len(parts) == 1 and fnmatch.fnmatch(name, "*_binaural_*.wav"):
        return "root_test_wavs", "root_test_wavs_bytes"
    return None


def purge_anergy(workspace_path: Path, dry_run: bool = False) -> dict[str, Any]:
    """Delete eligible regular files individually, anchored to an opened workspace.

    Directories are retained. SQLite names/headers and uninspectable objects are
    preserved. Descriptor-relative O_NOFOLLOW prevents following links; identity
    is rechecked before unlink. This is not an OS sandbox or an atomic type-check
    plus unlink against a hostile concurrent rename.
    """
    if type(dry_run) is not bool:
        raise ValueError("dry_run must be bool")
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "fwalk"):
        raise RuntimeError("Cleanup requires descriptor-relative O_NOFOLLOW support")
    stats: dict[str, Any] = {
        "scratch_files": 0, "scratch_bytes": 0, "out_ephemeral_files": 0,
        "out_ephemeral_bytes": 0, "pycache_dirs": 0, "pyc_files": 0,
        "pycache_bytes": 0, "os_meta_files": 0, "os_meta_bytes": 0,
        "root_test_wavs": 0, "root_test_wavs_bytes": 0, "wal_orphans": 0,
        "wal_bytes": 0, "ghost_listeners_reset": 0, "total_bytes_recovered": 0,
        "planned_files": 0, "planned_bytes": 0, "skipped_candidates": 0,
        "errors": 0, "dry_run": dry_run, "wal_policy": "PRESERVED",
        "global_sessions": "NOT_CHECKED",
    }
    workspace = Path(workspace_path).absolute()
    root_fd = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    def walk_error(error: OSError) -> None:
        stats["errors"] += 1

    try:
        for relative, directories, files, directory_fd in os.fwalk(
            ".", topdown=True, follow_symlinks=False, dir_fd=root_fd, onerror=walk_error
        ):
            prefix = Path(relative).parts
            directories[:] = [name for name in directories if not _protected(prefix + (name,))]
            for name in files:
                category = _category(prefix + (name,))
                if category is None:
                    continue
                count_key, byte_key = category
                fd = None
                try:
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
                    info = os.fstat(fd)
                    if not stat.S_ISREG(info.st_mode):
                        stats["skipped_candidates"] += 1
                        continue
                    header = os.read(fd, 16)
                    if header.startswith(SQLITE_HEADERS):
                        stats["skipped_candidates"] += 1
                        continue
                    if name.endswith(".pyc") and not header.startswith(importlib.util.MAGIC_NUMBER):
                        stats["skipped_candidates"] += 1
                        continue
                    current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    if (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino):
                        stats["skipped_candidates"] += 1
                        continue
                    stats["planned_files"] += 1
                    stats["planned_bytes"] += info.st_size
                    if not dry_run:
                        os.unlink(name, dir_fd=directory_fd)
                        stats[count_key] += 1
                        stats[byte_key] += info.st_size
                except OSError:
                    stats["errors"] += 1
                finally:
                    if fd is not None:
                        os.close(fd)
    finally:
        os.close(root_fd)
    # Legacy key: logical sizes of unlinked files, not measured disk space freed.
    stats["total_bytes_recovered"] = sum(stats[key] for key in (
        "scratch_bytes", "out_ephemeral_bytes", "pycache_bytes", "os_meta_bytes", "root_test_wavs_bytes",
    ))
    return stats


def print_brutalist_table(stats: dict, workspace_path: Path) -> None:
    mode = "DRY-RUN (no files removed)" if stats["dry_run"] else "WORKSPACE FILE CLEANUP"
    print(f"\n{mode}: {workspace_path}")
    print(f"Candidates: {stats['planned_files']}; candidate bytes: {format_bytes(stats['planned_bytes'])}")
    print(f"Logical file bytes removed: {format_bytes(stats['total_bytes_recovered'])}")
    print("SQLite WAL/SHM/journals: PRESERVED")
    print("Global sessions: NOT_CHECKED (outside workspace maintenance)")
    print(f"Inspection/operation errors: {stats['errors']}; skipped objects: {stats['skipped_candidates']}")
    print("Directories and protected artifacts remain in place.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Conservative workspace artifact cleanup.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true", help="Inspect candidates without deleting files")
    args = parser.parse_args()
    try:
        stats = purge_anergy(args.workspace.absolute(), dry_run=args.dry_run)
    except (OSError, ValueError, RuntimeError, NotImplementedError) as error:
        print(f"Cleanup refused: {error}", file=sys.stderr)
        return 1
    print_brutalist_table(stats, args.workspace)
    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
