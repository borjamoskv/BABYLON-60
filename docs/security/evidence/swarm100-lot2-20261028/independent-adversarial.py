"""Independent Lot2 fixtures. All helper execution is confined to TemporaryDirectory."""
import asyncio
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
SOURCES = [
    "tools/skill_library/global/anergy-purge-protocol/scripts/anergy_purge.py",
    "tools/skill_library/global/c5-cortex-swarm-orchestrator/references/modules/anergy-purge-protocol/scripts/anergy_purge.py",
]


def load_source(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    results = []
    old_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="lot2-independent-") as temporary:
        base = Path(temporary)
        home = base / "home"
        home.mkdir()
        os.chdir(base)
        try:
            with patch.dict(os.environ, {"HOME": str(home), "BABYLON_HOME": str(home / "babylon")}), patch.object(Path, "home", return_value=home):
                for index, source in enumerate(SOURCES):
                    module = load_source(source, f"independent_anergy_{index}")
                    workspace = base / f"workspace-{index}"
                    workspace.mkdir()
                    candidate = workspace / "blocked.tmp"
                    candidate.write_bytes(b"temporary unlink failure fixture")
                    with patch.object(module.os, "unlink", side_effect=PermissionError("fixture")):
                        stats = module.purge_anergy(workspace)
                    assert candidate.exists() and stats["errors"] == 1
                    assert stats["total_bytes_recovered"] == 0
                    candidate.unlink()
                    results.append({"source": source, "case": "unlink_failure_preserves_and_counts_zero", "passed": True})

                    fifo = workspace / "pipe.tmp"
                    os.mkfifo(fifo)
                    outside = base / f"outside-{index}"
                    outside.write_bytes(b"external fixture sentinel")
                    link = workspace / "link.tmp"
                    link.symlink_to(outside)
                    unrecognized = workspace / "invalid.pyc"
                    unrecognized.write_bytes(b"not recognized bytecode")
                    with patch.object(Path, "home", side_effect=AssertionError("HOME must not be resolved")):
                        stats = module.purge_anergy(workspace)
                    assert fifo.exists() and link.is_symlink() and unrecognized.exists()
                    assert outside.read_bytes() == b"external fixture sentinel"
                    assert stats["total_bytes_recovered"] == 0
                    results.append({"source": source, "case": "fifo_symlink_unknown_bytecode_and_home_guard", "passed": True})

                    victim = workspace / "victim.tmp"
                    victim.write_bytes(b"eligible temporary fixture")
                    replacement = workspace / "replacement.db"
                    replacement.write_bytes(b"SQLite format 3\0preserved replacement fixture")
                    old_stat = os.stat
                    swapped = []

                    def replace_before_recheck(path, *args, **kwargs):
                        if path == "victim.tmp" and kwargs.get("dir_fd") is not None and not swapped:
                            fd = kwargs["dir_fd"]
                            os.replace("replacement.db", "victim.tmp", src_dir_fd=fd, dst_dir_fd=fd)
                            swapped.append(True)
                        return old_stat(path, *args, **kwargs)

                    with patch.object(module.os, "stat", side_effect=replace_before_recheck):
                        stats = module.purge_anergy(workspace)
                    assert swapped and victim.read_bytes().startswith(b"SQLite format 3\0")
                    assert stats["total_bytes_recovered"] == 0
                    results.append({"source": source, "case": "replacement_before_inode_recheck_preserved", "passed": True})

                consolidation = load_source("scripts/c5_cortex/autoconsolidate.py", "independent_consolidation")

                class ForbiddenPath:
                    def __fspath__(self):
                        raise AssertionError("unsupported operation must not resolve a database path")

                try:
                    asyncio.run(consolidation.autoconsolidate(db_path=ForbiddenPath()))
                except consolidation.ConsolidationUnsupportedError:
                    pass
                else:
                    raise AssertionError("consolidation unexpectedly succeeded")
                results.append({"source": "scripts/c5_cortex/autoconsolidate.py", "case": "rejects_before_path_resolution", "passed": True})
        finally:
            os.chdir(old_cwd)
    print(json.dumps({"checks": results, "passed": len(results), "scope": "temporary files only; no main/cohorts/global stores/network"}, indent=2))


if __name__ == "__main__":
    main()
