#!/usr/bin/env python3
"""Portable zero-config launcher for the BABYLON-60 Kernel MCP server.

Preserves logical symlink paths (INV_C5_PATH_SYMLINK_CONFINEMENT) and avoids
hardcoding host-specific absolute paths in versioned MCP manifests (.mcp.json).
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


def main() -> int:
    repo_root = Path(__file__).absolute().parents[2]
    mcp_script = repo_root / "tools" / "babylon60_mcp.py"
    venv_python = repo_root / "target" / "kernel-mcp-venv" / "bin" / "python"
    # The checkout's shared presentation package must also be available when
    # the server runs in its dedicated MCP environment, from any working folder.
    source_root = str(repo_root / "01_KISH_ENGINE")
    python_paths = os.environ.get("PYTHONPATH", "").split(os.pathsep)
    os.environ["PYTHONPATH"] = os.pathsep.join(
        [source_root, *(path for path in python_paths if path and path != source_root)]
    )

    extra_args = sys.argv[1:]
    if "--root" not in extra_args:
        extra_args = ["--root", str(repo_root), *extra_args]

    if venv_python.is_file() and os.access(venv_python, os.X_OK):
        argv = [str(venv_python), str(mcp_script), *extra_args]
        os.execv(str(venv_python), argv)

    uv_bin = shutil.which("uv")
    if uv_bin is not None:
        argv = [
            uv_bin,
            "run",
            "--no-project",
            "--with",
            "fastmcp==4.1.0",
            "--with",
            "blake3==1.0.11",
            "--with",
            "pyjwt>=2.15.1",
            "python3",
            str(mcp_script),
            *extra_args,
        ]
        os.execv(uv_bin, argv)

    argv = [sys.executable, str(mcp_script), *extra_args]
    os.execv(sys.executable, argv)


if __name__ == "__main__":
    raise SystemExit(main())
